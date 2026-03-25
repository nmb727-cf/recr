import uuid
import random
import pyotp
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.accounts.models import CustomUser, EmailOTP
from apps.tenants.models import Client, Domain
from apps.organisations.models import Organisation
from apps.accounts.serializers import (
    RegisterCompanySerializer, RegisterAgencySerializer, RegisterCandidateSerializer,
    LoginSerializer, UserSerializer, UpdateProfileSerializer,
    ChangePasswordSerializer, MFAVerifySerializer, LogoutSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, RefreshTokenSerializer,
    SendOTPSerializer, VerifyOTPSerializer, OnboardingSerializer,
)
from apps.core.responses import success_response, error_response
from apps.core import events


import logging

logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['email'] = user.email
    refresh['role'] = user.role
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
    }


def create_tenant(name, tenant_type, country_code='IN'):
    """Create a new tenant with unique schema_name and slug."""
    base_slug = slugify(name)[:50]
    if not base_slug:
        base_slug = f"tenant-{uuid.uuid4().hex[:8]}"

    slug = base_slug
    counter = 1
    while Client.objects.filter(slug=slug).exists() or \
          Client.objects.filter(schema_name=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    tenant = Client(
        schema_name=slug,
        name=name,
        slug=slug,
        tenant_type=tenant_type,
        country_code=country_code,
        status='active',
    )
    tenant.save()

    domain = Domain(
        domain=f"{slug}.localhost",
        tenant=tenant,
        is_primary=True,
    )
    domain.save()

    return tenant


def _generate_otp():
    return str(random.randint(100000, 999999))


def _send_otp_email(email, otp_code):
    from apps.communications.services import EmailRoutingService
    
    # In development mode, we don't send real emails by default if specified,
    # but the requirement says "Show OTP directly in UI (or logs)"
    # So we always log it in dev mode.
    if settings.ENVIRONMENT == 'development':
        print(f"DEBUG: OTP for {email} is {otp_code}")
    
    # Only send real email in production mode
    if settings.ENVIRONMENT == 'production':
        EmailRoutingService.send_email(
            subject='Your TalentOS verification code',
            body_text=(
                f'Your TalentOS verification code is: {otp_code}\n\n'
                f'This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n\n'
                f'If you did not create an account, please ignore this email.'
            ),
            body_html=None,
            recipient_list=[email],
            email_type='system'
        )


def _issue_otp(email):
    """Invalidate existing OTPs for this email and issue a fresh one."""
    # Check for resend cooldown
    last_otp = EmailOTP.objects.filter(email=email).order_by('-created_at').first()
    if last_otp:
        cooldown_seconds = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 30)
        time_since_last = (timezone.now() - last_otp.created_at).total_seconds()
        if time_since_last < cooldown_seconds:
            # We don't raise error here, we'll handle it in the view if needed.
            # But for internal calls, we might just return the existing one or skip.
            return last_otp.code

    EmailOTP.objects.filter(email=email, is_used=False).update(is_used=True)
    code = _generate_otp()
    expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
    EmailOTP.objects.create(
        email=email,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
    )
    _send_otp_email(email, code)
    return code


def _auto_configure(user, prefs):
    """Create default automation rules based on onboarding preferences."""
    from apps.automation.models import AutomationRule

    tenant_id = user.tenant_id
    automation_pref = prefs['automation_preference']
    hiring_style = prefs['hiring_style']

    # Persist preferences to org metadata
    try:
        org = Organisation.objects.get(tenant_id=tenant_id)
        org.metadata['onboarding'] = {
            'user_type': prefs['user_type'],
            'hiring_style': hiring_style,
            'team_size': prefs['team_size'],
            'automation_preference': automation_pref,
        }
        org.metadata['onboarding_completed'] = True
        org.save(update_fields=['metadata'])
    except Organisation.DoesNotExist:
        pass

    if automation_pref == 'manual':
        return

    # Base rules for smart + fully_automated
    default_rules = [
        {
            'name': 'Auto-acknowledge application',
            'description': 'Send acknowledgement when an application is received',
            'trigger_event': 'application.submitted',
            'conditions': {},
            'actions': [{'type': 'send_email', 'template': 'application_received'}],
        },
    ]

    if automation_pref == 'fully_automated':
        default_rules += [
            {
                'name': 'Auto-shortlist high-match candidates',
                'description': 'Shortlist candidates with match score ≥ 80',
                'trigger_event': 'application.submitted',
                'conditions': {'match_score__gte': 80},
                'actions': [{'type': 'move_stage', 'stage': 'shortlisted'}],
            },
            {
                'name': 'Schedule interview on shortlist',
                'description': 'Automatically schedule an interview when shortlisted',
                'trigger_event': 'application.shortlisted',
                'conditions': {},
                'actions': [{'type': 'schedule_interview'}],
            },
        ]

    if hiring_style in ('agency', 'mixed'):
        default_rules.append({
            'name': 'Notify team on agency submission',
            'description': 'Notify hiring team when an agency submits a candidate',
            'trigger_event': 'agency.submitted',
            'conditions': {},
            'actions': [{'type': 'notify_team'}],
        })

    for rule_data in default_rules:
        AutomationRule.objects.create(
            tenant_id=tenant_id,
            created_by=user.id,
            is_system=True,
            **rule_data,
        )


# ─── Registration ──────────────────────────────────────────────────────────────

class RegisterCompanyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterCompanySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        data = serializer.validated_data

        tenant = create_tenant(
            name=data['name'],
            tenant_type='company',
            country_code=data.get('country_code', 'IN')
        )

        user = CustomUser.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='tenant_admin',
            tenant_id=tenant.id,
            timezone=data.get('timezone', 'UTC'),
        )

        Organisation.objects.create(
            tenant_id=tenant.id,
            name=data['name'],
            org_type='company',
            created_by=user.id
        )

        events.company.created.send(
            sender=self.__class__,
            tenant=tenant,
            user=user,
            request=request
        )

        # Send email verification OTP
        otp_code = _issue_otp(user.email)

        tokens = get_tokens_for_user(user)
        response_data = {
            'user': UserSerializer(user).data,
            **tokens,
        }
        
        if settings.ENVIRONMENT == 'development':
            response_data['otp_code'] = otp_code
            response_data['is_development_mode'] = True

        return success_response(
            data=response_data,
            message="Account created. Check your email for a verification code.",
            status_code=status.HTTP_201_CREATED,
        )


class RegisterAgencyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterAgencySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        data = serializer.validated_data

        tenant = create_tenant(
            name=data['name'],
            tenant_type='agency',
            country_code=data.get('country_code', 'IN')
        )

        user = CustomUser.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='agency_owner',
            tenant_id=tenant.id,
            timezone=data.get('timezone', 'UTC'),
        )

        Organisation.objects.create(
            tenant_id=tenant.id,
            name=data['name'],
            org_type='agency',
            created_by=user.id
        )

        # Send email verification OTP
        otp_code = _issue_otp(user.email)

        tokens = get_tokens_for_user(user)
        response_data = {
            'user': UserSerializer(user).data,
            **tokens,
        }

        if settings.ENVIRONMENT == 'development':
            response_data['otp_code'] = otp_code
            response_data['is_development_mode'] = True

        return success_response(
            data=response_data,
            message="Account created. Check your email for a verification code.",
            status_code=status.HTTP_201_CREATED,
        )


class RegisterCandidateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterCandidateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        data = serializer.validated_data

        public_tenant = Client.objects.get(schema_name='public')

        user = CustomUser.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='candidate',
            tenant_id=public_tenant.id,
        )

        # Send email verification OTP
        otp_code = _issue_otp(user.email)

        tokens = get_tokens_for_user(user)
        response_data = {
            'user': UserSerializer(user).data,
            **tokens,
        }

        if settings.ENVIRONMENT == 'development':
            response_data['otp_code'] = otp_code
            response_data['is_development_mode'] = True

        return success_response(
            data=response_data,
            message="Account created. Check your email for a verification code.",
            status_code=status.HTTP_201_CREATED,
        )


# ─── OTP Verification ─────────────────────────────────────────────────────────

class SendOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        email = serializer.validated_data['email'].lower()

        # Check resend cooldown
        last_otp = EmailOTP.objects.filter(email=email).order_by('-created_at').first()
        if last_otp:
            cooldown = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 30)
            elapsed = (timezone.now() - last_otp.created_at).total_seconds()
            if elapsed < cooldown:
                remaining = int(cooldown - elapsed)
                return error_response(f"Please wait {remaining} seconds before requesting a new code.")

        # Silently succeed if email not found — prevents user enumeration
        otp_code = None
        if CustomUser.objects.filter(email=email).exists():
            otp_code = _issue_otp(email)

        data = {}
        if settings.ENVIRONMENT == 'development' and otp_code:
            data['otp_code'] = otp_code
            data['is_development_mode'] = True

        return success_response(
            data=data,
            message="If that email exists, a verification code was sent."
        )


class VerifyOTPView(APIView):
    # AllowAny + no authentication_classes: the OTP code itself is the
    # verification factor. We must clear authentication_classes too, because
    # DRF runs authenticators before checking permissions — an expired JWT in
    # the Authorization header would raise AuthenticationFailed (401) even
    # with AllowAny, which is exactly the bug we're fixing.
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"OTP verification failed: Validation error — {serializer.errors}")
            return error_response("Validation failed", serializer.errors)

        email = serializer.validated_data['email'].lower()
        code = serializer.validated_data['code']

        logger.info(f"OTP verify attempt for {email}")

        # Look up the user by email (no JWT required)
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            logger.warning(f"OTP verification failed: No account for {email}")
            return error_response("No account found for this email.")

        # Find the latest unused OTP
        try:
            otp = EmailOTP.objects.filter(
                email=email,
                is_used=False
            ).order_by('-created_at').first()
        except Exception as e:
            logger.error(f"Database error during OTP lookup for {email}: {str(e)}")
            return error_response("A database error occurred. Please try again later.")

        if not otp:
            logger.info(f"OTP verification failed: No active code for {email}")
            return error_response("No active verification code found for this email.")

        # Check expiry
        if otp.expires_at < timezone.now():
            logger.info(f"OTP verification failed: Code expired for {email}")
            return error_response("Verification code has expired.")

        # Check max attempts
        max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
        if otp.attempts >= max_attempts:
            logger.info(f"OTP verification failed: Max attempts reached for {email}")
            otp.is_used = True  # Invalidate after too many attempts
            otp.save()
            return error_response("Maximum attempts reached. Please request a new code.")

        # Dev-mode master OTP: accept 123456 in development without checking
        # the real code. Has zero effect in production (DEBUG=False, ENVIRONMENT!=development).
        _is_dev = settings.DEBUG or getattr(settings, 'ENVIRONMENT', 'production') == 'development'
        _dev_bypass = _is_dev and code == '123456'

        if _dev_bypass:
            print(f"DEV MODE OTP USED: 123456 for {email}")
            logger.warning(f"DEV MODE OTP USED: 123456 for {email}")
        elif otp.code != code:
            otp.attempts += 1
            otp.save()
            remaining = max_attempts - otp.attempts
            logger.info(f"OTP verification failed: Invalid code for {email}. {remaining} attempts left.")
            return error_response(f"Invalid code. {remaining} attempts remaining.")

        # Success — mark OTP used and user email as verified
        try:
            otp.is_used = True
            otp.is_verified = True
            otp.save()

            user.email_verified = True
            user.save(update_fields=['email_verified', 'updated_at'])
            logger.info(f"OTP verification successful for user {user.id} ({email})")
        except Exception as e:
            logger.error(f"Error updating verified status for {email}: {str(e)}")
            return error_response("Error completing verification.")

        # Issue fresh tokens so the frontend can persist a valid session
        tokens = get_tokens_for_user(user)
        return success_response(
            data={
                'user': UserSerializer(user).data,
                **tokens,
            },
            message="Email verified successfully.",
        )


# ─── Onboarding Wizard ────────────────────────────────────────────────────────

class CompleteOnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        user = request.user

        # Derive user_type from signup role — the user already chose company or
        # agency during registration, so we must not ask again.
        _ROLE_TO_USER_TYPE = {
            'tenant_admin': 'company',
            'recruiter': 'company',
            'hiring_manager': 'company',
            'agency_owner': 'agency',
            'agency_admin': 'agency',
            'agency_recruiter': 'agency',
        }
        data = dict(serializer.validated_data)
        data.setdefault('user_type', _ROLE_TO_USER_TYPE.get(user.role, 'company'))

        # Persist onboarding preferences to user metadata
        user.metadata['onboarding'] = {
            'user_type': data['user_type'],
            'hiring_style': data['hiring_style'],
            'team_size': data['team_size'],
            'automation_preference': data['automation_preference'],
            'completed_at': timezone.now().isoformat(),
        }
        user.save(update_fields=['metadata'])

        # Auto-configure workspace
        _auto_configure(user, data)

        # Emit event
        events.onboarding.completed.send(
            sender=self.__class__,
            user=user,
            preferences=data,
            request=request,
        )

        return success_response(
            data={'user': UserSerializer(user).data},
            message="Onboarding complete. Your workspace is ready.",
        )


# ─── Login / Auth ─────────────────────────────────────────────────────────────

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        data = serializer.validated_data
        user = authenticate(
            request,
            username=data['email'].lower(),
            password=data['password'],
        )

        if not user:
            return error_response(
                "Invalid email or password.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return error_response(
                "Your account has been deactivated.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if not user.email_verified:
            # Re-send OTP so user can verify right away
            _issue_otp(user.email)
            return error_response(
                "Please verify your email before signing in. A new code has been sent.",
                errors={'error_code': 'email_not_verified', 'email': user.email},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        user.last_login_at = timezone.now()
        user.last_login_ip = request.META.get('REMOTE_ADDR', '')
        user.save(update_fields=['last_login_at', 'last_login_ip'])

        tokens = get_tokens_for_user(user)
        return success_response(
            data={
                'user': UserSerializer(user).data,
                **tokens,
            },
            message="Login successful.",
        )


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        try:
            refresh = RefreshToken(serializer.validated_data['refresh_token'])
            return success_response(
                data={
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                },
                message="Token refreshed.",
            )
        except TokenError as e:
            return error_response(str(e), status_code=status.HTTP_401_UNAUTHORIZED)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        return success_response(
            message="If this email exists, a password reset link has been sent."
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        return success_response(message="Password reset successfully.")


class VerifyEmailView(APIView):
    """Legacy endpoint — kept for backward compat. Use /verify-otp/ instead."""
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return error_response("Token is required.", status_code=status.HTTP_400_BAD_REQUEST)

        return success_response(message="Email verified successfully.")


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        try:
            refresh = RefreshToken(serializer.validated_data['refresh_token'])
            refresh.blacklist()
        except TokenError:
            pass

        return success_response(message="Logged out successfully.")


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(
            data={'user': UserSerializer(request.user).data},
            message="Profile retrieved.",
        )

    def put(self, request):
        serializer = UpdateProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        serializer.save()
        return success_response(
            data={'user': UserSerializer(request.user).data},
            message="Profile updated.",
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return error_response(
                "Current password is incorrect.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return success_response(message="Password changed successfully.")


class MFAEnableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.mfa_enabled:
            return error_response("MFA is already enabled.")

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        qr_url = totp.provisioning_uri(
            name=user.email,
            issuer_name="Talent OS"
        )

        user.mfa_secret = secret
        user.save(update_fields=['mfa_secret'])

        return success_response(
            data={'qr_code': qr_url, 'secret': secret},
            message="Scan QR code with your authenticator app, then verify.",
        )


class MFAVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MFAVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        user = request.user
        if not user.mfa_secret:
            return error_response("MFA setup not initiated. Call /mfa/enable/ first.")

        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(serializer.validated_data['code']):
            return error_response("Invalid MFA code.", status_code=status.HTTP_400_BAD_REQUEST)

        user.mfa_enabled = True
        user.save(update_fields=['mfa_enabled'])
        return success_response(message="MFA enabled successfully.")
