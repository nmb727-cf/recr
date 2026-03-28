from rest_framework import serializers

from apps.automation.models import AutomationRule, AutomationLog


class AutomationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationRule
        fields = [
            'id', 'tenant_id', 'name', 'description', 'trigger_event',
            'conditions', 'actions', 'is_active', 'is_system',
            'execution_count', 'last_executed_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'is_system', 'execution_count',
            'last_executed_at', 'created_at', 'updated_at',
        ]

    def validate_actions(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("actions must be a list.")
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("each action must be an object.")
            if not item.get('type'):
                raise serializers.ValidationError("each action requires a type.")
        return value


class AutomationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationLog
        fields = [
            'id', 'rule_id', 'trigger_event', 'entity_type', 'entity_id',
            'status', 'actions_taken', 'error_message', 'executed_at',
        ]


class AutomationTriggerSerializer(serializers.Serializer):
    trigger_event = serializers.CharField(max_length=100)
    entity_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    entity_id = serializers.UUIDField(required=False, allow_null=True)
    context = serializers.JSONField(required=False)

