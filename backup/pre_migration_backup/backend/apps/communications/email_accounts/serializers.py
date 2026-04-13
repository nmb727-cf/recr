from rest_framework import serializers

from apps.communications.models import EmailPreference, EmailSendingAccount
from apps.communications.utils import encrypt_string


class EmailSendingAccountSerializer(serializers.ModelSerializer):
    smtp_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = EmailSendingAccount
        fields = [
            'id', 'tenant_id', 'user_id', 'provider_type', 'account_scope',
            'email_address', 'display_name', 'from_name',
            'status', 'is_default_sender', 'can_send', 'can_receive',
            'token_expires_at',
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_encryption_mode',
            'signature_html', 'signature_text',
            'last_tested_at', 'last_success_at', 'last_failure_at', 'failure_reason',
            'health_status', 'metadata_json', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'user_id', 'status', 'token_expires_at',
            'last_tested_at', 'last_success_at', 'last_failure_at', 'failure_reason',
            'health_status', 'created_at', 'updated_at',
        ]

    def create(self, validated_data):
        smtp_password = validated_data.pop('smtp_password', '')
        if smtp_password:
            validated_data['smtp_password_encrypted'] = encrypt_string(smtp_password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        smtp_password = validated_data.pop('smtp_password', None)
        if smtp_password is not None:
            instance.smtp_password_encrypted = encrypt_string(smtp_password)
        return super().update(instance, validated_data)


class EmailPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailPreference
        fields = [
            'id', 'tenant_id', 'user_id', 'default_sender_account',
            'fallback_behavior', 'default_signature_mode', 'allow_system_fallback',
            'banner_dismissed', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'user_id', 'created_at', 'updated_at']
