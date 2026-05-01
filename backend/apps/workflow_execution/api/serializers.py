from rest_framework import serializers
from apps.workflow_execution.models import (
    WorkflowInstance,
    WorkflowStageExecution,
    WorkflowExecutionTimeline,
    WorkflowStageTransition,
    WorkflowWaitState,
    WorkflowTransitionLog,
    WorkflowFailureLog,
    WorkflowTimeline,
    WorkflowExecutionContext,
    WorkflowExecutionDecision,
    WorkflowOrchestratorLog,
    WorkflowStageSLA,
    WorkflowSLATracker,
    WorkflowSLAEvent,
    WorkflowNotificationRule,
    WorkflowNotificationLog,
    WorkflowNotificationQueue,
    WorkflowScheduledTask,
    WorkflowSchedulerLog,
    WorkflowConditionRule,
    WorkflowConditionGroup,
    WorkflowConditionEvaluationLog,
    WorkflowActionDefinition,
    WorkflowActionExecutionLog,
    WorkflowActionDependency,
    WorkflowHumanTask,
    WorkflowApprovalRule,
    WorkflowApprovalLog,
    WorkflowVersion,
    WorkflowDraft,
    WorkflowVersionChangeLog,
    WorkflowVersionComparison,
    WorkflowTemplate,
    WorkflowTemplateVersion,
    WorkflowTemplateUsage,
    WorkflowTemplateRating,
    WorkflowBuilderNode,
    WorkflowBuilderConnection,
    WorkflowBuilderLayout,
    WorkflowExecutionTimelineEntry,
    WorkflowExecutionTrace,
    WorkflowObservabilitySnapshot,
    WorkflowExecutionMetric,
    WorkflowRecoveryCase,
    WorkflowRetryAttempt,
    WorkflowRecoveryActionLog,
    WorkflowRecoveryPolicy,
    WorkflowMetricSnapshot,
    WorkflowStageMetric,
    WorkflowFailureMetric,
    WorkflowActionMetric,
    WorkflowAutomationImpactMetric,
    WorkflowEntityRoute,
    WorkflowActorAssignment,
    WorkflowHandoffCheckpoint,
    WorkflowRoutingRule,
    WorkflowRouteTimelineLog,
)
from apps.orchestration_center.models.event_trigger import (
    WorkflowEventDefinition,
    WorkflowEventSubscription,
    WorkflowEventLog,
    WorkflowEventDebugTrace,
)


# ------------------------------------------------------------------ #
# Core execution                                                        #
# ------------------------------------------------------------------ #

class WorkflowStageExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStageExecution
        fields = '__all__'


class WorkflowExecutionTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowExecutionTimeline
        fields = '__all__'


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    stage_executions = WorkflowStageExecutionSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowInstance
        fields = '__all__'


class WorkflowInstanceSummarySerializer(serializers.ModelSerializer):
    """Lightweight version for list views."""
    class Meta:
        model = WorkflowInstance
        fields = [
            'id', 'workflow_id', 'version_id', 'entity_type', 'entity_id',
            'status', 'wait_reason', 'current_stage_id',
            'started_at', 'completed_at',
        ]


# ------------------------------------------------------------------ #
# WorkflowStageTransition                                              #
# ------------------------------------------------------------------ #

class WorkflowStageTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStageTransition
        fields = [
            'id', 'tenant_id', 'workflow_id',
            'from_stage_id', 'to_stage_id',
            'transition_type', 'condition_config',
            'priority', 'label', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ------------------------------------------------------------------ #
# WorkflowWaitState                                                    #
# ------------------------------------------------------------------ #

class WorkflowWaitStateSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowWaitState
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'wait_type', 'wait_reason', 'resume_event',
            'timeout_at', 'status', 'created_at', 'resumed_at', 'resumed_by',
            'resume_context', 'duration_seconds',
        ]
        read_only_fields = fields

    def get_duration_seconds(self, obj):
        if obj.status == 'waiting':
            from django.utils import timezone
            return int((timezone.now() - obj.created_at).total_seconds())
        if obj.resumed_at:
            return int((obj.resumed_at - obj.created_at).total_seconds())
        return None


# ------------------------------------------------------------------ #
# WorkflowTransitionLog                                                #
# ------------------------------------------------------------------ #

class WorkflowTransitionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTransitionLog
        fields = [
            'id', 'tenant_id', 'workflow_instance',
            'from_stage', 'to_stage',
            'from_stage_id', 'from_stage_name',
            'to_stage_id', 'to_stage_name',
            'transition_type', 'label',
            'triggered_by', 'actor_id',
            'reason', 'condition_result', 'created_at',
        ]
        read_only_fields = fields


class WorkflowFailureLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowFailureLog
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'error_message', 'error_type', 'retry_count',
            'status', 'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTimeline
        fields = [
            'id', 'tenant_id', 'workflow_instance',
            'stage_execution', 'wait_state', 'transition_log', 'failure_log',
            'event_type', 'event_label',
            'actor_type', 'actor_id',
            'occurred_at', 'payload', 'metadata',
        ]
        read_only_fields = fields


class WorkflowExecutionContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowExecutionContext
        fields = [
            'id', 'tenant_id', 'workflow_instance',
            'context_key', 'context_value', 'source_type', 'updated_at',
        ]
        read_only_fields = fields


class WorkflowExecutionDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowExecutionDecision
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'decision_type', 'decision_result', 'decision_reason',
            'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowOrchestratorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowOrchestratorLog
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'log_type', 'message', 'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowStageSLASerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStageSLA
        fields = [
            'id', 'tenant_id', 'workflow_id', 'stage_id',
            'sla_duration', 'warning_duration', 'escalation_duration',
            'escalation_role', 'escalation_user', 'is_active', 'created_at',
        ]
        read_only_fields = fields


class WorkflowSLATrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowSLATracker
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution', 'stage_sla',
            'sla_start', 'warning_at', 'breach_at', 'escalated_at', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class WorkflowSLAEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowSLAEvent
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'event_type', 'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowNotificationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNotificationRule
        fields = [
            'id', 'tenant_id', 'workflow_id', 'stage_id',
            'trigger_type', 'recipient_type', 'channel',
            'template_key', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowNotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNotificationLog
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'recipient_type', 'recipient_id', 'channel',
            'template_key', 'message_preview', 'status',
            'sent_at', 'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowNotificationQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNotificationQueue
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'recipient_type', 'recipient_id', 'channel',
            'template_key', 'payload', 'status', 'scheduled_at',
            'processed_at', 'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowScheduledTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowScheduledTask
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'task_type', 'scheduled_at', 'status', 'payload',
            'retry_count', 'created_at', 'executed_at',
        ]
        read_only_fields = fields


class WorkflowSchedulerLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowSchedulerLog
        fields = [
            'id', 'tenant_id', 'task', 'workflow_instance',
            'task_type', 'status', 'message', 'created_at',
        ]
        read_only_fields = fields


class WorkflowConditionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowConditionRule
        fields = [
            'id', 'tenant_id', 'workflow_id', 'stage_id',
            'rule_name', 'rule_group', 'condition_type',
            'field_name', 'operator', 'expected_value',
            'logical_join', 'priority', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowConditionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowConditionGroup
        fields = [
            'id', 'tenant_id', 'workflow_id', 'stage_id',
            'group_name', 'success_transition_id', 'failure_transition_id',
            'default_transition_id', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowConditionEvaluationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowConditionEvaluationLog
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'condition_group', 'rule', 'evaluated_value', 'expected_value',
            'result', 'reason', 'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowActionDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowActionDefinition
        fields = [
            'id', 'tenant_id', 'workflow_id', 'stage_id',
            'action_name', 'action_type', 'action_config',
            'execution_order', 'run_mode', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowActionExecutionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowActionExecutionLog
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'action_definition', 'action_type', 'status',
            'started_at', 'completed_at', 'error_message',
            'execution_result', 'metadata', 'created_at',
        ]
        read_only_fields = fields


class WorkflowActionDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowActionDependency
        fields = [
            'id', 'tenant_id', 'action_definition', 'depends_on_action',
            'dependency_type', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowHumanTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowHumanTask
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'task_type', 'assigned_to_type', 'assigned_to_id',
            'title', 'description', 'priority', 'due_at',
            'status', 'created_at', 'completed_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowApprovalRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowApprovalRule
        fields = [
            'id', 'tenant_id', 'workflow_id', 'stage_id',
            'approval_type', 'required_approvals', 'approval_role',
            'escalation_role', 'timeout_hours', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowApprovalLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowApprovalLog
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'task',
            'approver_type', 'approver_id', 'decision', 'comments', 'created_at',
        ]
        read_only_fields = fields


class WorkflowVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowVersion
        fields = [
            'id', 'tenant_id', 'workflow_id', 'version_number', 'status',
            'created_by', 'created_at', 'published_at', 'notes', 'metadata',
        ]
        read_only_fields = ['id', 'created_at', 'published_at']


class WorkflowDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDraft
        fields = [
            'id', 'tenant_id', 'workflow_id', 'version',
            'name', 'description', 'config_snapshot', 'builder_mode',
            'created_by', 'created_at', 'updated_at', 'status',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkflowVersionChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowVersionChangeLog
        fields = [
            'id', 'tenant_id', 'workflow_id', 'version',
            'change_type', 'changed_by', 'change_summary', 'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowVersionComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowVersionComparison
        fields = [
            'id', 'tenant_id', 'workflow_id', 'from_version',
            'to_version', 'comparison_result', 'created_at',
        ]
        read_only_fields = fields


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    rating_average = serializers.FloatField(read_only=True)
    usage_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = WorkflowTemplate
        fields = [
            'id', 'tenant_id',
            'name', 'description', 'category', 'template_type',
            'visibility', 'created_by', 'created_at', 'updated_at',
            'is_active', 'metadata',
            'rating_average', 'usage_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'rating_average', 'usage_count']


class WorkflowTemplateVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTemplateVersion
        fields = [
            'id', 'tenant_id', 'template', 'version_number',
            'config_snapshot', 'created_by', 'created_at', 'is_active',
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowTemplateUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTemplateUsage
        fields = [
            'id', 'tenant_id', 'template', 'workflow_id',
            'used_by', 'created_at',
        ]
        read_only_fields = fields


class WorkflowTemplateRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTemplateRating
        fields = [
            'id', 'tenant_id', 'template', 'rating', 'review',
            'created_by', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowBuilderNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowBuilderNode
        fields = [
            'id', 'tenant_id', 'workflow_id', 'node_type', 'node_name',
            'position_x', 'position_y', 'config', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkflowBuilderConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowBuilderConnection
        fields = [
            'id', 'tenant_id', 'workflow_id', 'source_node_id', 'target_node_id',
            'condition_label', 'connection_type', 'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkflowBuilderLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowBuilderLayout
        fields = [
            'id', 'tenant_id', 'workflow_id', 'canvas_config', 'zoom_level',
            'viewport', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkflowExecutionTimelineEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowExecutionTimelineEntry
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'entry_type', 'entry_label', 'entry_description',
            'actor_type', 'actor_id', 'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowExecutionTraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowExecutionTrace
        fields = [
            'id', 'tenant_id', 'workflow_instance',
            'trace_key', 'trace_type', 'source_module',
            'source_id', 'trace_message', 'severity',
            'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowObservabilitySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowObservabilitySnapshot
        fields = [
            'id', 'tenant_id', 'workflow_instance',
            'current_stage_id', 'current_status', 'wait_reason',
            'active_actor_type', 'active_actor_id',
            'pending_task_count', 'pending_notification_count',
            'has_failure', 'has_sla_risk',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class WorkflowExecutionMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowExecutionMetric
        fields = [
            'id', 'tenant_id', 'workflow_instance',
            'metric_name', 'metric_value', 'metric_type',
            'recorded_at', 'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowMetricSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowMetricSnapshot
        fields = [
            'id', 'tenant_id', 'workflow_id', 'snapshot_date',
            'total_instances', 'completed_instances', 'failed_instances', 'in_progress_instances',
            'average_completion_time_seconds', 'average_wait_time_seconds',
            'average_stage_count', 'average_retry_count',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowStageMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStageMetric
        fields = [
            'id', 'tenant_id', 'workflow_id', 'stage_id', 'metric_date',
            'total_entries', 'completed_entries', 'failed_entries',
            'average_time_in_stage_seconds', 'average_wait_time_seconds',
            'average_retry_count', 'sla_breach_count',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowFailureMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowFailureMetric
        fields = [
            'id', 'tenant_id', 'workflow_id', 'stage_id', 'metric_date',
            'failure_type', 'failure_count', 'recovered_count',
            'permanent_failure_count', 'average_recovery_time_seconds',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowActionMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowActionMetric
        fields = [
            'id', 'tenant_id', 'workflow_id', 'stage_id', 'action_type', 'metric_date',
            'execution_count', 'success_count', 'failure_count', 'average_duration_seconds',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowAutomationImpactMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAutomationImpactMetric
        fields = [
            'id', 'tenant_id', 'workflow_id', 'metric_date',
            'tasks_automated_count', 'approvals_automated_count',
            'notifications_sent_count', 'manual_steps_saved_count',
            'estimated_time_saved_minutes', 'estimated_cost_saved',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowRecoveryCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRecoveryCase
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution', 'action_execution_log',
            'recovery_type', 'failure_type', 'error_message', 'error_code',
            'status', 'retry_strategy', 'retry_limit', 'retry_count',
            'next_retry_at', 'resolved_at', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowRetryAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRetryAttempt
        fields = [
            'id', 'tenant_id', 'recovery_case', 'attempt_number',
            'started_at', 'completed_at', 'status', 'error_message',
            'result_summary', 'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowRecoveryActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRecoveryActionLog
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'recovery_case',
            'action_type', 'action_taken_by', 'action_summary', 'created_at', 'metadata',
        ]
        read_only_fields = fields


class WorkflowRecoveryPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRecoveryPolicy
        fields = [
            'id', 'tenant_id', 'workflow_id', 'stage_id', 'action_type',
            'failure_type', 'retry_strategy', 'retry_limit', 'retry_delay_seconds',
            'escalate_after_failures', 'requires_manual_review', 'is_active', 'created_at', 'metadata',
        ]
        read_only_fields = ['id', 'created_at']


# ------------------------------------------------------------------ #
# Trigger Registry                                                      #
# ------------------------------------------------------------------ #

class WorkflowTriggerRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowEventDefinition
        fields = [
            'id', 'event_key', 'event_name', 'module_scope',
            'description', 'payload_schema', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ------------------------------------------------------------------ #
# Trigger Mapping                                                       #
# ------------------------------------------------------------------ #

class WorkflowTriggerMappingSerializer(serializers.ModelSerializer):
    event_key   = serializers.CharField(source='event_definition.event_key', read_only=True)
    event_name  = serializers.CharField(source='event_definition.event_name', read_only=True)
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)

    class Meta:
        model = WorkflowEventSubscription
        fields = [
            'id', 'tenant_id', 'workflow', 'workflow_name',
            'event_definition', 'event_key', 'event_name',
            'trigger_filters', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'event_key', 'event_name', 'workflow_name']


class WorkflowTriggerMappingWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowEventSubscription
        fields = ['workflow', 'event_definition', 'trigger_filters', 'is_active', 'tenant_id']


# ------------------------------------------------------------------ #
# Event Logs                                                            #
# ------------------------------------------------------------------ #

class WorkflowEventLogSerializer(serializers.ModelSerializer):
    trace_count = serializers.IntegerField(source='debug_traces.count', read_only=True)

    class Meta:
        model = WorkflowEventLog
        fields = [
            'id', 'tenant_id', 'event_key', 'entity_type', 'entity_id',
            'payload', 'source_module', 'status', 'created_at', 'trace_count',
        ]
        read_only_fields = fields


class WorkflowEventDebugTraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowEventDebugTrace
        fields = [
            'id', 'tenant_id', 'event_log', 'workflow',
            'decision', 'reason', 'trace_payload', 'created_at',
        ]
        read_only_fields = fields


# ------------------------------------------------------------------ #
# Action input serializers                                              #
# ------------------------------------------------------------------ #

class TestEmitSerializer(serializers.Serializer):
    tenant_id   = serializers.UUIDField()
    event_key   = serializers.CharField(max_length=128)
    entity_type = serializers.CharField(max_length=64)
    entity_id   = serializers.UUIDField()
    payload     = serializers.JSONField(default=dict)
    source_module = serializers.CharField(max_length=64, default='test')


class CompanyExternalCallbackSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField()
    callback_reference = serializers.CharField(max_length=255)
    workflow_instance_id = serializers.UUIDField(required=False, allow_null=True)
    wait_state_id = serializers.UUIDField(required=False, allow_null=True)
    entity_type = serializers.CharField(max_length=64, required=False, allow_blank=True)
    entity_id = serializers.UUIDField(required=False, allow_null=True)
    actor_type = serializers.CharField(max_length=64, required=False, default='external')
    actor_id = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    payload = serializers.JSONField(required=False, default=dict)

    def validate(self, attrs):
        workflow_instance_id = attrs.get('workflow_instance_id')
        wait_state_id = attrs.get('wait_state_id')
        entity_type = str(attrs.get('entity_type') or '').strip()
        entity_id = attrs.get('entity_id')

        has_scope = any(
            [
                workflow_instance_id is not None,
                wait_state_id is not None,
                entity_type and entity_id is not None,
            ]
        )
        if not has_scope:
            raise serializers.ValidationError(
                "Provide one scope: `workflow_instance_id`, `wait_state_id`, or both `entity_type` and `entity_id`."
            )
        if (entity_type and entity_id is None) or (entity_id is not None and not entity_type):
            raise serializers.ValidationError("`entity_type` and `entity_id` must be provided together.")
        return attrs


class CompanyCandidateInterviewConfirmSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    callback_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    workflow_instance_id = serializers.UUIDField(required=False, allow_null=True)
    wait_state_id = serializers.UUIDField(required=False, allow_null=True)
    interview_id = serializers.UUIDField()
    response = serializers.ChoiceField(choices=['accepted', 'declined', 'reschedule-request'])
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    actor_type = serializers.CharField(max_length=64, required=False, default='external')
    actor_id = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    payload = serializers.JSONField(required=False, default=dict)


class CompanyCandidateOfferResponseSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    callback_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    workflow_instance_id = serializers.UUIDField(required=False, allow_null=True)
    wait_state_id = serializers.UUIDField(required=False, allow_null=True)
    offer_id = serializers.UUIDField()
    response = serializers.ChoiceField(choices=['accepted', 'rejected', 'counter'])
    counter_salary = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    actor_type = serializers.CharField(max_length=64, required=False, default='external')
    actor_id = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    payload = serializers.JSONField(required=False, default=dict)


class CompanyCandidateDocumentUploadedSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    callback_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    workflow_instance_id = serializers.UUIDField(required=False, allow_null=True)
    wait_state_id = serializers.UUIDField(required=False, allow_null=True)
    onboarding_id = serializers.UUIDField()
    document_type = serializers.CharField(max_length=100)
    document_status = serializers.CharField(max_length=64)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    actor_type = serializers.CharField(max_length=64, required=False, default='external')
    actor_id = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    payload = serializers.JSONField(required=False, default=dict)


class CompanyHRMSHandoffSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    callback_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    workflow_instance_id = serializers.UUIDField(required=False, allow_null=True)
    wait_state_id = serializers.UUIDField(required=False, allow_null=True)
    onboarding_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=['acknowledged', 'rejected'])
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    actor_type = serializers.CharField(max_length=64, required=False, default='external')
    actor_id = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    payload = serializers.JSONField(required=False, default=dict)


class ResumeInstanceSerializer(serializers.Serializer):
    triggered_by = serializers.ChoiceField(
        choices=['system', 'user', 'event', 'automation'], default='user'
    )
    actor_id = serializers.UUIDField(required=False, allow_null=True)
    context  = serializers.JSONField(required=False, default=dict)


class SkipStageSerializer(serializers.Serializer):
    stage_id     = serializers.UUIDField(required=False, allow_null=True,
                                          help_text="Defaults to current_stage_id")
    reason       = serializers.CharField(max_length=255, default='Skipped manually')
    triggered_by = serializers.ChoiceField(
        choices=['system', 'user', 'event', 'automation'], default='user'
    )
    actor_id = serializers.UUIDField(required=False, allow_null=True)


class FailInstanceSerializer(serializers.Serializer):
    reason       = serializers.CharField(max_length=255, default='Failed manually')
    triggered_by = serializers.ChoiceField(
        choices=['system', 'user', 'event', 'automation'], default='user'
    )
    actor_id = serializers.UUIDField(required=False, allow_null=True)


class WorkflowNotificationTestSendSerializer(serializers.Serializer):
    workflow_instance_id = serializers.UUIDField()
    stage_execution_id = serializers.UUIDField(required=False, allow_null=True)
    trigger_type = serializers.ChoiceField(choices=[choice[0] for choice in WorkflowNotificationRule.TRIGGER_TYPES])
    payload = serializers.JSONField(required=False, default=dict)


class WorkflowConditionGroupTestEvaluateSerializer(serializers.Serializer):
    workflow_instance_id = serializers.UUIDField()
    stage_execution_id = serializers.UUIDField(required=False, allow_null=True)
    context = serializers.JSONField(required=False, default=dict)


class WorkflowActionTestRunSerializer(serializers.Serializer):
    workflow_instance_id = serializers.UUIDField()
    stage_execution_id = serializers.UUIDField(required=False, allow_null=True)
    context = serializers.JSONField(required=False, default=dict)


class WorkflowHumanTaskCompleteSerializer(serializers.Serializer):
    actor_type = serializers.CharField(required=False, default='user')
    actor_id = serializers.UUIDField(required=False, allow_null=True)
    comments = serializers.CharField(required=False, allow_blank=True, default='')
    context = serializers.JSONField(required=False, default=dict)


class WorkflowDraftCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, default='')
    description = serializers.CharField(required=False, allow_blank=True, default='')
    builder_mode = serializers.ChoiceField(choices=['guided', 'advanced'], default='guided')
    created_by = serializers.UUIDField(required=False, allow_null=True)


class WorkflowDraftSaveSerializer(serializers.Serializer):
    draft_id = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    builder_mode = serializers.ChoiceField(choices=['guided', 'advanced'], required=False)
    config_snapshot = serializers.JSONField(required=False)
    ready_for_publish = serializers.BooleanField(required=False, default=False)
    changed_by = serializers.UUIDField(required=False, allow_null=True)


class WorkflowDraftPublishSerializer(serializers.Serializer):
    draft_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    changed_by = serializers.UUIDField(required=False, allow_null=True)


class WorkflowVersionRollbackSerializer(serializers.Serializer):
    changed_by = serializers.UUIDField(required=False, allow_null=True)


class WorkflowVersionCloneSerializer(serializers.Serializer):
    changed_by = serializers.UUIDField(required=False, allow_null=True)


class WorkflowDraftDiscardSerializer(serializers.Serializer):
    draft_id = serializers.UUIDField(required=False, allow_null=True)
    changed_by = serializers.UUIDField(required=False, allow_null=True)


class WorkflowTemplateCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    category = serializers.ChoiceField(choices=[c[0] for c in WorkflowTemplate.CATEGORIES], default='custom')
    template_type = serializers.ChoiceField(choices=[c[0] for c in WorkflowTemplate.TEMPLATE_TYPES], default='custom')
    visibility = serializers.ChoiceField(choices=[c[0] for c in WorkflowTemplate.VISIBILITY_TYPES], default='private')
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    created_by = serializers.UUIDField(required=False, allow_null=True)
    config_snapshot = serializers.JSONField(required=False, default=dict)
    metadata = serializers.JSONField(required=False, default=dict)


class WorkflowTemplateCloneSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    created_by = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True, default='')


class WorkflowTemplateApplySerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField()
    workflow_name = serializers.CharField(required=False, allow_blank=True, default='')
    workflow_description = serializers.CharField(required=False, allow_blank=True, default='')
    trigger_event = serializers.CharField(required=False, allow_blank=True, default='manual')
    used_by = serializers.UUIDField(required=False, allow_null=True)


class WorkflowTemplatePublishSerializer(serializers.Serializer):
    visibility = serializers.ChoiceField(
        choices=[c[0] for c in WorkflowTemplate.VISIBILITY_TYPES],
        required=False,
    )


class WorkflowTemplateImportSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    created_by = serializers.UUIDField(required=False, allow_null=True)
    payload = serializers.JSONField()


class WorkflowTemplateRateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    review = serializers.CharField(required=False, allow_blank=True, default='')
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    created_by = serializers.UUIDField(required=False, allow_null=True)


class WorkflowBuilderGetSerializer(serializers.Serializer):
    workflow_id = serializers.UUIDField()


class WorkflowBuilderNodeCreateSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    workflow_id = serializers.UUIDField()
    node_type = serializers.ChoiceField(choices=[c[0] for c in WorkflowBuilderNode.NODE_TYPES])
    node_name = serializers.CharField(max_length=255)
    position_x = serializers.IntegerField(required=False, default=0)
    position_y = serializers.IntegerField(required=False, default=0)
    config = serializers.JSONField(required=False, default=dict)
    created_by = serializers.UUIDField(required=False, allow_null=True)


class WorkflowBuilderNodeUpdateSerializer(serializers.Serializer):
    node_name = serializers.CharField(max_length=255, required=False)
    position_x = serializers.IntegerField(required=False)
    position_y = serializers.IntegerField(required=False)
    config = serializers.JSONField(required=False)
    is_active = serializers.BooleanField(required=False)


class WorkflowBuilderConnectionCreateSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    workflow_id = serializers.UUIDField()
    source_node_id = serializers.UUIDField()
    target_node_id = serializers.UUIDField()
    condition_label = serializers.CharField(required=False, allow_blank=True, default='')
    connection_type = serializers.ChoiceField(choices=[c[0] for c in WorkflowBuilderConnection.CONNECTION_TYPES], default='default')
    metadata = serializers.JSONField(required=False, default=dict)
    created_by = serializers.UUIDField(required=False, allow_null=True)


class WorkflowBuilderValidateSerializer(serializers.Serializer):
    workflow_id = serializers.UUIDField()


class WorkflowBuilderSaveSerializer(serializers.Serializer):
    workflow_id = serializers.UUIDField()
    payload = serializers.JSONField(required=False, default=dict)
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    created_by = serializers.UUIDField(required=False, allow_null=True)
    auto_layout = serializers.BooleanField(required=False, default=False)


class WorkflowRecoveryManualActionSerializer(serializers.Serializer):
    action_taken_by = serializers.CharField(required=False, default='user')


class WorkflowRecoveryPolicyCreateSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    workflow_id = serializers.UUIDField()
    stage_id = serializers.UUIDField(required=False, allow_null=True)
    action_type = serializers.CharField(required=False, allow_blank=True, default='')
    failure_type = serializers.ChoiceField(choices=[c[0] for c in WorkflowRecoveryCase.FAILURE_TYPES], default='unknown')
    retry_strategy = serializers.ChoiceField(choices=[c[0] for c in WorkflowRecoveryCase.RETRY_STRATEGIES], default='manual_only')
    retry_limit = serializers.IntegerField(required=False, min_value=0, default=0)
    retry_delay_seconds = serializers.IntegerField(required=False, min_value=0, default=0)
    escalate_after_failures = serializers.IntegerField(required=False, min_value=0, default=0)
    requires_manual_review = serializers.BooleanField(required=False, default=False)
    is_active = serializers.BooleanField(required=False, default=True)
    metadata = serializers.JSONField(required=False, default=dict)


# ------------------------------------------------------------------ #
# Cross-entity routing                                                  #
# ------------------------------------------------------------------ #

class WorkflowEntityRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowEntityRoute
        fields = [
            'id', 'tenant_id', 'workflow_instance',
            'from_entity_type', 'from_entity_id',
            'to_entity_type', 'to_entity_id',
            'route_type', 'route_reason', 'status',
            'stage_id', 'completed_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class WorkflowActorAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowActorAssignment
        fields = [
            'id', 'tenant_id', 'workflow_instance',
            'stage_id', 'actor_type', 'actor_id',
            'assignment_type', 'assigned_at', 'status', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'assigned_at', 'created_at', 'updated_at']


class WorkflowHandoffCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowHandoffCheckpoint
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'stage_execution',
            'handoff_from', 'handoff_to', 'handoff_type',
            'payload', 'expected_response_event',
            'status', 'responded_at', 'response_payload',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'responded_at', 'created_at', 'updated_at']


class WorkflowRoutingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRoutingRule
        fields = [
            'id', 'tenant_id', 'workflow_id', 'stage_id',
            'condition_config',
            'route_to_entity_type', 'route_to_actor_type', 'route_config',
            'priority', 'label', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkflowRouteTimelineLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRouteTimelineLog
        fields = [
            'id', 'tenant_id', 'workflow_instance', 'route',
            'action', 'from_actor', 'to_actor', 'reason',
            'created_at',
        ]
        read_only_fields = fields


# ------------------------------------------------------------------ #
# Routing action input serializers                                      #
# ------------------------------------------------------------------ #

class CompleteHandoffSerializer(serializers.Serializer):
    response_payload = serializers.JSONField(required=False, default=dict)
    triggered_by     = serializers.ChoiceField(
        choices=['system', 'user', 'event', 'automation'], default='system'
    )
    actor_id = serializers.UUIDField(required=False, allow_null=True)


class AcknowledgeHandoffSerializer(serializers.Serializer):
    response_payload = serializers.JSONField(required=False, default=dict)


class AssignActorSerializer(serializers.Serializer):
    stage_id        = serializers.UUIDField()
    actor_type      = serializers.ChoiceField(choices=[
        'recruiter', 'hiring_manager', 'hr', 'agency_manager',
        'agency_recruiter', 'interviewer', 'candidate', 'system',
    ])
    actor_id        = serializers.UUIDField(required=False, allow_null=True)
    assignment_type = serializers.ChoiceField(
        choices=['responsible', 'reviewer', 'approver', 'scheduler', 'coordinator', 'observer'],
        default='responsible',
    )
    notes = serializers.CharField(max_length=512, required=False, default='')


class OrchestratorRunSerializer(serializers.Serializer):
    context = serializers.JSONField(required=False, default=dict)
    source_type = serializers.ChoiceField(
        choices=['workflow', 'event', 'stage', 'actor', 'routing', 'system'],
        default='system',
    )


class OrchestratorResumeSerializer(serializers.Serializer):
    resume_event = serializers.CharField(max_length=128, required=False, allow_blank=True, default='')
    context = serializers.JSONField(required=False, default=dict)


class OrchestratorFailSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=512, default='Failed by orchestrator action')
