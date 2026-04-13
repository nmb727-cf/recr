from rest_framework import serializers

from apps.automation_notifications.models import (
    WorkflowEscalationNotification,
    WorkflowNotificationDelivery,
    WorkflowNotificationInsight,
    WorkflowNotificationPreference,
    WorkflowNotificationRule,
)


class WorkflowNotificationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNotificationRule
        fields = [
            'id', 'tenant_id', 'workflow_id', 'action_node_id',
            'notification_event', 'recipient_type', 'channel', 'template_id',
            'fallback_channels', 'send_delay_minutes', 'throttle_window_minutes',
            'dedupe_key_template', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class WorkflowNotificationDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNotificationDelivery
        fields = [
            'id', 'tenant_id', 'execution_id', 'workflow_id', 'notification_rule',
            'recipient_user_id', 'recipient_email', 'channel', 'status',
            'provider_message_id', 'subject', 'dedupe_key',
            'sent_at', 'delivered_at', 'failed_at',
            'retry_count', 'failure_reason', 'created_at',
        ]
        read_only_fields = fields


class WorkflowNotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNotificationPreference
        fields = [
            'id', 'tenant_id', 'user_id', 'notification_type',
            'preferred_channels', 'quiet_hours_start', 'quiet_hours_end',
            'allow_escalation_override', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class WorkflowEscalationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowEscalationNotification
        fields = [
            'id', 'tenant_id', 'workflow_id', 'execution_id',
            'escalation_level', 'trigger_reason', 'target_recipient_type',
            'channel', 'status', 'sent_at', 'created_at',
        ]
        read_only_fields = fields


class WorkflowNotificationInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNotificationInsight
        fields = [
            'id', 'tenant_id', 'workflow_id', 'insight_type',
            'title', 'description', 'metric_value', 'created_at',
        ]
        read_only_fields = fields


class TestSendSerializer(serializers.Serializer):
    workflow_id  = serializers.UUIDField()
    rule_id      = serializers.UUIDField()
    recipient_id = serializers.UUIDField(required=False, allow_null=True)
    channel      = serializers.CharField(max_length=20)
