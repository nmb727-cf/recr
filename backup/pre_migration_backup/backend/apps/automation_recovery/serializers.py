from rest_framework import serializers
from .models import (
    WorkflowRecoveryCase,
    WorkflowRecoveryAttempt,
    WorkflowDeadLetterItem,
    WorkflowFallbackRule,
    WorkflowRecoveryInsight,
)


class WorkflowRecoveryAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRecoveryAttempt
        fields = [
            'id', 'tenant_id', 'recovery_case_id', 'attempt_number',
            'strategy_used', 'started_at', 'completed_at', 'status',
            'error_message', 'recovery_output', 'created_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at']


class WorkflowRecoveryCaseSerializer(serializers.ModelSerializer):
    attempts = WorkflowRecoveryAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowRecoveryCase
        fields = [
            'id', 'tenant_id', 'workflow_id', 'execution_id',
            'failure_node_id', 'failure_type', 'recovery_status',
            'recovery_strategy', 'retry_count', 'max_retry_limit',
            'error_message', 'execution_snapshot', 'next_retry_at',
            'created_at', 'updated_at', 'resolved_at', 'attempts',
        ]
        read_only_fields = ['id', 'tenant_id', 'retry_count', 'created_at', 'updated_at']


class WorkflowRecoveryCaseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views (no nested attempts)."""

    class Meta:
        model = WorkflowRecoveryCase
        fields = [
            'id', 'workflow_id', 'execution_id', 'failure_type',
            'recovery_status', 'recovery_strategy', 'retry_count',
            'max_retry_limit', 'created_at', 'updated_at',
        ]


class WorkflowDeadLetterItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDeadLetterItem
        fields = [
            'id', 'tenant_id', 'workflow_id', 'execution_id',
            'entity_type', 'entity_id', 'failed_node_id',
            'failure_reason', 'payload_snapshot', 'status',
            'assigned_to', 'created_at', 'resolved_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at']


class WorkflowFallbackRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowFallbackRule
        fields = [
            'id', 'tenant_id', 'workflow_id', 'node_id',
            'failure_type', 'fallback_action_type', 'fallback_config',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at']


class WorkflowRecoveryInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRecoveryInsight
        fields = [
            'id', 'tenant_id', 'workflow_id', 'insight_type',
            'title', 'description', 'recommendation',
            'occurrence_count', 'last_seen_at', 'status', 'created_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'last_seen_at']
