from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from apps.accounts.models import CustomUser
from apps.tenants.models import Client
from apps.rbac.utils import get_user_permissions

# Forces at least one letter — prevents all-numeric strings from being
# schema-compliant, matching Django's NumericPasswordValidator requirement.
_password_has_letter = RegexValidator(
    r'[a-zA-Z]',
    'Password must contain at least one letter.',
)


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'schema_name', 'on_trial', 'paid_until']


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    is_super_admin = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'avatar_url', 'role', 'is_super_admin', 'is_superuser', 'is_staff', 'is_active',
            'email_verified', 'mfa_enabled', 'timezone', 'language',
            'notification_preferences', 'ui_preferences',
            'tenant_id', 'created_at', 'last_login_at',
            'permissions',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'last_login_at', 'email_verified']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_permissions(self, obj):
        return sorted(get_user_permissions(obj))

    def get_is_super_admin(self, obj):
        return bool(
            getattr(obj, 'role', '') == 'super_admin'
            or getattr(obj, 'is_superuser', False)
            or getattr(obj, 'is_staff', False)
        )


class RegisterCompanySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)  # Company Name
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, validators=[_password_has_letter, validate_password])
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    country_code = serializers.CharField(max_length=5, required=False, default='IN')
    timezone = serializers.CharField(max_length=50, required=False, default='UTC')

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()


class RegisterAgencySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)  # Agency Name
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, validators=[_password_has_letter, validate_password])
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    country_code = serializers.CharField(max_length=5, required=False, default='IN')
    timezone = serializers.CharField(max_length=50, required=False, default='UTC')

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()


class RegisterCandidateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, validators=[_password_has_letter, validate_password])
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    tenant_slug = serializers.CharField(required=False, allow_blank=True)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, validators=[_password_has_letter, validate_password])


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'avatar_url',
                  'notification_preferences', 'ui_preferences', 'timezone', 'language']


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class MFAVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, min_length=6)


class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)


class OnboardingSerializer(serializers.Serializer):
    # user_type is optional — the view derives it from request.user.role so the
    # frontend does not need to ask the user (they already chose a signup flow).
    user_type = serializers.ChoiceField(choices=['company', 'agency', 'both'], required=False)
    hiring_style = serializers.ChoiceField(choices=['internal', 'agency', 'mixed'])
    team_size = serializers.ChoiceField(choices=['1-5', '5-20', '20+'])
    automation_preference = serializers.ChoiceField(choices=['manual', 'smart', 'fully_automated'])
