from rest_framework import serializers

from apps.automation_permissions.models import (
    WorkflowAccessAudit,
    WorkflowPermissionPolicy,
    WorkflowPermissionRule,
    WorkflowRestrictedAction,
)


class WorkflowPermissionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowPermissionRule
        fields = [
            'id', 'role_code', 'module_scope', 'resource_type',
            'action_type', 'permission_level', 'conditions', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowPermissionPolicySerializer(serializers.ModelSerializer):
    rules = WorkflowPermissionRuleSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowPermissionPolicy
        fields = [
            'id', 'tenant_id', 'name', 'description', 'is_active',
            'created_by', 'created_at', 'updated_at', 'rules',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_by', 'created_at', 'updated_at']


class WorkflowPermissionPolicyWriteSerializer(serializers.ModelSerializer):
    """Used for create / update — rules submitted inline."""
    rules = WorkflowPermissionRuleSerializer(many=True, required=False)

    class Meta:
        model = WorkflowPermissionPolicy
        fields = ['name', 'description', 'is_active', 'rules']

    def create(self, validated_data):
        rules_data = validated_data.pop('rules', [])
        policy = WorkflowPermissionPolicy.objects.create(**validated_data)
        for r in rules_data:
            WorkflowPermissionRule.objects.create(policy=policy, **r)
        return policy

    def update(self, instance, validated_data):
        rules_data = validated_data.pop('rules', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if rules_data is not None:
            instance.rules.all().delete()
            for r in rules_data:
                WorkflowPermissionRule.objects.create(policy=instance, **r)
        return instance


class WorkflowRestrictedActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRestrictedAction
        fields = [
            'id', 'tenant_id', 'action_key', 'description',
            'severity', 'requires_approval', 'requires_admin', 'created_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'action_key', 'created_at']


class WorkflowAccessAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAccessAudit
        fields = [
            'id', 'tenant_id', 'user_id', 'workflow_id',
            'action_attempted', 'decision', 'reason', 'metadata', 'created_at',
        ]
        read_only_fields = fields


class PermissionCheckSerializer(serializers.Serializer):
    workflow_id = serializers.UUIDField(required=False, allow_null=True)
    action      = serializers.CharField(max_length=100)
    resource_type = serializers.CharField(max_length=50, default='workflow')
