import uuid
import pyotp
from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.accounts.models import CustomUser
from apps.tenants.models import Client, Domain
from apps.organisations.models import Organisation
from apps.accounts.serializers import (
    RegisterCompanySerializer, RegisterAgencySerializer, RegisterCandidateSerializer,
    LoginSerializer, UserSerializer, UpdateProfileSerializer,
    ChangePasswordSerializer, MFAVerifySerializer, LogoutSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, RefreshTokenSerializer,
)
from apps.core.responses import success_response, error_response
from apps.core import events


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

    # Ensure unique slug and schema_name
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

        # Auto-create Organisation record to prevent 404s
        Organisation.objects.create(
            tenant_id=tenant.id,
            name=data['name'],
            org_type='company',
            created_by=user.id
        )

        # Emit Event
        events.company.created.send(
            sender=self.__class__,
            tenant=tenant,
            user=user,
            request=request
        )

        tokens = get_tokens_for_user(user)
        return success_response(
            data={
                'user': UserSerializer(user).data,
                **tokens,
            },
            message="Company registered successfully. Please verify your email.",
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

        # Auto-create Organisation record
        Organisation.objects.create(
            tenant_id=tenant.id,
            name=data['name'],
            org_type='agency',
            created_by=user.id
        )

        tokens = get_tokens_for_user(user)
        return success_response(
            data={
                'user': UserSerializer(user).data,
                **tokens,
            },
            message="Agency registered successfully. Please verify your email.",
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

        tokens = get_tokens_for_user(user)
        return success_response(
            data={
                'user': UserSerializer(user).data,
                **tokens,
            },
            message="Candidate registered successfully.",
            status_code=status.HTTP_201_CREATED,
        )


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
