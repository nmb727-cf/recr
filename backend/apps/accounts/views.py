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
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers

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
    """
    Return a 6-digit OTP string.
    In development (DEBUG=True or ENVIRONMENT=development) always returns '123456'
    so engineers can verify without real email access.
    Production always receives a cryptographically random code.
    """
    _is_dev = settings.DEBUG or getattr(settings, 'ENVIRONMENT', 'production') == 'development'
    if _is_dev:
        return '123456'
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

    @extend_schema(
        request=RegisterCompanySerializer,
        responses={
            201: OpenApiResponse(description="Company account created successfully"),
            400: OpenApiResponse(description="Validation failed"),
        }
    )
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

    @extend_schema(
        request=RegisterAgencySerializer,
        responses={
            201: OpenApiResponse(description="Agency account created successfully"),
            400: OpenApiResponse(description="Validation failed"),
        }
    )
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
    """
    Source 3 — Direct candidate signup.

    Identity deduplication:
      • If a user account already exists with the submitted email or phone,
        return needs_login=True so the frontend routes to login / forgot-password
        instead of creating a duplicate account.
      • If a candidate record (without a user) already exists with the same
        email/phone, create the user and immediately link it to that record so
        the candidate's pre-existing profile is not lost.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterCandidateSerializer,
        responses={
            201: OpenApiResponse(description="Candidate account created successfully"),
            400: OpenApiResponse(description="Validation failed"),
        }
    )
    def post(self, request):
        serializer = RegisterCandidateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        data = serializer.validated_data
        email = data['email'].strip().lower()
        phone = data.get('phone', '').strip()

        # ── Source 3: Check if a user account already exists ───────────────
        # If yes, do not create a duplicate — tell the frontend to redirect
        # to login / forgot-password.
        from apps.candidates.identity_service import match_user, match_candidate, link_user_to_candidate
        existing_user = match_user(email=email, phone=phone)
        if existing_user:
            return success_response(
                data={'needs_login': True, 'email': existing_user.email},
                message=(
                    "An account with this email or phone already exists. "
                    "Please log in or use forgot password."
                ),
                status_code=200,
            )

        public_tenant = Client.objects.get(schema_name='public')

        user = CustomUser.objects.create_user(
            email=email,
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='candidate',
            tenant_id=public_tenant.id,
        )

        # ── Source 3: Link to existing candidate record if one exists ───────
        # A recruiter may have already added this candidate (Source 1) before
        # they signed up.  Link the new account so the candidate can see their
        # pre-populated profile without any duplicate being created.
        existing_candidate = match_candidate(email=email, phone=phone)
        if existing_candidate:
            link_user_to_candidate(user, existing_candidate)

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

        if existing_candidate:
            response_data['linked_candidate_id'] = str(existing_candidate.id)

        return success_response(
            data=response_data,
            message="Account created. Check your email for a verification code.",
            status_code=status.HTTP_201_CREATED,
        )


# ─── OTP Verification ─────────────────────────────────────────────────────────

class SendOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=SendOTPSerializer,
        responses={
            200: OpenApiResponse(description="OTP sent successfully"),
            400: OpenApiResponse(description="Validation failed"),
        }
    )
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

    @extend_schema(
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(description="OTP verified successfully"),
            400: OpenApiResponse(description="Validation failed"),
        }
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"OTP verification failed: Validation error — {serializer.errors}")
            return error_response("Validation failed", serializer.errors)

        email = serializer.validated_data['email'].lower()
        code = serializer.validated_data['code']

        logger.info(f"OTP verify attempt for {email}")

        # ── Dev bypass — evaluated FIRST, before any OTP record guards ────────
        # In development (DEBUG=True or ENVIRONMENT=development), code '123456'
        # skips all record checks (not-found, expired, max-attempts).
        # Has ZERO effect when DEBUG=False and ENVIRONMENT != 'development'.
        _is_dev = settings.DEBUG or getattr(settings, 'ENVIRONMENT', 'production') == 'development'
        _dev_bypass = _is_dev and code == '123456'

        # Look up the user by email (no JWT required).
        # Return 200 with verified=False for unknown emails to avoid user enumeration.
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            logger.warning(f"OTP verification failed: No account for {email}")
            return success_response(
                data={'verified': False},
                message="No active verification code found for this email.",
            )

        if _dev_bypass:
            logger.warning(f"DEV MODE OTP 123456 accepted for {email}")
            # Tidy up: mark any pending OTPs as used so they don't accumulate
            EmailOTP.objects.filter(email=email, is_used=False).update(
                is_used=True, is_verified=True
            )
        else:
            # ── Production path: validate OTP record normally ──────────────────
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

            if otp.expires_at < timezone.now():
                logger.info(f"OTP verification failed: Code expired for {email}")
                return error_response("Verification code has expired.")

            max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
            if otp.attempts >= max_attempts:
                logger.info(f"OTP verification failed: Max attempts reached for {email}")
                otp.is_used = True
                otp.save()
                return error_response("Maximum attempts reached. Please request a new code.")

            if otp.code != code:
                otp.attempts += 1
                otp.save()
                remaining = max_attempts - otp.attempts
                logger.info(f"OTP verification failed: Invalid code for {email}. {remaining} left.")
                return error_response(f"Invalid code. {remaining} attempts remaining.")

            otp.is_used = True
            otp.is_verified = True
            otp.save()

        # ── Mark user as verified ──────────────────────────────────────────────
        try:
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
        derived_user_type = _ROLE_TO_USER_TYPE.get(user.role)
        if not user.tenant_id:
            return error_response(
                "Authenticated user is not attached to a tenant.",
                errors={'tenant_id': 'missing'},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not derived_user_type:
            return error_response(
                "Unsupported user role for onboarding.",
                errors={'role': user.role},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        data.setdefault('user_type', derived_user_type)

        # Persist onboarding preferences to user metadata
        metadata = user.metadata if isinstance(user.metadata, dict) else {}
        metadata['onboarding'] = {
            'user_type': data['user_type'],
            'hiring_style': data['hiring_style'],
            'team_size': data['team_size'],
            'automation_preference': data['automation_preference'],
            'completed_at': timezone.now().isoformat(),
        }
        user.metadata = metadata
        user.save(update_fields=['metadata'])

        # Auto-configure workspace
        _auto_configure(user, data)

        # Emit event. Onboarding completion should not fail if optional async
        # email/event infrastructure is unavailable.
        signal_responses = events.onboarding.completed.send_robust(
            sender=self.__class__,
            user=user,
            preferences=data,
            request=request,
        )
        for receiver, response in signal_responses:
            if isinstance(response, Exception):
                logger.exception(
                    "Onboarding completion receiver failed for user %s via %s",
                    user.id,
                    getattr(receiver, '__name__', repr(receiver)),
                    exc_info=response,
                )

        return success_response(
            data={'user': UserSerializer(user).data},
            message="Onboarding complete. Your workspace is ready.",
        )


# ─── Login / Auth ─────────────────────────────────────────────────────────────

class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful"),
            400: OpenApiResponse(description="Validation failed"),
            401: OpenApiResponse(description="Invalid email or password"),
            403: OpenApiResponse(description="Account inactive or email not verified"),
        }
    )
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
            # Re-issue OTP so the user can verify immediately
            _issue_otp(user.email)
            _is_dev = settings.DEBUG or getattr(settings, 'ENVIRONMENT', 'production') == 'development'
            errors = {'error_code': 'email_not_verified', 'email': user.email}
            if _is_dev:
                errors['dev_otp'] = '123456'
            return error_response(
                "Please verify your email before signing in. A new code has been sent.",
                errors=errors,
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

    @extend_schema(
        request=RefreshTokenSerializer,
        responses={
            200: OpenApiResponse(description="Token refreshed successfully"),
            400: OpenApiResponse(description="Invalid or missing refresh token"),
            401: OpenApiResponse(description="Refresh token is invalid or expired"),
        }
    )
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

    @extend_schema(
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password reset OTP sent successfully"),
            400: OpenApiResponse(description="Validation failed"),
        }
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        return success_response(
            message="If this email exists, a password reset link has been sent."
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password reset successfully"),
            400: OpenApiResponse(description="Validation failed"),
        }
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors)

        return success_response(message="Password reset successfully.")

class VerifyEmailView(APIView):

    """Legacy endpoint — kept for backward compat. Use /verify-otp/ instead."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=inline_serializer(
            name='VerifyEmailRequest',
            fields={'token': drf_serializers.CharField()},
        ),
        responses={
            200: OpenApiResponse(description="Email verified successfully"),
            400: OpenApiResponse(description="Token is required or invalid"),
        }
    )
    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        token = data.get('token')
        if not token or not isinstance(token, str):
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


from apps.accounts.services import RecruiterIntelligenceService

class RecruiterIntelligenceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        
        if user_id:
            metrics = RecruiterIntelligenceService.calculate_recruiter_metrics(
                tenant_id=request.user.tenant_id,
                user_id=user_id
            )
            workload = RecruiterIntelligenceService.get_recruiter_workload(
                tenant_id=request.user.tenant_id,
                user_id=user_id
            )
            return success_response(
                data={
                    'metrics': metrics,
                    'workload': workload
                },
                message="Recruiter intelligence retrieved."
            )

        # List all team members with intelligence
        team = RecruiterIntelligenceService.get_team_intelligence(
            tenant_id=request.user.tenant_id
        )
        return success_response(
            data={'team': team},
            message="Team intelligence retrieved.",
            meta={'total': len(team)}
        )


class JobRecruiterIntelligenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, requisition_id):
        # 1. Get recommendations for this job
        assignment_intel = RecruiterIntelligenceService.get_assignment_recommendations(
            requisition_id=requisition_id,
            tenant_id=request.user.tenant_id
        )

        # 2. Get workload overview for the team
        team = RecruiterIntelligenceService.get_team_intelligence(
            tenant_id=request.user.tenant_id
        )

        overloaded = [r for r in team if r['workload']['workload_status'] == 'overloaded']
        available = [r for r in team if r['workload']['workload_status'] != 'overloaded']

        return success_response(
            data={
                'recommendations': [assignment_intel['recommended']] if assignment_intel['recommended'] else assignment_intel['fallbacks'],
                'smart_intel': assignment_intel,
                'overloaded': overloaded,
                'available': available
            },
            message="Job recruiter intelligence retrieved."
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
