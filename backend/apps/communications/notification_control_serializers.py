"""
Notification Control Center — Serializers
"""
from rest_framework import serializers

from apps.communications.notification_control_models import (
    NotificationRule,
    NotificationChannelSetting,
    TenantNotificationPreferenceDefaults,
)


class NotificationRuleSerializer(serializers.ModelSerializer):
    # Expose whether this is a system default (read-only info for UI)
    is_tenant_override = serializers.SerializerMethodField()

    class Meta:
        model = NotificationRule
        fields = [
            'id',
            'tenant_id',
            'event_key',
            'business_label',
            'category',
            'priority',
            'is_active',
            'is_system',
            'is_locked',
            'in_app_enabled',
            'email_enabled',
            'whatsapp_enabled',
            'sms_enabled',
            'send_immediately',
            'fallback_enabled',
            'fallback_delay_minutes',
            'escalation_enabled',
            'escalation_delay_minutes',
            'escalation_target_type',
            'template_id',
            'template_name',
            'allow_user_override',
            'admin_notes',
            'is_tenant_override',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'event_key', 'is_system', 'created_at', 'updated_at',
        ]

    def get_is_tenant_override(self, obj) -> bool:
        return obj.tenant_id is not None


class NotificationRuleWriteSerializer(serializers.ModelSerializer):
    """Used for create / update operations from admin."""

    class Meta:
        model = NotificationRule
        fields = [
            'event_key',
            'business_label',
            'category',
            'priority',
            'is_active',
            'in_app_enabled',
            'email_enabled',
            'whatsapp_enabled',
            'sms_enabled',
            'send_immediately',
            'fallback_enabled',
            'fallback_delay_minutes',
            'escalation_enabled',
            'escalation_delay_minutes',
            'escalation_target_type',
            'template_id',
            'template_name',
            'allow_user_override',
            'admin_notes',
        ]

    def validate_fallback_delay_minutes(self, value):
        if value < 0:
            raise serializers.ValidationError('Fallback delay must be 0 or greater.')
        return value

    def validate_escalation_delay_minutes(self, value):
        if value < 0:
            raise serializers.ValidationError('Escalation delay must be 0 or greater.')
        return value


class NotificationChannelSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannelSetting
        fields = [
            'id',
            'tenant_id',
            'channel_type',
            'is_enabled',
            'provider',
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
            'sender_name',
            'sender_email',
            'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'channel_type', 'updated_at']


class NotificationChannelSettingUpdateSerializer(serializers.ModelSerializer):
    channel_type = serializers.CharField()

    class Meta:
        model = NotificationChannelSetting
        fields = [
            'channel_type',
            'is_enabled',
            'provider',
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
            'sender_name',
            'sender_email',
        ]


class TenantNotificationPreferenceDefaultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantNotificationPreferenceDefaults
        fields = [
            'id',
            'tenant_id',
            'default_in_app_enabled',
            'default_email_enabled',
            'default_reminder_enabled',
            'allow_user_override',
            'digest_frequency',
            'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'updated_at']
