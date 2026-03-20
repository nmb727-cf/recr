from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from apps.accounts.models import CustomUser
from apps.tenants.models import Client


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'schema_name', 'on_trial', 'paid_until']


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'avatar_url', 'role', 'is_active',
            'email_verified', 'mfa_enabled', 'timezone', 'language',
            'notification_preferences', 'ui_preferences',
            'created_at', 'last_login_at',
        ]
        read_only_fields = ['id', 'created_at', 'last_login_at', 'email_verified']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class RegisterCompanySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    company_name = serializers.CharField(max_length=255)
    country_code = serializers.CharField(max_length=5, required=False, default='IN')

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()


class RegisterAgencySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    agency_name = serializers.CharField(max_length=255)
    country_code = serializers.CharField(max_length=5, required=False, default='IN')

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()


class RegisterCandidateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])

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
    new_password = serializers.CharField(validators=[validate_password])


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