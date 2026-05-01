from rest_framework import serializers

from apps.automation_tasks.models import (
    WorkflowTaskDependency,
    WorkflowTaskEscalation,
    WorkflowTaskExecution,
    WorkflowTaskRule,
)


class WorkflowTaskRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTaskRule
        fields = [
            'id', 'tenant_id', 'workflow_id', 'node_id',
            'task_title_template', 'task_description_template',
            'assignee_type', 'assignee_field', 'priority',
            'due_in_minutes', 'escalate_after_minutes',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at']


class WorkflowTaskEscalationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTaskEscalation
        fields = [
            'id', 'tenant_id', 'task_execution', 'escalation_level',
            'escalated_to', 'escalated_to_role', 'reason', 'escalated_at',
        ]
        read_only_fields = fields


class WorkflowTaskExecutionSerializer(serializers.ModelSerializer):
    escalations = WorkflowTaskEscalationSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowTaskExecution
        fields = [
            'id', 'tenant_id', 'workflow_id', 'execution_id', 'rule',
            'task_title', 'task_description', 'assignee_user_id',
            'priority', 'due_at', 'status', 'escalated',
            'completed_at', 'created_at', 'updated_at', 'escalations',
        ]
        read_only_fields = fields


class WorkflowTaskDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTaskDependency
        fields = ['id', 'tenant_id', 'task_execution', 'depends_on_task', 'created_at']
        read_only_fields = fields


class TaskTestSerializer(serializers.Serializer):
    workflow_id = serializers.UUIDField()
    rule_id     = serializers.UUIDField()
    context     = serializers.DictField(required=False, default=dict)
