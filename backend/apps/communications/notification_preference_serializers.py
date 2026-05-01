"""
User Notification Preference Serializers
=========================================
"""
from rest_framework import serializers

from apps.communications.models import (
    UserNotificationPreference,
    UserNotificationSetting,
)
from apps.communications.notification_preference_service import (
    NOTIFICATION_CATEGORIES,
    NOTIFICATION_CHANNELS,
    _PRIORITY_RANK,
    _validate_timezone,
)


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationPreference
        fields = [
            'id',
            'category',
            'channel_type',
            'is_enabled',
            'min_priority',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']


class UserNotificationPreferenceUpdateSerializer(serializers.Serializer):
    """Single-item preference update."""
    category = serializers.ChoiceField(choices=NOTIFICATION_CATEGORIES)
    channel_type = serializers.ChoiceField(choices=NOTIFICATION_CHANNELS)
    is_enabled = serializers.BooleanField(required=False)
    min_priority = serializers.ChoiceField(
        choices=list(_PRIORITY_RANK.keys()),
        required=False,
    )

    def validate(self, data):
        if 'is_enabled' not in data and 'min_priority' not in data:
            raise serializers.ValidationError(
                "At least one of 'is_enabled' or 'min_priority' must be provided."
            )
        return data


class UserNotificationPreferenceBulkUpdateSerializer(serializers.Serializer):
    """Bulk preference update — list of category+channel updates."""
    updates = serializers.ListField(
        child=UserNotificationPreferenceUpdateSerializer(),
        min_length=1,
        max_length=50,
    )


class UserNotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationSetting
        fields = [
            'id',
            'user_id',
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
            'timezone',
            'digest_mode',
            'all_email_enabled',
            'all_sms_enabled',
            'all_whatsapp_enabled',
            'all_push_enabled',
            'updated_at',
        ]
        read_only_fields = ['id', 'user_id', 'updated_at']


class UserNotificationSettingUpdateSerializer(serializers.Serializer):
    """Validated settings update — all fields optional (PATCH semantics)."""
    quiet_hours_enabled = serializers.BooleanField(required=False)
    quiet_hours_start = serializers.TimeField(required=False, allow_null=True)
    quiet_hours_end = serializers.TimeField(required=False, allow_null=True)
    timezone = serializers.CharField(max_length=50, required=False)
    digest_mode = serializers.ChoiceField(
        choices=['none', 'hourly', 'daily', 'weekly'],
        required=False,
    )
    all_email_enabled = serializers.BooleanField(required=False)
    all_sms_enabled = serializers.BooleanField(required=False)
    all_whatsapp_enabled = serializers.BooleanField(required=False)
    all_push_enabled = serializers.BooleanField(required=False)

    def validate_timezone(self, value):
        try:
            return _validate_timezone(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))

    def validate(self, data):
        # When enabling quiet hours, both bounds must be known
        if data.get('quiet_hours_enabled') is True:
            has_start = (
                data.get('quiet_hours_start') is not None
                or (self.instance and self.instance.quiet_hours_start)
            )
            has_end = (
                data.get('quiet_hours_end') is not None
                or (self.instance and self.instance.quiet_hours_end)
            )
            if not has_start or not has_end:
                raise serializers.ValidationError(
                    "quiet_hours_start and quiet_hours_end are required when enabling quiet hours."
                )
        return data
