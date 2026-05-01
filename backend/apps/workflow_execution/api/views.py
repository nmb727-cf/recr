from rest_framework import viewsets, status, response, mixins
from rest_framework.decorators import action
from rest_framework.views import APIView
import uuid

from apps.workflow_execution.models import (
    WorkflowInstance,
    WorkflowExecutionTimeline,
    WorkflowStageExecution,
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
from apps.workflow_execution.api.serializers import (
    WorkflowInstanceSerializer,
    WorkflowInstanceSummarySerializer,
    WorkflowExecutionTimelineSerializer,
    WorkflowStageExecutionSerializer,
    WorkflowStageTransitionSerializer,
    WorkflowWaitStateSerializer,
    WorkflowTransitionLogSerializer,
    WorkflowFailureLogSerializer,
    WorkflowTimelineSerializer,
    WorkflowExecutionContextSerializer,
    WorkflowExecutionDecisionSerializer,
    WorkflowOrchestratorLogSerializer,
    WorkflowStageSLASerializer,
    WorkflowSLATrackerSerializer,
    WorkflowSLAEventSerializer,
    WorkflowNotificationRuleSerializer,
    WorkflowNotificationLogSerializer,
    WorkflowNotificationQueueSerializer,
    WorkflowScheduledTaskSerializer,
    WorkflowSchedulerLogSerializer,
    WorkflowConditionRuleSerializer,
    WorkflowConditionGroupSerializer,
    WorkflowConditionEvaluationLogSerializer,
    WorkflowActionDefinitionSerializer,
    WorkflowActionExecutionLogSerializer,
    WorkflowActionDependencySerializer,
    WorkflowHumanTaskSerializer,
    WorkflowApprovalRuleSerializer,
    WorkflowApprovalLogSerializer,
    WorkflowVersionSerializer,
    WorkflowDraftSerializer,
    WorkflowVersionChangeLogSerializer,
    WorkflowVersionComparisonSerializer,
    WorkflowTemplateSerializer,
    WorkflowTemplateVersionSerializer,
    WorkflowTemplateUsageSerializer,
    WorkflowTemplateRatingSerializer,
    WorkflowTriggerRegistrySerializer,
    WorkflowTriggerMappingSerializer,
    WorkflowTriggerMappingWriteSerializer,
    WorkflowEventLogSerializer,
    WorkflowEventDebugTraceSerializer,
    TestEmitSerializer,
    CompanyExternalCallbackSerializer,
    CompanyCandidateInterviewConfirmSerializer,
    CompanyCandidateOfferResponseSerializer,
    CompanyCandidateDocumentUploadedSerializer,
    CompanyHRMSHandoffSerializer,
    ResumeInstanceSerializer,
    SkipStageSerializer,
    FailInstanceSerializer,
    WorkflowEntityRouteSerializer,
    WorkflowActorAssignmentSerializer,
    WorkflowHandoffCheckpointSerializer,
    WorkflowRoutingRuleSerializer,
    WorkflowRouteTimelineLogSerializer,
    CompleteHandoffSerializer,
    AcknowledgeHandoffSerializer,
    AssignActorSerializer,
    OrchestratorRunSerializer,
    OrchestratorResumeSerializer,
    OrchestratorFailSerializer,
    WorkflowNotificationTestSendSerializer,
    WorkflowConditionGroupTestEvaluateSerializer,
    WorkflowActionTestRunSerializer,
    WorkflowHumanTaskCompleteSerializer,
    WorkflowDraftCreateSerializer,
    WorkflowDraftSaveSerializer,
    WorkflowDraftPublishSerializer,
    WorkflowVersionRollbackSerializer,
    WorkflowVersionCloneSerializer,
    WorkflowDraftDiscardSerializer,
    WorkflowTemplateCreateSerializer,
    WorkflowTemplateCloneSerializer,
    WorkflowTemplateApplySerializer,
    WorkflowTemplatePublishSerializer,
    WorkflowTemplateImportSerializer,
    WorkflowTemplateRateSerializer,
    WorkflowBuilderNodeSerializer,
    WorkflowBuilderConnectionSerializer,
    WorkflowBuilderLayoutSerializer,
    WorkflowBuilderNodeCreateSerializer,
    WorkflowBuilderNodeUpdateSerializer,
    WorkflowBuilderConnectionCreateSerializer,
    WorkflowBuilderValidateSerializer,
    WorkflowBuilderSaveSerializer,
    WorkflowExecutionTimelineEntrySerializer,
    WorkflowExecutionTraceSerializer,
    WorkflowObservabilitySnapshotSerializer,
    WorkflowExecutionMetricSerializer,
    WorkflowRecoveryCaseSerializer,
    WorkflowRetryAttemptSerializer,
    WorkflowRecoveryActionLogSerializer,
    WorkflowRecoveryPolicySerializer,
    WorkflowRecoveryManualActionSerializer,
    WorkflowRecoveryPolicyCreateSerializer,
    WorkflowMetricSnapshotSerializer,
    WorkflowStageMetricSerializer,
    WorkflowFailureMetricSerializer,
    WorkflowActionMetricSerializer,
    WorkflowAutomationImpactMetricSerializer,
)
from apps.interviews.models import Interview
from apps.documents.models import OfferLetter
from apps.pipeline.models import Application, ApplicationStageHistory
from apps.hdc.models import JoiningCase
from apps.hdc.services import HDCOperationalService
from apps.core import events
from apps.workflow_execution.services.workflow_execution_engine import WorkflowExecutionEngine
from apps.workflow_execution.services.workflow_event_listener import WorkflowEventListener
from apps.workflow_execution.services.workflow_execution_orchestrator import WorkflowExecutionOrchestrator
from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.workflow_execution.services.workflow_cross_entity_routing_engine import WorkflowCrossEntityRoutingEngine
from apps.workflow_execution.services.workflow_sla_engine import WorkflowSLAEngine
from apps.workflow_execution.services.workflow_notification_engine import WorkflowNotificationEngine
from apps.workflow_execution.services.workflow_scheduler_engine import WorkflowSchedulerEngine
from apps.workflow_execution.services.workflow_conditional_logic_engine import WorkflowConditionalLogicEngine
from apps.workflow_execution.services.workflow_action_handlers_engine import WorkflowActionHandlersEngine
from apps.workflow_execution.services.workflow_human_task_engine import WorkflowHumanTaskEngine
from apps.workflow_execution.services.workflow_versioning_engine import WorkflowVersioningEngine
from apps.workflow_execution.services.workflow_template_engine import WorkflowTemplateEngine
from apps.workflow_execution.services.workflow_visual_builder_engine import WorkflowVisualBuilderEngine
from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine
from apps.workflow_execution.services.workflow_failure_recovery_engine import WorkflowFailureRecoveryEngine
from apps.workflow_execution.services.workflow_metrics_analytics_engine import WorkflowMetricsAnalyticsEngine
from apps.workflow_execution.models.execution import WAIT_REASON_RESUME_EVENTS
from django.db.models import Count, Avg, Q
from django.utils import timezone


# ------------------------------------------------------------------ #
# Workflow Instances                                                    #
# ------------------------------------------------------------------ #

class WorkflowInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/v1/workflow/instances/
    GET  /api/v1/workflow/instances/{id}/
    GET  /api/v1/workflow/instances/{id}/timeline/
    GET  /api/v1/workflow/instances/{id}/wait-states/
    GET  /api/v1/workflow/instances/{id}/transition-logs/
    POST /api/v1/workflow/instances/start/
    POST /api/v1/workflow/instances/{id}/resume/
    POST /api/v1/workflow/instances/{id}/skip/
    POST /api/v1/workflow/instances/{id}/fail/
    POST /api/v1/workflow/instances/{id}/pause/
    """
    queryset = WorkflowInstance.objects.all()
    serializer_class = WorkflowInstanceSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return WorkflowInstanceSummarySerializer
        return WorkflowInstanceSerializer

    def get_queryset(self):
        qs = self.queryset
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        workflow_id = self.request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type=entity_type)
        entity_id = self.request.query_params.get('entity_id')
        if entity_id:
            qs = qs.filter(entity_id=entity_id)
        return qs

    # --- read sub-resources ---

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """GET /api/v1/workflow/instances/{id}/timeline/"""
        instance = self.get_object()
        unified_events = instance.unified_timeline.all()
        if unified_events.exists():
            return response.Response(WorkflowTimelineSerializer(unified_events, many=True).data)
        events = instance.timeline_events.all()
        return response.Response(WorkflowExecutionTimelineSerializer(events, many=True).data)

    @action(detail=True, methods=['get'])
    def stages(self, request, pk=None):
        """GET /api/v1/workflow/instances/{id}/stages/"""
        instance = self.get_object()
        executions = instance.stage_executions.all().order_by('started_at')
        return response.Response(WorkflowStageExecutionSerializer(executions, many=True).data)

    @action(detail=True, methods=['get'], url_path='wait-states')
    def wait_states(self, request, pk=None):
        """GET /api/v1/workflow/instances/{id}/wait-states/"""
        instance = self.get_object()
        states = instance.wait_states.all()
        return response.Response(WorkflowWaitStateSerializer(states, many=True).data)

    @action(detail=True, methods=['get'], url_path='sla')
    def sla(self, request, pk=None):
        """GET /api/v1/workflow-instances/{id}/sla/"""
        instance = self.get_object()
        trackers = instance.sla_trackers.all()
        return response.Response(WorkflowSLATrackerSerializer(trackers, many=True).data)

    @action(detail=True, methods=['get'], url_path='transition-logs')
    def transition_logs(self, request, pk=None):
        """GET /api/v1/workflow/instances/{id}/transition-logs/"""
        instance = self.get_object()
        logs = instance.transition_logs.all()
        return response.Response(WorkflowTransitionLogSerializer(logs, many=True).data)

    @action(detail=True, methods=['get'], url_path='failures')
    def failures(self, request, pk=None):
        """GET /api/v1/workflow/instances/{id}/failures/"""
        instance = self.get_object()
        failures = instance.failure_logs.all()
        return response.Response(WorkflowFailureLogSerializer(failures, many=True).data)

    @action(detail=True, methods=['get'], url_path='notifications')
    def notifications(self, request, pk=None):
        """GET /api/v1/workflow-instances/{id}/notifications/"""
        instance = self.get_object()
        logs = instance.notification_logs.all()
        return response.Response(WorkflowNotificationLogSerializer(logs, many=True).data)

    @action(detail=True, methods=['get'], url_path='scheduled-tasks')
    def scheduled_tasks(self, request, pk=None):
        """GET /api/v1/workflow-instances/{id}/scheduled-tasks/"""
        instance = self.get_object()
        tasks = instance.scheduled_tasks.all()
        return response.Response(WorkflowScheduledTaskSerializer(tasks, many=True).data)

    @action(detail=True, methods=['get'], url_path='condition-logs')
    def condition_logs(self, request, pk=None):
        """GET /api/v1/workflow-instances/{id}/condition-logs/"""
        instance = self.get_object()
        logs = instance.condition_evaluation_logs.all()
        return response.Response(WorkflowConditionEvaluationLogSerializer(logs, many=True).data)

    @action(detail=True, methods=['get'], url_path='action-logs')
    def action_logs(self, request, pk=None):
        """GET /api/v1/workflow-instances/{id}/action-logs/"""
        instance = self.get_object()
        logs = instance.action_execution_logs.all()
        return response.Response(WorkflowActionExecutionLogSerializer(logs, many=True).data)

    @action(detail=True, methods=['get'], url_path='human-tasks')
    def human_tasks(self, request, pk=None):
        """GET /api/v1/workflow-instances/{id}/human-tasks/"""
        instance = self.get_object()
        tasks = instance.human_tasks.all()
        return response.Response(WorkflowHumanTaskSerializer(tasks, many=True).data)

    @action(detail=True, methods=['get'], url_path='recovery')
    def recovery(self, request, pk=None):
        """GET /api/v1/workflow-instances/{id}/recovery/"""
        instance = self.get_object()
        cases = instance.recovery_cases.all().order_by('-created_at')
        return response.Response(WorkflowRecoveryCaseSerializer(cases, many=True).data)

    @action(detail=True, methods=['get'])
    def routes(self, request, pk=None):
        """GET /api/v1/workflow/instances/{id}/routes/"""
        instance = self.get_object()
        routes = instance.entity_routes.all()
        return response.Response(WorkflowEntityRouteSerializer(routes, many=True).data)

    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """GET /api/v1/workflow/instances/{id}/assignments/"""
        instance = self.get_object()
        assignments = instance.actor_assignments.filter(status='active')
        return response.Response(WorkflowActorAssignmentSerializer(assignments, many=True).data)

    @action(detail=True, methods=['get'], url_path='actor-ownership')
    def actor_ownership(self, request, pk=None):
        """GET /api/v1/workflow/instances/{id}/actor-ownership/"""
        instance = self.get_object()
        assignments = instance.actor_assignments.filter(status='active')
        return response.Response(WorkflowActorAssignmentSerializer(assignments, many=True).data)

    @action(detail=True, methods=['get'])
    def handoffs(self, request, pk=None):
        """GET /api/v1/workflow/instances/{id}/handoffs/"""
        instance = self.get_object()
        handoffs = instance.handoff_checkpoints.all()
        return response.Response(WorkflowHandoffCheckpointSerializer(handoffs, many=True).data)

    @action(detail=True, methods=['get'], url_path='route-timeline')
    def route_timeline(self, request, pk=None):
        """GET /api/v1/workflow/instances/{id}/route-timeline/"""
        instance = self.get_object()
        logs = instance.route_timeline.all()
        return response.Response(WorkflowRouteTimelineLogSerializer(logs, many=True).data)

    @action(detail=True, methods=['post'], url_path='assign-actor')
    def assign_actor(self, request, pk=None):
        """POST /api/v1/workflow/instances/{id}/assign-actor/"""
        instance = self.get_object()
        ser = AssignActorSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        assignment = WorkflowCrossEntityRoutingEngine.assign_actor_for_stage(
            instance=instance,
            stage_id=data['stage_id'],
            actor_type=data['actor_type'],
            actor_id=data.get('actor_id'),
            assignment_type=data.get('assignment_type', 'responsible'),
            notes=data.get('notes', ''),
        )
        return response.Response(
            WorkflowActorAssignmentSerializer(assignment).data,
            status=status.HTTP_201_CREATED,
        )

    # --- write operations ---

    @action(detail=False, methods=['post'])
    def start(self, request):
        """POST /api/v1/workflow/instances/start/"""
        tenant_id   = request.data.get('tenant_id')
        workflow_id = request.data.get('workflow_id')
        entity_type = request.data.get('entity_type')
        entity_id   = request.data.get('entity_id')
        context     = request.data.get('context', {})

        instance = WorkflowExecutionEngine.start_workflow_instance(
            tenant_id, workflow_id, entity_type, entity_id, context=context
        )
        return response.Response(
            WorkflowInstanceSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """POST /api/v1/workflow/instances/{id}/resume/"""
        instance = self.get_object()
        ser = ResumeInstanceSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        updated = WorkflowStageEngine.resume_instance(
            instance.id,
            triggered_by=data.get('triggered_by', 'user'),
            actor_id=data.get('actor_id'),
            context=data.get('context'),
        )
        updated.refresh_from_db()
        return response.Response({'status': updated.status, 'wait_reason': updated.wait_reason})

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """POST /api/v1/workflow/instances/{id}/retry/"""
        instance = self.get_object()
        retried_stage = WorkflowInstanceTracker.retry_stage(
            instance,
            triggered_by='manual',
            actor_id=request.data.get('actor_id'),
            metadata=request.data.get('context', {}),
        )
        instance.refresh_from_db()
        if retried_stage is None:
            return response.Response(
                {'error': 'No stage execution available to retry.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return response.Response(
            {
                'status': instance.status,
                'retried_stage_execution_id': str(retried_stage.id),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        """POST /api/v1/workflow/instances/{id}/skip/"""
        instance = self.get_object()
        ser = SkipStageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        stage_id = data.get('stage_id') or instance.current_stage_id
        if not stage_id:
            return response.Response(
                {'error': 'No current stage to skip.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        WorkflowStageEngine.skip_stage(
            instance,
            stage_id=stage_id,
            reason=data.get('reason', 'Skipped manually'),
            triggered_by=data.get('triggered_by', 'user'),
            actor_id=data.get('actor_id'),
        )
        instance.refresh_from_db()
        return response.Response({'status': instance.status, 'current_stage_id': str(instance.current_stage_id or '')})

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """POST /api/v1/workflow/instances/{id}/fail/"""
        instance = self.get_object()
        ser = FailInstanceSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        WorkflowStageEngine.fail_stage(
            instance,
            reason=data.get('reason', 'Failed manually'),
            triggered_by=data.get('triggered_by', 'user'),
            actor_id=data.get('actor_id'),
        )
        instance.refresh_from_db()
        return response.Response({'status': instance.status})

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """POST /api/v1/workflow/instances/{id}/pause/"""
        instance = self.get_object()
        instance.status = 'paused'
        instance.save(update_fields=['status', 'updated_at'])
        return response.Response({'status': 'paused'})

    # Kept for backwards compatibility
    @action(detail=True, methods=['post'])
    def advance(self, request, pk=None):
        instance = self.get_object()
        WorkflowExecutionEngine.resume_workflow(instance.id)
        instance.refresh_from_db()
        return response.Response({'status': instance.status})


# ------------------------------------------------------------------ #
# Stage Transitions  (CRUD)                                            #
# ------------------------------------------------------------------ #

class WorkflowStageTransitionViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET    /api/v1/workflow/stage-transitions/
    POST   /api/v1/workflow/stage-transitions/
    GET    /api/v1/workflow/stage-transitions/{id}/
    PUT    /api/v1/workflow/stage-transitions/{id}/
    PATCH  /api/v1/workflow/stage-transitions/{id}/
    DELETE /api/v1/workflow/stage-transitions/{id}/
    """
    queryset = WorkflowStageTransition.objects.all()
    serializer_class = WorkflowStageTransitionSerializer

    def get_queryset(self):
        qs = self.queryset
        workflow_id = self.request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        from_stage_id = self.request.query_params.get('from_stage_id')
        if from_stage_id:
            qs = qs.filter(from_stage_id=from_stage_id)
        return qs


# ------------------------------------------------------------------ #
# Wait States  (read-only global view)                                 #
# ------------------------------------------------------------------ #

class WorkflowWaitStateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/workflow/wait-states/
    GET /api/v1/workflow/wait-states/{id}/
    """
    queryset = WorkflowWaitState.objects.select_related('workflow_instance', 'stage_execution').all()
    serializer_class = WorkflowWaitStateSerializer

    def get_queryset(self):
        qs = self.queryset
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        ws_status = self.request.query_params.get('status')
        if ws_status:
            qs = qs.filter(status=ws_status)
        wait_type = self.request.query_params.get('wait_type')
        if wait_type:
            qs = qs.filter(wait_type=wait_type)
        return qs

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """POST /api/v1/workflow/wait-states/{id}/resume/"""
        ser = ResumeInstanceSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        wait_state = WorkflowStageEngine.resume_wait_state(
            wait_state_id=pk,
            triggered_by=data.get('triggered_by', 'user'),
            actor_id=data.get('actor_id'),
            context=data.get('context'),
        )
        if wait_state is None:
            return response.Response(
                {'error': 'Wait state not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return response.Response(WorkflowWaitStateSerializer(wait_state).data)


# ------------------------------------------------------------------ #
# Transition Logs  (read-only)                                         #
# ------------------------------------------------------------------ #

class WorkflowTransitionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/workflow/transition-logs/
    GET /api/v1/workflow/transition-logs/{id}/
    """
    queryset = WorkflowTransitionLog.objects.select_related('workflow_instance').all()
    serializer_class = WorkflowTransitionLogSerializer

    def get_queryset(self):
        qs = self.queryset
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        instance_id = self.request.query_params.get('workflow_instance_id')
        if instance_id:
            qs = qs.filter(workflow_instance_id=instance_id)
        return qs


class WorkflowFailureLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/workflow/failure-logs/
    GET /api/v1/workflow/failure-logs/{id}/
    """
    queryset = WorkflowFailureLog.objects.select_related('workflow_instance', 'stage_execution').all()
    serializer_class = WorkflowFailureLogSerializer

    def get_queryset(self):
        qs = self.queryset
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        instance_id = self.request.query_params.get('workflow_instance_id')
        if instance_id:
            qs = qs.filter(workflow_instance_id=instance_id)
        return qs


class WorkflowOrchestratorInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/v1/workflow-orchestrator/instances/{id}/context/
    GET  /api/v1/workflow-orchestrator/instances/{id}/decisions/
    GET  /api/v1/workflow-orchestrator/instances/{id}/logs/
    POST /api/v1/workflow-orchestrator/instances/{id}/run/
    POST /api/v1/workflow-orchestrator/instances/{id}/resume/
    POST /api/v1/workflow-orchestrator/instances/{id}/retry/
    POST /api/v1/workflow-orchestrator/instances/{id}/fail/
    """
    queryset = WorkflowInstance.objects.all()
    serializer_class = WorkflowInstanceSerializer

    @action(detail=True, methods=['get'])
    def context(self, request, pk=None):
        instance = self.get_object()
        contexts = instance.execution_contexts.all().order_by('context_key')
        return response.Response(WorkflowExecutionContextSerializer(contexts, many=True).data)

    @action(detail=True, methods=['get'])
    def decisions(self, request, pk=None):
        instance = self.get_object()
        decisions = instance.execution_decisions.all()
        return response.Response(WorkflowExecutionDecisionSerializer(decisions, many=True).data)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        instance = self.get_object()
        logs = instance.orchestrator_logs.all()
        return response.Response(WorkflowOrchestratorLogSerializer(logs, many=True).data)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        ser = OrchestratorRunSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        result = WorkflowExecutionOrchestrator.orchestrate_workflow_instance(
            pk,
            context=data.get('context', {}),
            source_type=data.get('source_type', 'system'),
        )
        return response.Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        ser = OrchestratorResumeSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        result = WorkflowExecutionOrchestrator.orchestrate_workflow_instance(
            pk,
            context=data.get('context', {}),
            resume_event=data.get('resume_event', ''),
            source_type='event',
        )
        return response.Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        instance = self.get_object()
        latest_stage = instance.stage_executions.order_by('-created_at').first()
        retried = WorkflowExecutionOrchestrator.apply_retry(
            instance,
            latest_stage,
            {'reason': 'Retry requested via orchestrator API'},
        )
        instance.refresh_from_db()
        return response.Response(
            {
                'status': instance.status,
                'retried_stage_execution_id': str(retried.id) if retried else None,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        ser = OrchestratorFailSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        instance = self.get_object()
        WorkflowExecutionOrchestrator.fail_workflow_instance(
            instance,
            reason=data.get('reason', 'Failed by orchestrator action'),
        )
        instance.refresh_from_db()
        return response.Response({'status': instance.status}, status=status.HTTP_200_OK)


class WorkflowSLAListView(APIView):
    """GET /api/v1/workflow-sla/"""

    def get(self, request, *args, **kwargs):
        qs = WorkflowSLATracker.objects.select_related('workflow_instance', 'stage_execution', 'stage_sla').all()
        tenant_id = request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        instance_id = request.query_params.get('workflow_instance_id')
        if instance_id:
            qs = qs.filter(workflow_instance_id=instance_id)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return response.Response(WorkflowSLATrackerSerializer(qs, many=True).data)


class WorkflowSLAResolveView(APIView):
    """POST /api/v1/workflow-sla/{id}/resolve/"""

    def post(self, request, pk=None, *args, **kwargs):
        tracker = WorkflowSLATracker.objects.select_related('workflow_instance', 'stage_execution').filter(id=pk).first()
        if tracker is None:
            return response.Response({'error': 'SLA tracker not found.'}, status=status.HTTP_404_NOT_FOUND)
        WorkflowSLAEngine.resolve_sla(tracker.workflow_instance, tracker.stage_execution)
        tracker.refresh_from_db()
        return response.Response(WorkflowSLATrackerSerializer(tracker).data, status=status.HTTP_200_OK)


class WorkflowStageSLAByStageView(APIView):
    """GET /api/v1/workflow-stages/{id}/sla/"""

    def get(self, request, pk=None, *args, **kwargs):
        slas = WorkflowStageSLA.objects.filter(stage_id=pk, is_active=True).order_by('-created_at')
        return response.Response(WorkflowStageSLASerializer(slas, many=True).data, status=status.HTTP_200_OK)


class WorkflowNotificationListView(APIView):
    """GET /api/v1/workflow-notifications/"""

    def get(self, request, *args, **kwargs):
        qs = WorkflowNotificationLog.objects.select_related('workflow_instance', 'stage_execution').all()
        tenant_id = request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        workflow_instance_id = request.query_params.get('workflow_instance_id')
        if workflow_instance_id:
            qs = qs.filter(workflow_instance_id=workflow_instance_id)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        channel = request.query_params.get('channel')
        if channel:
            qs = qs.filter(channel=channel)
        return response.Response(WorkflowNotificationLogSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class WorkflowNotificationDetailView(APIView):
    """GET /api/v1/workflow-notifications/{id}/"""

    def get(self, request, pk=None, *args, **kwargs):
        notification = WorkflowNotificationLog.objects.filter(id=pk).first()
        if not notification:
            return response.Response({'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(WorkflowNotificationLogSerializer(notification).data, status=status.HTTP_200_OK)


class WorkflowNotificationTestSendView(APIView):
    """POST /api/v1/workflow-notifications/test-send/"""

    def post(self, request, *args, **kwargs):
        ser = WorkflowNotificationTestSendSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        instance = WorkflowInstance.objects.filter(id=data['workflow_instance_id']).first()
        if instance is None:
            return response.Response({'error': 'Workflow instance not found.'}, status=status.HTTP_404_NOT_FOUND)
        stage_execution = None
        if data.get('stage_execution_id'):
            stage_execution = WorkflowStageExecution.objects.filter(id=data['stage_execution_id']).first()

        queued = WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=instance,
            trigger_type=data['trigger_type'],
            stage_execution=stage_execution,
            payload=data.get('payload', {}),
        )
        processed = WorkflowNotificationEngine.process_notification_queue(limit=max(1, len(queued)))
        return response.Response(
            {'queued_count': len(queued), 'processed': processed},
            status=status.HTTP_200_OK,
        )


class WorkflowNotificationRetryView(APIView):
    """POST /api/v1/workflow-notifications/{id}/retry/"""

    def post(self, request, pk=None, *args, **kwargs):
        log = WorkflowNotificationLog.objects.select_related('workflow_instance', 'stage_execution').filter(id=pk).first()
        if log is None:
            return response.Response({'error': 'Notification log not found.'}, status=status.HTTP_404_NOT_FOUND)
        queue_item = WorkflowNotificationEngine.queue_notification(
            workflow_instance=log.workflow_instance,
            stage_execution=log.stage_execution,
            recipient_type=log.recipient_type,
            recipient_id=log.recipient_id,
            channel=log.channel,
            template_key=log.template_key,
            payload=log.metadata or {},
        )
        result = WorkflowNotificationEngine.send_notification(queue_item)
        return response.Response(
            {
                'queue_id': str(queue_item.id),
                'result': result,
            },
            status=status.HTTP_200_OK,
        )


class WorkflowSchedulerTaskListView(APIView):
    """GET /api/v1/workflow-scheduler/tasks/"""

    def get(self, request, *args, **kwargs):
        qs = WorkflowScheduledTask.objects.select_related('workflow_instance', 'stage_execution').all()
        tenant_id = request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        workflow_instance_id = request.query_params.get('workflow_instance_id')
        if workflow_instance_id:
            qs = qs.filter(workflow_instance_id=workflow_instance_id)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        task_type = request.query_params.get('task_type')
        if task_type:
            qs = qs.filter(task_type=task_type)
        return response.Response(WorkflowScheduledTaskSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class WorkflowSchedulerTaskDetailView(APIView):
    """GET /api/v1/workflow-scheduler/tasks/{id}/"""

    def get(self, request, pk=None, *args, **kwargs):
        task = WorkflowScheduledTask.objects.filter(id=pk).first()
        if task is None:
            return response.Response({'error': 'Scheduled task not found.'}, status=status.HTTP_404_NOT_FOUND)
        logs = WorkflowSchedulerLog.objects.filter(task=task).order_by('-created_at')
        return response.Response(
            {
                'task': WorkflowScheduledTaskSerializer(task).data,
                'logs': WorkflowSchedulerLogSerializer(logs, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class WorkflowSchedulerTaskRetryView(APIView):
    """POST /api/v1/workflow-scheduler/tasks/{id}/retry/"""

    def post(self, request, pk=None, *args, **kwargs):
        task = WorkflowScheduledTask.objects.filter(id=pk).first()
        if task is None:
            return response.Response({'error': 'Scheduled task not found.'}, status=status.HTTP_404_NOT_FOUND)
        retried = WorkflowSchedulerEngine.retry_task(task, reason='Retry requested by API')
        return response.Response(WorkflowScheduledTaskSerializer(retried).data, status=status.HTTP_200_OK)


class WorkflowSchedulerTaskCancelView(APIView):
    """POST /api/v1/workflow-scheduler/tasks/{id}/cancel/"""

    def post(self, request, pk=None, *args, **kwargs):
        task = WorkflowSchedulerEngine.cancel_task(pk)
        if task is None:
            return response.Response({'error': 'Scheduled task not found.'}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(WorkflowScheduledTaskSerializer(task).data, status=status.HTTP_200_OK)


class WorkflowActionListView(APIView):
    """GET/POST /api/v1/workflow-actions/"""

    def get(self, request, *args, **kwargs):
        qs = WorkflowActionDefinition.objects.all().order_by('execution_order', 'created_at')
        workflow_id = request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        stage_id = request.query_params.get('stage_id')
        if stage_id:
            qs = qs.filter(stage_id=stage_id)
        if request.query_params.get('active') == 'true':
            qs = qs.filter(is_active=True)
        return response.Response(WorkflowActionDefinitionSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        ser = WorkflowActionDefinitionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        record = ser.save()
        dependencies = request.data.get('dependencies', []) or []
        for dependency in dependencies:
            depends_on_id = dependency.get('depends_on_action_id')
            dependency_type = dependency.get('dependency_type', 'must_complete_first')
            if depends_on_id:
                WorkflowActionDependency.objects.get_or_create(
                    tenant_id=record.tenant_id,
                    action_definition=record,
                    depends_on_action_id=depends_on_id,
                    dependency_type=dependency_type,
                )
        payload = WorkflowActionDefinitionSerializer(record).data
        payload['dependencies'] = WorkflowActionDependencySerializer(record.dependencies.all(), many=True).data
        return response.Response(payload, status=status.HTTP_201_CREATED)


class WorkflowActionDetailView(APIView):
    """GET/PUT /api/v1/workflow-actions/{id}/"""

    def get(self, request, pk=None, *args, **kwargs):
        record = WorkflowActionDefinition.objects.filter(id=pk).first()
        if not record:
            return response.Response({'error': 'Workflow action not found.'}, status=status.HTTP_404_NOT_FOUND)
        payload = WorkflowActionDefinitionSerializer(record).data
        payload['dependencies'] = WorkflowActionDependencySerializer(record.dependencies.all(), many=True).data
        payload['recent_logs'] = WorkflowActionExecutionLogSerializer(record.execution_logs.all()[:20], many=True).data
        return response.Response(payload, status=status.HTTP_200_OK)

    def put(self, request, pk=None, *args, **kwargs):
        record = WorkflowActionDefinition.objects.filter(id=pk).first()
        if not record:
            return response.Response({'error': 'Workflow action not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowActionDefinitionSerializer(record, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        updated = ser.save()
        if 'dependencies' in request.data:
            updated.dependencies.all().delete()
            for dependency in request.data.get('dependencies', []) or []:
                depends_on_id = dependency.get('depends_on_action_id')
                dependency_type = dependency.get('dependency_type', 'must_complete_first')
                if depends_on_id:
                    WorkflowActionDependency.objects.create(
                        tenant_id=updated.tenant_id,
                        action_definition=updated,
                        depends_on_action_id=depends_on_id,
                        dependency_type=dependency_type,
                    )
        payload = WorkflowActionDefinitionSerializer(updated).data
        payload['dependencies'] = WorkflowActionDependencySerializer(updated.dependencies.all(), many=True).data
        return response.Response(payload, status=status.HTTP_200_OK)


class WorkflowActionTestRunView(APIView):
    """POST /api/v1/workflow-actions/{id}/test-run/"""

    def post(self, request, pk=None, *args, **kwargs):
        action_def = WorkflowActionDefinition.objects.filter(id=pk).first()
        if not action_def:
            return response.Response({'error': 'Workflow action not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowActionTestRunSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        instance = WorkflowInstance.objects.filter(id=data['workflow_instance_id']).first()
        if instance is None:
            return response.Response({'error': 'Workflow instance not found.'}, status=status.HTTP_404_NOT_FOUND)
        stage_execution = None
        if data.get('stage_execution_id'):
            stage_execution = WorkflowStageExecution.objects.filter(id=data['stage_execution_id']).first()
        if stage_execution is None:
            stage_execution = instance.stage_executions.filter(stage_id=action_def.stage_id).order_by('-created_at').first()

        log = WorkflowActionHandlersEngine.execute_action(
            instance=instance,
            stage_execution=stage_execution,
            action_definition=action_def,
            action_context=data.get('context', {}),
        )
        return response.Response(WorkflowActionExecutionLogSerializer(log).data, status=status.HTTP_200_OK)


class WorkflowHumanTaskListView(APIView):
    """GET /api/v1/workflow-human-tasks/"""

    def get(self, request, *args, **kwargs):
        qs = WorkflowHumanTask.objects.select_related('workflow_instance', 'stage_execution').all().order_by('due_at', 'created_at')
        tenant_id = request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        workflow_instance_id = request.query_params.get('workflow_instance_id')
        if workflow_instance_id:
            qs = qs.filter(workflow_instance_id=workflow_instance_id)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        assigned_to_id = request.query_params.get('assigned_to_id')
        if assigned_to_id:
            qs = qs.filter(assigned_to_id=assigned_to_id)
        return response.Response(WorkflowHumanTaskSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class WorkflowHumanTaskDetailView(APIView):
    """GET /api/v1/workflow-human-tasks/{id}/"""

    def get(self, request, pk=None, *args, **kwargs):
        task = WorkflowHumanTask.objects.select_related('workflow_instance', 'stage_execution').filter(id=pk).first()
        if not task:
            return response.Response({'error': 'Workflow human task not found.'}, status=status.HTTP_404_NOT_FOUND)
        payload = WorkflowHumanTaskSerializer(task).data
        payload['approval_logs'] = WorkflowApprovalLogSerializer(task.approval_logs.all(), many=True).data
        return response.Response(payload, status=status.HTTP_200_OK)


class WorkflowHumanTaskCompleteView(APIView):
    """POST /api/v1/workflow-human-tasks/{id}/complete/"""

    def post(self, request, pk=None, *args, **kwargs):
        task = WorkflowHumanTask.objects.filter(id=pk).first()
        if not task:
            return response.Response({'error': 'Workflow human task not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowHumanTaskCompleteSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        result = WorkflowHumanTaskEngine.complete_human_task(
            task=task,
            completed_by_type=data.get('actor_type', 'user'),
            completed_by_id=data.get('actor_id'),
            comments=data.get('comments', ''),
            metadata=data.get('context', {}),
        )
        task.refresh_from_db()
        return response.Response({'task': WorkflowHumanTaskSerializer(task).data, 'result': result}, status=status.HTTP_200_OK)


class WorkflowHumanTaskRejectView(APIView):
    """POST /api/v1/workflow-human-tasks/{id}/reject/"""

    def post(self, request, pk=None, *args, **kwargs):
        task = WorkflowHumanTask.objects.filter(id=pk).first()
        if not task:
            return response.Response({'error': 'Workflow human task not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowHumanTaskCompleteSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        result = WorkflowHumanTaskEngine.reject_human_task(
            task=task,
            rejected_by_type=data.get('actor_type', 'user'),
            rejected_by_id=data.get('actor_id'),
            comments=data.get('comments', ''),
            metadata=data.get('context', {}),
        )
        task.refresh_from_db()
        return response.Response({'task': WorkflowHumanTaskSerializer(task).data, 'result': result}, status=status.HTTP_200_OK)


class WorkflowHumanTaskEscalateView(APIView):
    """POST /api/v1/workflow-human-tasks/{id}/escalate/"""

    def post(self, request, pk=None, *args, **kwargs):
        task = WorkflowHumanTask.objects.filter(id=pk).first()
        if not task:
            return response.Response({'error': 'Workflow human task not found.'}, status=status.HTTP_404_NOT_FOUND)
        reason = str((request.data or {}).get('reason', 'Escalated by API request'))
        task = WorkflowHumanTaskEngine.escalate_human_task(task=task, reason=reason)
        return response.Response(WorkflowHumanTaskSerializer(task).data, status=status.HTTP_200_OK)


class WorkflowVersionListView(APIView):
    """GET /api/v1/workflow-versions/"""

    def get(self, request, *args, **kwargs):
        qs = WorkflowVersion.objects.all().order_by('-version_number', '-created_at')
        workflow_id = request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return response.Response(WorkflowVersionSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class WorkflowVersionDetailView(APIView):
    """GET /api/v1/workflow-versions/{id}/"""

    def get(self, request, pk=None, *args, **kwargs):
        version = WorkflowVersion.objects.filter(id=pk).first()
        if version is None:
            return response.Response({'error': 'Workflow version not found.'}, status=status.HTTP_404_NOT_FOUND)
        payload = WorkflowVersionSerializer(version).data
        payload['change_logs'] = WorkflowVersionChangeLogSerializer(version.change_logs.all()[:50], many=True).data
        return response.Response(payload, status=status.HTTP_200_OK)


class WorkflowDraftGetView(APIView):
    """GET /api/v1/workflows/{id}/draft/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        draft = WorkflowDraft.objects.filter(
            workflow_id=workflow_id,
            status__in=['editing', 'ready_for_publish', 'published'],
        ).order_by('-updated_at').first()
        if draft is None:
            return response.Response({'error': 'Workflow draft not found.'}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(WorkflowDraftSerializer(draft).data, status=status.HTTP_200_OK)


class WorkflowVersionsByWorkflowView(APIView):
    """GET /api/v1/workflows/{id}/versions/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        versions = WorkflowVersion.objects.filter(workflow_id=workflow_id).order_by('-version_number')
        return response.Response(WorkflowVersionSerializer(versions, many=True).data, status=status.HTTP_200_OK)


class WorkflowVersionCompareView(APIView):
    """GET /api/v1/workflows/{id}/versions/compare/?from={id}&to={id}"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        from_version_id = request.query_params.get('from')
        to_version_id = request.query_params.get('to')
        if not from_version_id or not to_version_id:
            return response.Response({'error': 'Both from and to version IDs are required.'}, status=status.HTTP_400_BAD_REQUEST)
        comparison = WorkflowVersioningEngine.compare_versions(
            workflow_id=workflow_id,
            from_version_id=from_version_id,
            to_version_id=to_version_id,
        )
        if comparison is None:
            return response.Response({'error': 'One or both versions not found.'}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(WorkflowVersionComparisonSerializer(comparison).data, status=status.HTTP_200_OK)


class WorkflowDraftCreateView(APIView):
    """POST /api/v1/workflows/{id}/draft/create/"""

    def post(self, request, workflow_id=None, *args, **kwargs):
        ser = WorkflowDraftCreateSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        draft = WorkflowVersioningEngine.create_draft(
            workflow_id=workflow_id,
            name=data.get('name', ''),
            description=data.get('description', ''),
            builder_mode=data.get('builder_mode', 'guided'),
            created_by=data.get('created_by'),
        )
        return response.Response(WorkflowDraftSerializer(draft).data, status=status.HTTP_201_CREATED)


class WorkflowDraftSaveView(APIView):
    """POST /api/v1/workflows/{id}/draft/save/"""

    def post(self, request, workflow_id=None, *args, **kwargs):
        ser = WorkflowDraftSaveSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        draft = None
        if data.get('draft_id'):
            draft = WorkflowDraft.objects.filter(id=data.get('draft_id'), workflow_id=workflow_id).first()
        if draft is None:
            draft = WorkflowDraft.objects.filter(workflow_id=workflow_id, status__in=['editing', 'ready_for_publish']).order_by('-updated_at').first()
        if draft is None:
            draft = WorkflowVersioningEngine.create_draft(workflow_id=workflow_id, created_by=data.get('changed_by'))

        WorkflowVersioningEngine.update_draft(
            draft=draft,
            name=data.get('name'),
            description=data.get('description'),
            builder_mode=data.get('builder_mode'),
        )
        WorkflowVersioningEngine.save_draft_snapshot(
            draft=draft,
            config_snapshot=data.get('config_snapshot'),
            ready_for_publish=data.get('ready_for_publish', False),
            changed_by=data.get('changed_by'),
        )
        draft.refresh_from_db()
        return response.Response(WorkflowDraftSerializer(draft).data, status=status.HTTP_200_OK)


class WorkflowDraftPublishView(APIView):
    """POST /api/v1/workflows/{id}/draft/publish/"""

    def post(self, request, workflow_id=None, *args, **kwargs):
        ser = WorkflowDraftPublishSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        draft = None
        if data.get('draft_id'):
            draft = WorkflowDraft.objects.filter(id=data.get('draft_id'), workflow_id=workflow_id).first()
        if draft is None:
            draft = WorkflowDraft.objects.filter(workflow_id=workflow_id, status__in=['editing', 'ready_for_publish']).order_by('-updated_at').first()
        if draft is None:
            return response.Response({'error': 'No editable draft found to publish.'}, status=status.HTTP_404_NOT_FOUND)

        version = WorkflowVersioningEngine.publish_draft(
            draft=draft,
            notes=data.get('notes', ''),
            changed_by=data.get('changed_by'),
        )
        return response.Response(WorkflowVersionSerializer(version).data, status=status.HTTP_200_OK)


class WorkflowVersionRollbackView(APIView):
    """POST /api/v1/workflows/{id}/versions/{id}/rollback/"""

    def post(self, request, workflow_id=None, version_id=None, *args, **kwargs):
        ser = WorkflowVersionRollbackSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        version = WorkflowVersioningEngine.rollback_to_version(
            workflow_id=workflow_id,
            version_id=version_id,
            changed_by=data.get('changed_by'),
        )
        if version is None:
            return response.Response({'error': 'Target version not found.'}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(WorkflowVersionSerializer(version).data, status=status.HTTP_200_OK)


class WorkflowVersionCloneView(APIView):
    """POST /api/v1/workflows/{id}/versions/{id}/clone/"""

    def post(self, request, workflow_id=None, version_id=None, *args, **kwargs):
        ser = WorkflowVersionCloneSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        draft = WorkflowVersioningEngine.clone_version(
            workflow_id=workflow_id,
            version_id=version_id,
            changed_by=data.get('changed_by'),
        )
        if draft is None:
            return response.Response({'error': 'Source version not found.'}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(WorkflowDraftSerializer(draft).data, status=status.HTTP_201_CREATED)


class WorkflowDraftDiscardView(APIView):
    """POST /api/v1/workflows/{id}/draft/discard/"""

    def post(self, request, workflow_id=None, *args, **kwargs):
        ser = WorkflowDraftDiscardSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        draft = None
        if data.get('draft_id'):
            draft = WorkflowDraft.objects.filter(id=data.get('draft_id'), workflow_id=workflow_id).first()
        if draft is None:
            draft = WorkflowDraft.objects.filter(workflow_id=workflow_id, status__in=['editing', 'ready_for_publish']).order_by('-updated_at').first()
        if draft is None:
            return response.Response({'error': 'No editable draft found to discard.'}, status=status.HTTP_404_NOT_FOUND)

        draft = WorkflowVersioningEngine.discard_draft(
            draft=draft,
            changed_by=data.get('changed_by'),
        )
        return response.Response(WorkflowDraftSerializer(draft).data, status=status.HTTP_200_OK)


class WorkflowTemplateListView(APIView):
    """GET/POST /api/v1/workflow-templates/"""

    def get(self, request, *args, **kwargs):
        WorkflowTemplateEngine.ensure_system_templates()
        qs = WorkflowTemplate.objects.all().order_by('category', 'name')
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        template_type = request.query_params.get('template_type')
        if template_type:
            qs = qs.filter(template_type=template_type)
        visibility = request.query_params.get('visibility')
        if visibility:
            qs = qs.filter(visibility=visibility)
        is_active = request.query_params.get('is_active')
        if is_active in {'true', 'false'}:
            qs = qs.filter(is_active=(is_active == 'true'))
        qs = qs.annotate(
            rating_average=Avg('ratings__rating'),
            usage_count=Count('usages'),
        )
        return response.Response(WorkflowTemplateSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        ser = WorkflowTemplateCreateSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        template = WorkflowTemplateEngine.create_template(
            name=data['name'],
            description=data.get('description', ''),
            category=data.get('category', 'custom'),
            template_type=data.get('template_type', 'custom'),
            visibility=data.get('visibility', 'private'),
            tenant_id=data.get('tenant_id'),
            created_by=data.get('created_by'),
            config_snapshot=data.get('config_snapshot', {}),
            metadata=data.get('metadata', {}),
        )
        template = WorkflowTemplate.objects.filter(id=template.id).annotate(
            rating_average=Avg('ratings__rating'),
            usage_count=Count('usages'),
        ).first()
        return response.Response(WorkflowTemplateSerializer(template).data, status=status.HTTP_201_CREATED)


class WorkflowTemplateDetailView(APIView):
    """GET /api/v1/workflow-templates/{id}/"""

    def get(self, request, pk=None, *args, **kwargs):
        template = WorkflowTemplate.objects.filter(id=pk).annotate(
            rating_average=Avg('ratings__rating'),
            usage_count=Count('usages'),
        ).first()
        if template is None:
            return response.Response({'error': 'Workflow template not found.'}, status=status.HTTP_404_NOT_FOUND)
        payload = WorkflowTemplateSerializer(template).data
        payload['latest_version'] = WorkflowTemplateVersionSerializer(
            template.versions.order_by('-version_number').first()
        ).data if template.versions.exists() else None
        payload['latest_ratings'] = WorkflowTemplateRatingSerializer(
            template.ratings.all()[:10],
            many=True,
        ).data
        return response.Response(payload, status=status.HTTP_200_OK)


class WorkflowTemplateVersionsView(APIView):
    """GET /api/v1/workflow-templates/{id}/versions/"""

    def get(self, request, pk=None, *args, **kwargs):
        template = WorkflowTemplate.objects.filter(id=pk).first()
        if template is None:
            return response.Response({'error': 'Workflow template not found.'}, status=status.HTTP_404_NOT_FOUND)
        versions = template.versions.order_by('-version_number')
        return response.Response(WorkflowTemplateVersionSerializer(versions, many=True).data, status=status.HTTP_200_OK)


class WorkflowTemplateCloneView(APIView):
    """POST /api/v1/workflow-templates/{id}/clone/"""

    def post(self, request, pk=None, *args, **kwargs):
        template = WorkflowTemplate.objects.filter(id=pk).first()
        if template is None:
            return response.Response({'error': 'Workflow template not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowTemplateCloneSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        cloned = WorkflowTemplateEngine.clone_template(
            template=template,
            created_by=data.get('created_by'),
            tenant_id=data.get('tenant_id'),
            name=data.get('name') or None,
        )
        cloned = WorkflowTemplate.objects.filter(id=cloned.id).annotate(
            rating_average=Avg('ratings__rating'),
            usage_count=Count('usages'),
        ).first()
        return response.Response(WorkflowTemplateSerializer(cloned).data, status=status.HTTP_201_CREATED)


class WorkflowTemplateApplyView(APIView):
    """POST /api/v1/workflow-templates/{id}/apply/"""

    def post(self, request, pk=None, *args, **kwargs):
        template = WorkflowTemplate.objects.filter(id=pk, is_active=True).first()
        if template is None:
            return response.Response({'error': 'Active workflow template not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowTemplateApplySerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        workflow = WorkflowTemplateEngine.apply_template(
            template=template,
            tenant_id=data['tenant_id'],
            workflow_name=data.get('workflow_name') or None,
            workflow_description=data.get('workflow_description', ''),
            trigger_event=data.get('trigger_event', 'manual'),
            used_by=data.get('used_by'),
        )
        usage = WorkflowTemplateUsage.objects.filter(template=template, workflow_id=workflow.id).order_by('-created_at').first()
        return response.Response(
            {
                'template': WorkflowTemplateSerializer(
                    WorkflowTemplate.objects.filter(id=template.id).annotate(
                        rating_average=Avg('ratings__rating'),
                        usage_count=Count('usages'),
                    ).first()
                ).data,
                'workflow_id': str(workflow.id),
                'usage': WorkflowTemplateUsageSerializer(usage).data if usage else None,
            },
            status=status.HTTP_201_CREATED,
        )


class WorkflowTemplatePublishView(APIView):
    """POST /api/v1/workflow-templates/{id}/publish/"""

    def post(self, request, pk=None, *args, **kwargs):
        template = WorkflowTemplate.objects.filter(id=pk).first()
        if template is None:
            return response.Response({'error': 'Workflow template not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowTemplatePublishSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        template = WorkflowTemplateEngine.publish_template(template=template, visibility=ser.validated_data.get('visibility'))
        template = WorkflowTemplate.objects.filter(id=template.id).annotate(
            rating_average=Avg('ratings__rating'),
            usage_count=Count('usages'),
        ).first()
        return response.Response(WorkflowTemplateSerializer(template).data, status=status.HTTP_200_OK)


class WorkflowTemplateArchiveView(APIView):
    """POST /api/v1/workflow-templates/{id}/archive/"""

    def post(self, request, pk=None, *args, **kwargs):
        template = WorkflowTemplate.objects.filter(id=pk).first()
        if template is None:
            return response.Response({'error': 'Workflow template not found.'}, status=status.HTTP_404_NOT_FOUND)
        template = WorkflowTemplateEngine.archive_template(template=template)
        template = WorkflowTemplate.objects.filter(id=template.id).annotate(
            rating_average=Avg('ratings__rating'),
            usage_count=Count('usages'),
        ).first()
        return response.Response(WorkflowTemplateSerializer(template).data, status=status.HTTP_200_OK)


class WorkflowTemplateImportView(APIView):
    """POST /api/v1/workflow-templates/import/"""

    def post(self, request, *args, **kwargs):
        ser = WorkflowTemplateImportSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        payload = data['payload']
        if not isinstance(payload, dict):
            return response.Response({'error': 'Template payload must be a JSON object.'}, status=status.HTTP_400_BAD_REQUEST)
        template = WorkflowTemplateEngine.import_template(
            payload=payload,
            tenant_id=data.get('tenant_id'),
            created_by=data.get('created_by'),
        )
        template = WorkflowTemplate.objects.filter(id=template.id).annotate(
            rating_average=Avg('ratings__rating'),
            usage_count=Count('usages'),
        ).first()
        return response.Response(WorkflowTemplateSerializer(template).data, status=status.HTTP_201_CREATED)


class WorkflowTemplateExportView(APIView):
    """GET /api/v1/workflow-templates/{id}/export/"""

    def get(self, request, pk=None, *args, **kwargs):
        template = WorkflowTemplate.objects.filter(id=pk).first()
        if template is None:
            return response.Response({'error': 'Workflow template not found.'}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(WorkflowTemplateEngine.export_template(template=template), status=status.HTTP_200_OK)


class WorkflowTemplateRateView(APIView):
    """POST /api/v1/workflow-templates/{id}/rate/"""

    def post(self, request, pk=None, *args, **kwargs):
        template = WorkflowTemplate.objects.filter(id=pk).first()
        if template is None:
            return response.Response({'error': 'Workflow template not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowTemplateRateSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        rating = WorkflowTemplateEngine.rate_template(
            template=template,
            rating=data['rating'],
            review=data.get('review', ''),
            created_by=data.get('created_by'),
            tenant_id=data.get('tenant_id'),
        )
        template = WorkflowTemplate.objects.filter(id=template.id).annotate(
            rating_average=Avg('ratings__rating'),
            usage_count=Count('usages'),
        ).first()
        return response.Response(
            {
                'rating': WorkflowTemplateRatingSerializer(rating).data,
                'template': WorkflowTemplateSerializer(template).data,
            },
            status=status.HTTP_201_CREATED,
        )


class WorkflowBuilderGraphView(APIView):
    """GET /api/v1/workflow-builder/{workflow_id}/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        graph = WorkflowVisualBuilderEngine.export_workflow_graph(workflow_id=workflow_id)
        validation = WorkflowVisualBuilderEngine.validate_workflow_graph(workflow_id=workflow_id)
        layout = WorkflowBuilderLayout.objects.filter(workflow_id=workflow_id).first()
        return response.Response(
            {
                'graph': graph,
                'layout': WorkflowBuilderLayoutSerializer(layout).data if layout else None,
                'validation': validation,
            },
            status=status.HTTP_200_OK,
        )


class WorkflowBuilderNodeCreateView(APIView):
    """POST /api/v1/workflow-builder/node/"""

    def post(self, request, *args, **kwargs):
        ser = WorkflowBuilderNodeCreateSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        node = WorkflowVisualBuilderEngine.create_node(
            workflow_id=data['workflow_id'],
            node_type=data['node_type'],
            node_name=data['node_name'],
            position_x=data.get('position_x', 0),
            position_y=data.get('position_y', 0),
            config=data.get('config', {}),
            tenant_id=data.get('tenant_id'),
            created_by=data.get('created_by'),
        )
        return response.Response(WorkflowBuilderNodeSerializer(node).data, status=status.HTTP_201_CREATED)


class WorkflowBuilderNodeUpdateDeleteView(APIView):
    """PUT/DELETE /api/v1/workflow-builder/node/{id}/"""

    def put(self, request, pk=None, *args, **kwargs):
        node = WorkflowBuilderNode.objects.filter(id=pk).first()
        if node is None:
            return response.Response({'error': 'Builder node not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowBuilderNodeUpdateSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        updated = WorkflowVisualBuilderEngine.update_node(node=node, **ser.validated_data)
        return response.Response(WorkflowBuilderNodeSerializer(updated).data, status=status.HTTP_200_OK)

    def delete(self, request, pk=None, *args, **kwargs):
        node = WorkflowBuilderNode.objects.filter(id=pk).first()
        if node is None:
            return response.Response({'error': 'Builder node not found.'}, status=status.HTTP_404_NOT_FOUND)
        WorkflowVisualBuilderEngine.delete_node(node)
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class WorkflowBuilderConnectionCreateView(APIView):
    """POST /api/v1/workflow-builder/connection/"""

    def post(self, request, *args, **kwargs):
        ser = WorkflowBuilderConnectionCreateSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        try:
            connection = WorkflowVisualBuilderEngine.connect_nodes(
                workflow_id=data['workflow_id'],
                source_node_id=data['source_node_id'],
                target_node_id=data['target_node_id'],
                condition_label=data.get('condition_label', ''),
                connection_type=data.get('connection_type', 'default'),
                metadata=data.get('metadata', {}),
                tenant_id=data.get('tenant_id'),
                created_by=data.get('created_by'),
            )
        except ValueError as exc:
            return response.Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return response.Response(WorkflowBuilderConnectionSerializer(connection).data, status=status.HTTP_201_CREATED)


class WorkflowBuilderConnectionDeleteView(APIView):
    """DELETE /api/v1/workflow-builder/connection/{id}/"""

    def delete(self, request, pk=None, *args, **kwargs):
        connection = WorkflowBuilderConnection.objects.filter(id=pk).first()
        if connection is None:
            return response.Response({'error': 'Builder connection not found.'}, status=status.HTTP_404_NOT_FOUND)
        WorkflowVisualBuilderEngine.remove_connection(connection)
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class WorkflowBuilderValidateView(APIView):
    """POST /api/v1/workflow-builder/validate/"""

    def post(self, request, *args, **kwargs):
        ser = WorkflowBuilderValidateSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        validation = WorkflowVisualBuilderEngine.validate_workflow_graph(workflow_id=ser.validated_data['workflow_id'])
        status_code = status.HTTP_200_OK if validation['valid'] else status.HTTP_400_BAD_REQUEST
        return response.Response(validation, status=status_code)


class WorkflowBuilderSaveView(APIView):
    """POST /api/v1/workflow-builder/save/"""

    def post(self, request, *args, **kwargs):
        ser = WorkflowBuilderSaveSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        workflow_id = data['workflow_id']

        if data.get('payload'):
            WorkflowVisualBuilderEngine.import_workflow_graph(
                workflow_id=workflow_id,
                payload=data['payload'],
                tenant_id=data.get('tenant_id'),
                created_by=data.get('created_by'),
            )
        if data.get('auto_layout'):
            WorkflowVisualBuilderEngine.auto_layout_graph(workflow_id=workflow_id)

        result = WorkflowVisualBuilderEngine.save_to_runtime(workflow_id=workflow_id)
        status_code = status.HTTP_200_OK if result.get('saved') else status.HTTP_400_BAD_REQUEST
        result['graph'] = WorkflowVisualBuilderEngine.export_workflow_graph(workflow_id=workflow_id)
        return response.Response(result, status=status_code)


class WorkflowObservabilityInstanceTimelineView(APIView):
    """GET /api/v1/workflow-observability/instances/{id}/timeline/"""

    def get(self, request, instance_id=None, *args, **kwargs):
        entries = WorkflowObservabilityEngine.get_instance_timeline(instance_id)
        return response.Response(WorkflowExecutionTimelineEntrySerializer(entries, many=True).data, status=status.HTTP_200_OK)


class WorkflowObservabilityInstanceTraceView(APIView):
    """GET /api/v1/workflow-observability/instances/{id}/trace/"""

    def get(self, request, instance_id=None, *args, **kwargs):
        traces = WorkflowObservabilityEngine.get_instance_trace(instance_id)
        return response.Response(WorkflowExecutionTraceSerializer(traces, many=True).data, status=status.HTTP_200_OK)


class WorkflowObservabilityInstanceSnapshotView(APIView):
    """GET /api/v1/workflow-observability/instances/{id}/snapshot/"""

    def get(self, request, instance_id=None, *args, **kwargs):
        snapshot = WorkflowObservabilityEngine.get_instance_snapshot(instance_id)
        if snapshot is None:
            return response.Response({'error': 'Workflow instance not found.'}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(WorkflowObservabilitySnapshotSerializer(snapshot).data, status=status.HTTP_200_OK)


class WorkflowObservabilityInstanceMetricsView(APIView):
    """GET /api/v1/workflow-observability/instances/{id}/metrics/"""

    def get(self, request, instance_id=None, *args, **kwargs):
        metrics = WorkflowExecutionMetric.objects.filter(workflow_instance_id=instance_id).order_by('-recorded_at')
        return response.Response(WorkflowExecutionMetricSerializer(metrics, many=True).data, status=status.HTTP_200_OK)


class WorkflowObservabilityInstanceHealthView(APIView):
    """GET /api/v1/workflow-observability/instances/{id}/health/"""

    def get(self, request, instance_id=None, *args, **kwargs):
        health = WorkflowObservabilityEngine.summarize_execution_health(instance_id)
        if health is None:
            return response.Response({'error': 'Workflow instance not found.'}, status=status.HTTP_404_NOT_FOUND)
        health['stage_observability'] = WorkflowObservabilityEngine.get_stage_observability(instance_id)
        health['failure_summary'] = WorkflowObservabilityEngine.get_failure_summary(instance_id)
        return response.Response(health, status=status.HTTP_200_OK)


class WorkflowObservabilityWorkflowSummaryView(APIView):
    """GET /api/v1/workflow-observability/workflows/{id}/summary/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        summary = WorkflowObservabilityEngine.get_workflow_summary(workflow_id)
        return response.Response(summary, status=status.HTTP_200_OK)


class WorkflowObservabilityWorkflowFailuresView(APIView):
    """GET /api/v1/workflow-observability/workflows/{id}/failures/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        failures = WorkflowObservabilityEngine.get_workflow_failures(workflow_id)
        return response.Response(WorkflowFailureLogSerializer(failures, many=True).data, status=status.HTTP_200_OK)


class WorkflowObservabilityWorkflowSLARisksView(APIView):
    """GET /api/v1/workflow-observability/workflows/{id}/sla-risks/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        risks = WorkflowObservabilityEngine.get_workflow_sla_risks(workflow_id)
        return response.Response(WorkflowSLATrackerSerializer(risks, many=True).data, status=status.HTTP_200_OK)


class WorkflowAnalyticsWorkflowListView(APIView):
    """GET /api/v1/workflow-analytics/workflows/"""

    def get(self, request, *args, **kwargs):
        workflow_ids = WorkflowInstance.objects.values_list('workflow_id', flat=True).distinct()
        rows = []
        for workflow_id in workflow_ids:
            summary = WorkflowMetricsAnalyticsEngine.summarize_workflow_health(workflow_id=workflow_id)
            rows.append(summary)
        return response.Response(rows, status=status.HTTP_200_OK)


class WorkflowAnalyticsSummaryView(APIView):
    """GET /api/v1/workflow-analytics/workflows/{id}/summary/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        summary = WorkflowMetricsAnalyticsEngine.summarize_workflow_health(workflow_id=workflow_id)
        return response.Response(summary, status=status.HTTP_200_OK)


class WorkflowAnalyticsTimelineView(APIView):
    """GET /api/v1/workflow-analytics/workflows/{id}/timeline/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        instance_ids = WorkflowInstance.objects.filter(workflow_id=workflow_id).values_list('id', flat=True)
        entries = WorkflowExecutionTimelineEntry.objects.filter(workflow_instance_id__in=instance_ids).order_by('created_at')
        return response.Response(WorkflowExecutionTimelineEntrySerializer(entries, many=True).data, status=status.HTTP_200_OK)


class WorkflowAnalyticsBottlenecksView(APIView):
    """GET /api/v1/workflow-analytics/workflows/{id}/bottlenecks/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        today = timezone.localdate()
        WorkflowMetricsAnalyticsEngine.generate_stage_metrics(workflow_id=workflow_id, metric_date=today)
        payload = WorkflowMetricsAnalyticsEngine.calculate_bottlenecks(workflow_id=workflow_id, metric_date=today)
        return response.Response(payload, status=status.HTTP_200_OK)


class WorkflowAnalyticsFailuresView(APIView):
    """GET /api/v1/workflow-analytics/workflows/{id}/failures/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        metric_date = timezone.localdate()
        WorkflowMetricsAnalyticsEngine.generate_failure_metrics(workflow_id=workflow_id, metric_date=metric_date)
        rows = WorkflowFailureMetric.objects.filter(workflow_id=workflow_id, metric_date=metric_date).order_by('-failure_count')
        return response.Response(WorkflowFailureMetricSerializer(rows, many=True).data, status=status.HTTP_200_OK)


class WorkflowAnalyticsStagesView(APIView):
    """GET /api/v1/workflow-analytics/workflows/{id}/stages/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        metric_date = timezone.localdate()
        WorkflowMetricsAnalyticsEngine.generate_stage_metrics(workflow_id=workflow_id, metric_date=metric_date)
        rows = WorkflowStageMetric.objects.filter(workflow_id=workflow_id, metric_date=metric_date).order_by('-average_time_in_stage_seconds')
        return response.Response(WorkflowStageMetricSerializer(rows, many=True).data, status=status.HTTP_200_OK)


class WorkflowAnalyticsActionsView(APIView):
    """GET /api/v1/workflow-analytics/workflows/{id}/actions/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        metric_date = timezone.localdate()
        WorkflowMetricsAnalyticsEngine.generate_action_metrics(workflow_id=workflow_id, metric_date=metric_date)
        rows = WorkflowActionMetric.objects.filter(workflow_id=workflow_id, metric_date=metric_date).order_by('-execution_count')
        return response.Response(WorkflowActionMetricSerializer(rows, many=True).data, status=status.HTTP_200_OK)


class WorkflowAnalyticsImpactView(APIView):
    """GET /api/v1/workflow-analytics/workflows/{id}/impact/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        metric_date = timezone.localdate()
        impact = WorkflowMetricsAnalyticsEngine.generate_automation_impact_metrics(
            workflow_id=workflow_id,
            metric_date=metric_date,
        )
        return response.Response(WorkflowAutomationImpactMetricSerializer(impact).data, status=status.HTTP_200_OK)


class WorkflowAnalyticsTrendsView(APIView):
    """GET /api/v1/workflow-analytics/workflows/{id}/trends/"""

    def get(self, request, workflow_id=None, *args, **kwargs):
        days = int(request.query_params.get('days', 30))
        payload = WorkflowMetricsAnalyticsEngine.build_workflow_trend_data(workflow_id=workflow_id, days=days)
        return response.Response(payload, status=status.HTTP_200_OK)


class WorkflowRecoveryCaseListView(APIView):
    """GET /api/v1/workflow-recovery/cases/"""

    def get(self, request, *args, **kwargs):
        qs = WorkflowRecoveryCase.objects.select_related('workflow_instance', 'stage_execution', 'action_execution_log').all().order_by('-created_at')
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        workflow_instance_id = request.query_params.get('workflow_instance_id')
        if workflow_instance_id:
            qs = qs.filter(workflow_instance_id=workflow_instance_id)
        return response.Response(WorkflowRecoveryCaseSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class WorkflowRecoveryCaseDetailView(APIView):
    """GET /api/v1/workflow-recovery/cases/{id}/"""

    def get(self, request, pk=None, *args, **kwargs):
        case = WorkflowRecoveryCase.objects.filter(id=pk).first()
        if case is None:
            return response.Response({'error': 'Recovery case not found.'}, status=status.HTTP_404_NOT_FOUND)
        payload = WorkflowRecoveryCaseSerializer(case).data
        payload['retry_attempts'] = WorkflowRetryAttemptSerializer(case.retry_attempts.all().order_by('-started_at'), many=True).data
        payload['action_logs'] = WorkflowRecoveryActionLogSerializer(case.action_logs.all().order_by('-created_at'), many=True).data
        return response.Response(payload, status=status.HTTP_200_OK)


class WorkflowRecoveryPolicyListCreateView(APIView):
    """GET/POST /api/v1/workflow-recovery/policies/"""

    def get(self, request, *args, **kwargs):
        qs = WorkflowRecoveryPolicy.objects.all().order_by('-created_at')
        workflow_id = request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        if request.query_params.get('active') == 'true':
            qs = qs.filter(is_active=True)
        return response.Response(WorkflowRecoveryPolicySerializer(qs, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        ser = WorkflowRecoveryPolicyCreateSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        record = WorkflowRecoveryPolicy.objects.create(
            tenant_id=data.get('tenant_id'),
            workflow_id=data['workflow_id'],
            stage_id=data.get('stage_id'),
            action_type=data.get('action_type', ''),
            failure_type=data.get('failure_type', 'unknown'),
            retry_strategy=data.get('retry_strategy', 'manual_only'),
            retry_limit=data.get('retry_limit', 0),
            retry_delay_seconds=data.get('retry_delay_seconds', 0),
            escalate_after_failures=data.get('escalate_after_failures', 0),
            requires_manual_review=data.get('requires_manual_review', False),
            is_active=data.get('is_active', True),
            metadata=data.get('metadata', {}),
        )
        return response.Response(WorkflowRecoveryPolicySerializer(record).data, status=status.HTTP_201_CREATED)


class WorkflowRecoveryCaseRetryView(APIView):
    """POST /api/v1/workflow-recovery/cases/{id}/retry/"""

    def post(self, request, pk=None, *args, **kwargs):
        case = WorkflowRecoveryCase.objects.filter(id=pk).first()
        if case is None:
            return response.Response({'error': 'Recovery case not found.'}, status=status.HTTP_404_NOT_FOUND)
        attempt = WorkflowFailureRecoveryEngine.run_retry_attempt(case)
        case.refresh_from_db()
        return response.Response(
            {
                'case': WorkflowRecoveryCaseSerializer(case).data,
                'attempt': WorkflowRetryAttemptSerializer(attempt).data,
            },
            status=status.HTTP_200_OK,
        )


class WorkflowRecoveryCaseEscalateView(APIView):
    """POST /api/v1/workflow-recovery/cases/{id}/escalate/"""

    def post(self, request, pk=None, *args, **kwargs):
        case = WorkflowRecoveryCase.objects.filter(id=pk).first()
        if case is None:
            return response.Response({'error': 'Recovery case not found.'}, status=status.HTTP_404_NOT_FOUND)
        reason = str((request.data or {}).get('reason', 'Escalated by API request'))
        case = WorkflowFailureRecoveryEngine.escalate_recovery_case(case, reason=reason)
        return response.Response(WorkflowRecoveryCaseSerializer(case).data, status=status.HTTP_200_OK)


class WorkflowRecoveryCaseManualResumeView(APIView):
    """POST /api/v1/workflow-recovery/cases/{id}/manual-resume/"""

    def post(self, request, pk=None, *args, **kwargs):
        case = WorkflowRecoveryCase.objects.filter(id=pk).first()
        if case is None:
            return response.Response({'error': 'Recovery case not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowRecoveryManualActionSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        case = WorkflowFailureRecoveryEngine.manual_resume(case, action_taken_by=ser.validated_data.get('action_taken_by', 'user'))
        return response.Response(WorkflowRecoveryCaseSerializer(case).data, status=status.HTTP_200_OK)


class WorkflowRecoveryCaseManualSkipView(APIView):
    """POST /api/v1/workflow-recovery/cases/{id}/manual-skip/"""

    def post(self, request, pk=None, *args, **kwargs):
        case = WorkflowRecoveryCase.objects.filter(id=pk).first()
        if case is None:
            return response.Response({'error': 'Recovery case not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowRecoveryManualActionSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        case = WorkflowFailureRecoveryEngine.manual_skip(case, action_taken_by=ser.validated_data.get('action_taken_by', 'user'))
        return response.Response(WorkflowRecoveryCaseSerializer(case).data, status=status.HTTP_200_OK)


class WorkflowRecoveryCaseManualFailView(APIView):
    """POST /api/v1/workflow-recovery/cases/{id}/manual-fail/"""

    def post(self, request, pk=None, *args, **kwargs):
        case = WorkflowRecoveryCase.objects.filter(id=pk).first()
        if case is None:
            return response.Response({'error': 'Recovery case not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowRecoveryManualActionSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        case = WorkflowFailureRecoveryEngine.manual_fail(case, action_taken_by=ser.validated_data.get('action_taken_by', 'user'))
        return response.Response(WorkflowRecoveryCaseSerializer(case).data, status=status.HTTP_200_OK)


class WorkflowConditionRuleListView(APIView):
    """GET/POST /api/v1/workflow-conditions/"""

    def get(self, request, *args, **kwargs):
        qs = WorkflowConditionRule.objects.all().order_by('priority', 'created_at')
        workflow_id = request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        stage_id = request.query_params.get('stage_id')
        if stage_id:
            qs = qs.filter(stage_id=stage_id)
        if request.query_params.get('active') == 'true':
            qs = qs.filter(is_active=True)
        return response.Response(WorkflowConditionRuleSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        ser = WorkflowConditionRuleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        record = ser.save()
        return response.Response(WorkflowConditionRuleSerializer(record).data, status=status.HTTP_201_CREATED)


class WorkflowConditionRuleDetailView(APIView):
    """GET/PUT /api/v1/workflow-conditions/{id}/"""

    def get(self, request, pk=None, *args, **kwargs):
        record = WorkflowConditionRule.objects.filter(id=pk).first()
        if not record:
            return response.Response({'error': 'Condition rule not found.'}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(WorkflowConditionRuleSerializer(record).data, status=status.HTTP_200_OK)

    def put(self, request, pk=None, *args, **kwargs):
        record = WorkflowConditionRule.objects.filter(id=pk).first()
        if not record:
            return response.Response({'error': 'Condition rule not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowConditionRuleSerializer(record, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        updated = ser.save()
        return response.Response(WorkflowConditionRuleSerializer(updated).data, status=status.HTTP_200_OK)


class WorkflowConditionGroupListView(APIView):
    """GET/POST /api/v1/workflow-condition-groups/"""

    def get(self, request, *args, **kwargs):
        qs = WorkflowConditionGroup.objects.all().order_by('-created_at')
        workflow_id = request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        stage_id = request.query_params.get('stage_id')
        if stage_id:
            qs = qs.filter(stage_id=stage_id)
        if request.query_params.get('active') == 'true':
            qs = qs.filter(is_active=True)
        return response.Response(WorkflowConditionGroupSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        ser = WorkflowConditionGroupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        record = ser.save()
        return response.Response(WorkflowConditionGroupSerializer(record).data, status=status.HTTP_201_CREATED)


class WorkflowConditionGroupDetailView(APIView):
    """GET/PUT /api/v1/workflow-condition-groups/{id}/"""

    def get(self, request, pk=None, *args, **kwargs):
        record = WorkflowConditionGroup.objects.filter(id=pk).first()
        if not record:
            return response.Response({'error': 'Condition group not found.'}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(WorkflowConditionGroupSerializer(record).data, status=status.HTTP_200_OK)

    def put(self, request, pk=None, *args, **kwargs):
        record = WorkflowConditionGroup.objects.filter(id=pk).first()
        if not record:
            return response.Response({'error': 'Condition group not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowConditionGroupSerializer(record, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        updated = ser.save()
        return response.Response(WorkflowConditionGroupSerializer(updated).data, status=status.HTTP_200_OK)


class WorkflowConditionGroupTestEvaluateView(APIView):
    """POST /api/v1/workflow-condition-groups/{id}/test-evaluate/"""

    def post(self, request, pk=None, *args, **kwargs):
        group = WorkflowConditionGroup.objects.filter(id=pk).first()
        if not group:
            return response.Response({'error': 'Condition group not found.'}, status=status.HTTP_404_NOT_FOUND)
        ser = WorkflowConditionGroupTestEvaluateSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        instance = WorkflowInstance.objects.filter(id=data['workflow_instance_id']).first()
        if instance is None:
            return response.Response({'error': 'Workflow instance not found.'}, status=status.HTTP_404_NOT_FOUND)
        stage_execution = None
        if data.get('stage_execution_id'):
            stage_execution = WorkflowStageExecution.objects.filter(id=data['stage_execution_id']).first()

        evaluation = WorkflowConditionalLogicEngine.evaluate_condition_group(
            workflow_instance=instance,
            stage_execution=stage_execution,
            group=group,
            context=data.get('context', {}),
            write_log=True,
        )
        transition_result = WorkflowConditionalLogicEngine.determine_transition_from_conditions(
            workflow_instance=instance,
            stage_execution=stage_execution,
            stage_id=group.stage_id,
            context=data.get('context', {}),
            write_log=False,
        )
        return response.Response(
            {
                'evaluation': evaluation,
                'selected_transition_id': str(transition_result['transition'].id) if transition_result else None,
                'selected_to_stage_id': str(transition_result['transition'].to_stage_id) if transition_result else None,
            },
            status=status.HTTP_200_OK,
        )


# ------------------------------------------------------------------ #
# Trigger Registry  (read-only)                                        #
# ------------------------------------------------------------------ #

class WorkflowTriggerRegistryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowEventDefinition.objects.all().order_by('module_scope', 'event_name')
    serializer_class = WorkflowTriggerRegistrySerializer

    def get_queryset(self):
        qs = self.queryset
        module = self.request.query_params.get('module_scope')
        if module:
            qs = qs.filter(module_scope=module)
        if self.request.query_params.get('active') == 'true':
            qs = qs.filter(is_active=True)
        return qs


# ------------------------------------------------------------------ #
# Trigger Mappings  (CRUD)                                             #
# ------------------------------------------------------------------ #

class WorkflowTriggerMappingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = WorkflowEventSubscription.objects.select_related('workflow', 'event_definition').all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return WorkflowTriggerMappingWriteSerializer
        return WorkflowTriggerMappingSerializer

    def get_queryset(self):
        qs = self.queryset
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        workflow_id = self.request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        return qs


# ------------------------------------------------------------------ #
# Event Logs  (read-only)                                              #
# ------------------------------------------------------------------ #

class WorkflowEventLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowEventLog.objects.all().order_by('-created_at')
    serializer_class = WorkflowEventLogSerializer

    def get_queryset(self):
        qs = self.queryset
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        event_key = self.request.query_params.get('event_key')
        if event_key:
            qs = qs.filter(event_key=event_key)
        s = self.request.query_params.get('status')
        if s:
            qs = qs.filter(status=s)
        return qs

    @action(detail=True, methods=['get'])
    def traces(self, request, pk=None):
        event_log = self.get_object()
        return response.Response(
            WorkflowEventDebugTraceSerializer(event_log.debug_traces.all(), many=True).data
        )


# ------------------------------------------------------------------ #
# Event Debug Traces  (read-only)                                      #
# ------------------------------------------------------------------ #

class WorkflowEventDebugTraceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowEventDebugTrace.objects.select_related('event_log', 'workflow').all()
    serializer_class = WorkflowEventDebugTraceSerializer

    def get_queryset(self):
        qs = self.queryset
        event_log_id = self.request.query_params.get('event_log_id')
        if event_log_id:
            qs = qs.filter(event_log_id=event_log_id)
        workflow_id = self.request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        return qs


# ------------------------------------------------------------------ #
# Test-emit                                                             #
# ------------------------------------------------------------------ #

class WorkflowTestEmitView(APIView):
    """POST /api/v1/workflow/events/test-emit/"""

    def post(self, request, *args, **kwargs):
        ser = TestEmitSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        event_log = WorkflowEventListener.receive_event(
            tenant_id=data['tenant_id'],
            event_key=data['event_key'],
            entity_type=data['entity_type'],
            entity_id=data['entity_id'],
            payload=data.get('payload', {}),
            source_module=data.get('source_module', 'test'),
        )

        traces = WorkflowEventDebugTrace.objects.filter(event_log=event_log)
        return response.Response(
            {
                'event_log': WorkflowEventLogSerializer(event_log).data,
                'traces':    WorkflowEventDebugTraceSerializer(traces, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


# ------------------------------------------------------------------ #
# Company external callbacks                                           #
# ------------------------------------------------------------------ #

class CompanyExternalCallbackBaseView(APIView):
    authentication_classes = []
    permission_classes = []
    callback_name = 'external-callback'
    resume_event = ''

    def _resolve_event_key(self, data):
        return self.resume_event

    def _resolve_scope(self, data):
        instance = None
        wait_state = None
        if data.get('workflow_instance_id'):
            instance = WorkflowInstance.objects.filter(
                id=data['workflow_instance_id'],
                tenant_id=data['tenant_id'],
            ).first()
        if data.get('wait_state_id'):
            wait_state = WorkflowWaitState.objects.select_related('workflow_instance').filter(
                id=data['wait_state_id'],
                workflow_instance__tenant_id=data['tenant_id'],
            ).first()
            if wait_state and instance is None:
                instance = wait_state.workflow_instance
        return instance, wait_state

    def _log_callback_timeline(self, *, instance, event_key, callback_reference, payload, resumed_ids):
        if instance is None:
            return
        WorkflowTimeline.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            event_type='transition',
            event_label=f'External callback received: {self.callback_name}',
            actor_type='event',
            occurred_at=timezone.now(),
            payload={
                'callback_name': self.callback_name,
                'resume_event': event_key,
                'callback_reference': callback_reference,
                'resumed_instance_ids': [str(i) for i in resumed_ids],
                'resumed_count': len(resumed_ids),
                'external_payload': payload or {},
            },
        )

    def post(self, request, *args, **kwargs):
        serializer = CompanyExternalCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        event_key = self._resolve_event_key(data)
        if not event_key:
            return response.Response(
                {'error': 'No resume event configured for callback.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance, wait_state = self._resolve_scope(data)
        if data.get('workflow_instance_id') and instance is None:
            return response.Response(
                {'error': 'workflow_instance_id not found for tenant.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if data.get('wait_state_id') and wait_state is None:
            return response.Response(
                {'error': 'wait_state_id not found for tenant.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        matching_wait_reasons = [reason for reason, events in WAIT_REASON_RESUME_EVENTS.items() if event_key in events]
        context = {
            'source': 'company_external_callback',
            'callback_name': self.callback_name,
            'callback_reference': data['callback_reference'],
            'resume_event': event_key,
            'payload': data.get('payload', {}),
            'actor_type': data.get('actor_type', 'external'),
            'actor_id': data.get('actor_id', ''),
        }

        resumed_ids = set()

        if wait_state:
            WorkflowStageEngine.resume_wait_state(
                wait_state_id=wait_state.id,
                triggered_by='event',
                context=context,
            )
            resumed_ids.add(wait_state.workflow_instance_id)
        elif instance:
            qs = instance.wait_states.filter(status='waiting').filter(
                Q(resume_event=event_key) | Q(workflow_instance__wait_reason__in=matching_wait_reasons)
            )
            for state in qs:
                WorkflowStageEngine.resume_wait_state(
                    wait_state_id=state.id,
                    triggered_by='event',
                    context=context,
                )
                resumed_ids.add(state.workflow_instance_id)
        else:
            resumed = WorkflowStageEngine.resume_by_event(
                event_key=event_key,
                tenant_id=data['tenant_id'],
                entity_type=(data.get('entity_type') or None),
                entity_id=data.get('entity_id'),
                context=context,
            )
            resumed_ids.update(resumed)

        self._log_callback_timeline(
            instance=instance,
            event_key=event_key,
            callback_reference=data['callback_reference'],
            payload=data.get('payload', {}),
            resumed_ids=resumed_ids,
        )

        return response.Response(
            {
                'callback': self.callback_name,
                'resume_event': event_key,
                'resumed_count': len(resumed_ids),
                'resumed_instance_ids': [str(i) for i in resumed_ids],
            },
            status=status.HTTP_200_OK,
        )


class CompanyAgencySubmissionCallbackView(CompanyExternalCallbackBaseView):
    callback_name = 'agency-submission'
    resume_event = 'client_feedback_received'


class CompanyAgencyCoordinationCallbackView(CompanyExternalCallbackBaseView):
    callback_name = 'agency-coordination-response'
    resume_event = 'interview_scheduled'


class CompanyCandidateResponseCallbackView(CompanyExternalCallbackBaseView):
    callback_name = 'candidate-response'

    def _resolve_event_key(self, data):
        payload = data.get('payload') or {}
        response_value = str(payload.get('response') or payload.get('decision') or '').strip().lower()
        if response_value == 'accepted':
            return 'offer_accepted'
        if response_value == 'rejected':
            return 'offer_rejected'
        return 'candidate_response_received'


class CompanyCandidateInterviewConfirmCallbackView(CompanyExternalCallbackBaseView):
    callback_name = 'candidate-interview-confirm'

    RESPONSE_EVENT_MAP = {
        'accepted': 'candidate_interview_confirmed',
        'declined': 'candidate_interview_declined',
        'reschedule-request': 'candidate_interview_reschedule_requested',
    }

    def post(self, request, *args, **kwargs):
        serializer = CompanyCandidateInterviewConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        interview = Interview.objects.filter(id=data['interview_id'], is_deleted=False).first()
        if interview is None:
            return response.Response(
                {'error': 'interview_id not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        callback_reference = (data.get('callback_reference') or '').strip()
        if not callback_reference:
            callback_reference = f"candidate-interview-confirm:{interview.id}"

        payload = dict(data.get('payload') or {})
        payload.setdefault('interview_id', str(interview.id))
        payload['response'] = data['response']
        if data.get('notes'):
            payload['notes'] = data['notes']

        upstream_data = {
            'tenant_id': str(data.get('tenant_id') or interview.tenant_id),
            'callback_reference': callback_reference,
            'workflow_instance_id': data.get('workflow_instance_id'),
            'wait_state_id': data.get('wait_state_id'),
            'entity_type': 'interview',
            'entity_id': str(interview.id),
            'actor_type': data.get('actor_type', 'external'),
            'actor_id': data.get('actor_id', ''),
            'payload': payload,
        }

        base_serializer = CompanyExternalCallbackSerializer(data=upstream_data)
        base_serializer.is_valid(raise_exception=True)
        validated = base_serializer.validated_data
        event_key = self.RESPONSE_EVENT_MAP[data['response']]

        instance, wait_state = self._resolve_scope(validated)
        if validated.get('workflow_instance_id') and instance is None:
            return response.Response(
                {'error': 'workflow_instance_id not found for tenant.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if validated.get('wait_state_id') and wait_state is None:
            return response.Response(
                {'error': 'wait_state_id not found for tenant.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        matching_wait_reasons = [reason for reason, events in WAIT_REASON_RESUME_EVENTS.items() if event_key in events]
        context = {
            'source': 'company_external_callback',
            'callback_name': self.callback_name,
            'callback_reference': validated['callback_reference'],
            'resume_event': event_key,
            'payload': validated.get('payload', {}),
            'actor_type': validated.get('actor_type', 'external'),
            'actor_id': validated.get('actor_id', ''),
        }

        resumed_ids = set()
        if wait_state:
            WorkflowStageEngine.resume_wait_state(
                wait_state_id=wait_state.id,
                triggered_by='event',
                context=context,
            )
            resumed_ids.add(wait_state.workflow_instance_id)
        elif instance:
            qs = instance.wait_states.filter(status='waiting').filter(
                Q(resume_event=event_key) | Q(workflow_instance__wait_reason__in=matching_wait_reasons)
            )
            for state in qs:
                WorkflowStageEngine.resume_wait_state(
                    wait_state_id=state.id,
                    triggered_by='event',
                    context=context,
                )
                resumed_ids.add(state.workflow_instance_id)
        else:
            resumed = WorkflowStageEngine.resume_by_event(
                event_key=event_key,
                tenant_id=validated['tenant_id'],
                entity_type='interview',
                entity_id=interview.id,
                context=context,
            )
            resumed_ids.update(resumed)

        self._log_callback_timeline(
            instance=instance,
            event_key=event_key,
            callback_reference=validated['callback_reference'],
            payload=validated.get('payload', {}),
            resumed_ids=resumed_ids,
        )

        return response.Response(
            {
                'callback': self.callback_name,
                'resume_event': event_key,
                'response': data['response'],
                'resumed_count': len(resumed_ids),
                'resumed_instance_ids': [str(i) for i in resumed_ids],
            },
            status=status.HTTP_200_OK,
        )


class CompanyCandidateOfferResponseCallbackView(CompanyExternalCallbackBaseView):
    callback_name = 'candidate-offer-response'

    RESPONSE_EVENT_MAP = {
        'accepted': 'offer_accepted',
        'rejected': 'offer_rejected',
        'counter': 'offer_counter_received',
    }

    def post(self, request, *args, **kwargs):
        serializer = CompanyCandidateOfferResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        offer = OfferLetter.objects.filter(id=data['offer_id'], is_deleted=False).first()
        if offer is None:
            return response.Response(
                {'error': 'offer_id not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        callback_reference = (data.get('callback_reference') or '').strip()
        if not callback_reference:
            callback_reference = f"candidate-offer-response:{offer.id}"

        payload = dict(data.get('payload') or {})
        payload.setdefault('offer_id', str(offer.id))
        payload['response'] = data['response']
        if data.get('counter_salary') is not None:
            payload['counter_salary'] = str(data['counter_salary'])
        if data.get('notes'):
            payload['notes'] = data['notes']

        upstream_data = {
            'tenant_id': str(data.get('tenant_id') or offer.tenant_id),
            'callback_reference': callback_reference,
            'workflow_instance_id': data.get('workflow_instance_id'),
            'wait_state_id': data.get('wait_state_id'),
            'entity_type': 'application',
            'entity_id': str(offer.application_id),
            'actor_type': data.get('actor_type', 'external'),
            'actor_id': data.get('actor_id', ''),
            'payload': payload,
        }

        base_serializer = CompanyExternalCallbackSerializer(data=upstream_data)
        base_serializer.is_valid(raise_exception=True)
        validated = base_serializer.validated_data
        event_key = self.RESPONSE_EVENT_MAP[data['response']]

        self._apply_offer_response(offer=offer, data=data, request=request)

        instance, wait_state = self._resolve_scope(validated)
        if validated.get('workflow_instance_id') and instance is None:
            return response.Response(
                {'error': 'workflow_instance_id not found for tenant.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if validated.get('wait_state_id') and wait_state is None:
            return response.Response(
                {'error': 'wait_state_id not found for tenant.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        matching_wait_reasons = [reason for reason, events_list in WAIT_REASON_RESUME_EVENTS.items() if event_key in events_list]
        context = {
            'source': 'company_external_callback',
            'callback_name': self.callback_name,
            'callback_reference': validated['callback_reference'],
            'resume_event': event_key,
            'payload': validated.get('payload', {}),
            'actor_type': validated.get('actor_type', 'external'),
            'actor_id': validated.get('actor_id', ''),
        }

        resumed_ids = set()
        if wait_state:
            WorkflowStageEngine.resume_wait_state(
                wait_state_id=wait_state.id,
                triggered_by='event',
                context=context,
            )
            resumed_ids.add(wait_state.workflow_instance_id)
        elif instance:
            qs = instance.wait_states.filter(status='waiting').filter(
                Q(resume_event=event_key) | Q(workflow_instance__wait_reason__in=matching_wait_reasons)
            )
            for state in qs:
                WorkflowStageEngine.resume_wait_state(
                    wait_state_id=state.id,
                    triggered_by='event',
                    context=context,
                )
                resumed_ids.add(state.workflow_instance_id)
        else:
            resumed = WorkflowStageEngine.resume_by_event(
                event_key=event_key,
                tenant_id=validated['tenant_id'],
                entity_type='application',
                entity_id=offer.application_id,
                context=context,
            )
            resumed_ids.update(resumed)

        self._log_callback_timeline(
            instance=instance,
            event_key=event_key,
            callback_reference=validated['callback_reference'],
            payload=validated.get('payload', {}),
            resumed_ids=resumed_ids,
        )

        return response.Response(
            {
                'callback': self.callback_name,
                'resume_event': event_key,
                'response': data['response'],
                'resumed_count': len(resumed_ids),
                'resumed_instance_ids': [str(i) for i in resumed_ids],
            },
            status=status.HTTP_200_OK,
        )

    def _apply_offer_response(self, *, offer, data, request):
        now = timezone.now()
        response_value = data['response']
        update_fields = ['status', 'updated_at']

        metadata = dict(offer.metadata or {})
        if response_value == 'accepted':
            offer.status = 'accepted'
            offer.accepted_at = now
            update_fields.append('accepted_at')
            events.offer.accepted.send(sender=self.__class__, application=_offer_application_proxy(offer))
            self._ensure_onboarding_for_offer(offer=offer, accepted_at=now)
        elif response_value == 'rejected':
            offer.status = 'rejected'
            offer.rejected_at = now
            if data.get('notes'):
                offer.rejection_reason = data['notes']
                update_fields.append('rejection_reason')
            update_fields.append('rejected_at')
            events.offer.rejected.send(sender=self.__class__, application=_offer_application_proxy(offer))
        else:
            offer.status = 'negotiation'
            negotiation = dict(metadata.get('negotiation') or {})
            rounds = list(negotiation.get('rounds') or [])
            next_round = len(rounds) + 1
            rounds.append(
                {
                    'round': next_round,
                    'counter_salary': str(data.get('counter_salary') or ''),
                    'notes': data.get('notes', ''),
                    'source': 'external_candidate_response',
                    'updated_at': now.isoformat(),
                }
            )
            negotiation['rounds'] = rounds
            negotiation['latest_counter_salary'] = str(data.get('counter_salary') or '')
            negotiation['latest_notes'] = data.get('notes', '')
            metadata['negotiation'] = negotiation
            offer.metadata = metadata
            update_fields.append('metadata')

        offer.save(update_fields=update_fields)
        self._sync_application_from_offer(offer=offer, response_value=response_value, actor_id=data.get('actor_id') or '')

    def _ensure_onboarding_for_offer(self, *, offer, accepted_at):
        app = Application.objects.filter(
            id=offer.application_id,
            tenant_id=offer.tenant_id,
            is_deleted=False,
        ).first()
        if not app:
            return

        HDCOperationalService.ensure_onboarding_case(
            tenant_id=offer.tenant_id,
            application_id=offer.application_id,
            candidate_id=offer.candidate_id or app.candidate_id,
            job_id=getattr(app, 'requisition_id', None),
            offer_id=offer.id,
            joining_date=offer.joining_date or getattr(app, 'joining_date', None),
            accepted_at=accepted_at,
        )

    def _sync_application_from_offer(self, *, offer, response_value, actor_id):
        application = Application.objects.filter(id=offer.application_id, tenant_id=offer.tenant_id, is_deleted=False).first()
        if not application:
            return

        old_status = application.status
        app_fields = ['updated_at']
        if offer.offered_salary is not None:
            application.offer_amount = offer.offered_salary
            app_fields.append('offer_amount')
        if offer.currency:
            application.offer_currency = offer.currency
            app_fields.append('offer_currency')
        if offer.sent_at:
            application.offer_date = offer.sent_at.date()
            app_fields.append('offer_date')
        if offer.joining_date:
            application.joining_date = offer.joining_date
            app_fields.append('joining_date')

        if response_value == 'accepted':
            application.offer_accepted_at = timezone.now()
            app_fields.append('offer_accepted_at')
            application.status = 'offer'
            app_fields.append('status')
        elif response_value == 'rejected':
            application.offer_rejected_at = timezone.now()
            application.status = 'rejected'
            app_fields.extend(['offer_rejected_at', 'status'])
        else:
            application.status = 'offer'
            app_fields.append('status')
            metadata = dict(application.metadata or {})
            metadata['offer_negotiation'] = {
                'counter_salary': str(offer.metadata.get('negotiation', {}).get('latest_counter_salary', '')),
                'notes': offer.metadata.get('negotiation', {}).get('latest_notes', ''),
                'updated_at': timezone.now().isoformat(),
            }
            application.metadata = metadata
            app_fields.append('metadata')

        application.save(update_fields=app_fields)
        ApplicationStageHistory.objects.create(
            tenant_id=offer.tenant_id,
            application_id=application.id,
            from_stage_id=application.current_stage_id,
            to_stage_id=application.current_stage_id,
            from_status=old_status,
            to_status=application.status,
            moved_by=_safe_uuid(actor_id),
            reason=f'Offer response: {response_value}',
            notes=f'Offer {offer.id} external response received.',
        )


def _offer_application_proxy(offer):
    return type(
        'OfferApplicationProxy',
        (),
        {
            'id': offer.application_id,
            'tenant_id': offer.tenant_id,
            'candidate_id': offer.candidate_id,
        },
    )()


def _safe_uuid(value):
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except Exception:
        return None


class CompanyCandidateDocumentSignedCallbackView(CompanyExternalCallbackBaseView):
    callback_name = 'candidate-document-signed'
    resume_event = 'document_signed'


class CompanyCandidateDocumentUploadedCallbackView(CompanyExternalCallbackBaseView):
    callback_name = 'candidate-document-uploaded'
    resume_event = 'document_signed'

    def post(self, request, *args, **kwargs):
        serializer = CompanyCandidateDocumentUploadedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        joining_case = JoiningCase.objects.filter(id=data['onboarding_id'], is_deleted=False).first()
        if joining_case is None:
            return response.Response(
                {'error': 'onboarding_id not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        callback_reference = (data.get('callback_reference') or '').strip()
        if not callback_reference:
            callback_reference = f"candidate-document-uploaded:{joining_case.id}"

        payload = dict(data.get('payload') or {})
        payload.update(
            {
                'onboarding_id': str(joining_case.id),
                'document_type': data['document_type'],
                'document_status': data['document_status'],
                'notes': data.get('notes', ''),
            }
        )

        metadata = dict(joining_case.metadata or {})
        documents = dict(metadata.get('documents') or {})
        documents[data['document_type']] = {
            'status': data['document_status'],
            'notes': data.get('notes', ''),
            'updated_at': timezone.now().isoformat(),
        }
        metadata['documents'] = documents

        checklist = list(metadata.get('checklist') or [])
        for item in checklist:
            if str(item.get('task_name') or '').lower() == 'documents received':
                if str(data['document_status']).lower() in {'uploaded', 'received', 'verified', 'completed'}:
                    item['status'] = 'completed'
                else:
                    item['status'] = 'in_progress'
        metadata['checklist'] = checklist

        if str(data['document_status']).lower() in {'uploaded', 'received', 'verified', 'completed'}:
            if joining_case.status in {'pending', 'documents_pending'}:
                joining_case.status = 'in_progress'
        else:
            joining_case.status = 'documents_pending'
        joining_case.metadata = metadata
        joining_case.save(update_fields=['status', 'metadata', 'updated_at'])

        base_payload = {
            'tenant_id': str(data.get('tenant_id') or joining_case.tenant_id),
            'callback_reference': callback_reference,
            'workflow_instance_id': data.get('workflow_instance_id'),
            'wait_state_id': data.get('wait_state_id'),
            'entity_type': 'application',
            'entity_id': str(joining_case.application_id),
            'actor_type': data.get('actor_type', 'external'),
            'actor_id': data.get('actor_id', ''),
            'payload': payload,
        }
        base_serializer = CompanyExternalCallbackSerializer(data=base_payload)
        base_serializer.is_valid(raise_exception=True)
        validated = base_serializer.validated_data
        event_key = self._resolve_event_key(validated)

        instance, wait_state = self._resolve_scope(validated)
        if validated.get('workflow_instance_id') and instance is None:
            return response.Response(
                {'error': 'workflow_instance_id not found for tenant.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if validated.get('wait_state_id') and wait_state is None:
            return response.Response(
                {'error': 'wait_state_id not found for tenant.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        matching_wait_reasons = [reason for reason, events_list in WAIT_REASON_RESUME_EVENTS.items() if event_key in events_list]
        context = {
            'source': 'company_external_callback',
            'callback_name': self.callback_name,
            'callback_reference': validated['callback_reference'],
            'resume_event': event_key,
            'payload': validated.get('payload', {}),
            'actor_type': validated.get('actor_type', 'external'),
            'actor_id': validated.get('actor_id', ''),
        }

        resumed_ids = set()
        if wait_state:
            WorkflowStageEngine.resume_wait_state(
                wait_state_id=wait_state.id,
                triggered_by='event',
                context=context,
            )
            resumed_ids.add(wait_state.workflow_instance_id)
        elif instance:
            qs = instance.wait_states.filter(status='waiting').filter(
                Q(resume_event=event_key) | Q(workflow_instance__wait_reason__in=matching_wait_reasons)
            )
            for state in qs:
                WorkflowStageEngine.resume_wait_state(
                    wait_state_id=state.id,
                    triggered_by='event',
                    context=context,
                )
                resumed_ids.add(state.workflow_instance_id)
        else:
            resumed = WorkflowStageEngine.resume_by_event(
                event_key=event_key,
                tenant_id=validated['tenant_id'],
                entity_type='application',
                entity_id=joining_case.application_id,
                context=context,
            )
            resumed_ids.update(resumed)

        self._log_callback_timeline(
            instance=instance,
            event_key=event_key,
            callback_reference=validated['callback_reference'],
            payload=validated.get('payload', {}),
            resumed_ids=resumed_ids,
        )
        return response.Response(
            {
                'callback': self.callback_name,
                'resume_event': event_key,
                'resumed_count': len(resumed_ids),
                'resumed_instance_ids': [str(i) for i in resumed_ids],
            },
            status=status.HTTP_200_OK,
        )


class CompanyHRMSHandoffCallbackView(CompanyExternalCallbackBaseView):
    callback_name = 'hrms-handoff'
    resume_event = 'hrms_handoff_acknowledged'

    def _resolve_event_key(self, data):
        payload = data.get('payload') or {}
        handoff_status = str(payload.get('status') or '').strip().lower()
        if handoff_status == 'rejected':
            return 'hrms_handoff_rejected'
        return self.resume_event

    def post(self, request, *args, **kwargs):
        serializer = CompanyHRMSHandoffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        joining_case = JoiningCase.objects.filter(id=data['onboarding_id'], is_deleted=False).first()
        if joining_case is None:
            return response.Response(
                {'error': 'onboarding_id not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        callback_reference = (data.get('callback_reference') or '').strip()
        if not callback_reference:
            callback_reference = f"hrms-handoff:{joining_case.id}"

        payload = dict(data.get('payload') or {})
        payload.update(
            {
                'onboarding_id': str(joining_case.id),
                'status': data['status'],
                'notes': data.get('notes', ''),
            }
        )

        metadata = dict(joining_case.metadata or {})
        metadata['hrms_handoff'] = {
            'status': data['status'],
            'notes': data.get('notes', ''),
            'updated_at': timezone.now().isoformat(),
            'callback_reference': callback_reference,
        }
        joining_case.metadata = metadata
        joining_case.status = 'handed_off' if data['status'] == 'acknowledged' else 'completed'
        joining_case.save(update_fields=['status', 'metadata', 'updated_at'])

        base_payload = {
            'tenant_id': str(data.get('tenant_id') or joining_case.tenant_id),
            'callback_reference': callback_reference,
            'workflow_instance_id': data.get('workflow_instance_id'),
            'wait_state_id': data.get('wait_state_id'),
            'entity_type': 'application',
            'entity_id': str(joining_case.application_id),
            'actor_type': data.get('actor_type', 'external'),
            'actor_id': data.get('actor_id', ''),
            'payload': payload,
        }
        base_serializer = CompanyExternalCallbackSerializer(data=base_payload)
        base_serializer.is_valid(raise_exception=True)
        validated = base_serializer.validated_data
        return self._resume_from_payload(validated)

    def _resume_from_payload(self, validated):
        event_key = self._resolve_event_key(validated)
        instance, wait_state = self._resolve_scope(validated)
        if validated.get('workflow_instance_id') and instance is None:
            return response.Response(
                {'error': 'workflow_instance_id not found for tenant.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if validated.get('wait_state_id') and wait_state is None:
            return response.Response(
                {'error': 'wait_state_id not found for tenant.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        matching_wait_reasons = [reason for reason, events_list in WAIT_REASON_RESUME_EVENTS.items() if event_key in events_list]
        context = {
            'source': 'company_external_callback',
            'callback_name': self.callback_name,
            'callback_reference': validated['callback_reference'],
            'resume_event': event_key,
            'payload': validated.get('payload', {}),
            'actor_type': validated.get('actor_type', 'external'),
            'actor_id': validated.get('actor_id', ''),
        }

        resumed_ids = set()
        if wait_state:
            WorkflowStageEngine.resume_wait_state(
                wait_state_id=wait_state.id,
                triggered_by='event',
                context=context,
            )
            resumed_ids.add(wait_state.workflow_instance_id)
        elif instance:
            qs = instance.wait_states.filter(status='waiting').filter(
                Q(resume_event=event_key) | Q(workflow_instance__wait_reason__in=matching_wait_reasons)
            )
            for state in qs:
                WorkflowStageEngine.resume_wait_state(
                    wait_state_id=state.id,
                    triggered_by='event',
                    context=context,
                )
                resumed_ids.add(state.workflow_instance_id)
        else:
            resumed = WorkflowStageEngine.resume_by_event(
                event_key=event_key,
                tenant_id=validated['tenant_id'],
                entity_type=(validated.get('entity_type') or None),
                entity_id=validated.get('entity_id'),
                context=context,
            )
            resumed_ids.update(resumed)

        self._log_callback_timeline(
            instance=instance,
            event_key=event_key,
            callback_reference=validated['callback_reference'],
            payload=validated.get('payload', {}),
            resumed_ids=resumed_ids,
        )
        return response.Response(
            {
                'callback': self.callback_name,
                'resume_event': event_key,
                'resumed_count': len(resumed_ids),
                'resumed_instance_ids': [str(i) for i in resumed_ids],
            },
            status=status.HTTP_200_OK,
        )


class CompanyHRMSHandoffAckCallbackView(CompanyExternalCallbackBaseView):
    callback_name = 'hrms-handoff-ack'
    resume_event = 'hrms_handoff_acknowledged'


# ------------------------------------------------------------------ #
# Entity Routes  (read-only + complete/fail actions)                   #
# ------------------------------------------------------------------ #

class WorkflowEntityRouteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/v1/workflow/entity-routes/
    GET  /api/v1/workflow/entity-routes/{id}/
    POST /api/v1/workflow/entity-routes/{id}/complete/
    POST /api/v1/workflow/entity-routes/{id}/fail/
    """
    queryset = WorkflowEntityRoute.objects.select_related('workflow_instance').all()
    serializer_class = WorkflowEntityRouteSerializer

    def get_queryset(self):
        qs = self.queryset
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        instance_id = self.request.query_params.get('workflow_instance_id')
        if instance_id:
            qs = qs.filter(workflow_instance_id=instance_id)
        route_status = self.request.query_params.get('status')
        if route_status:
            qs = qs.filter(status=route_status)
        to_entity_type = self.request.query_params.get('to_entity_type')
        if to_entity_type:
            qs = qs.filter(to_entity_type=to_entity_type)
        return qs

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """POST /api/v1/workflow/entity-routes/{id}/complete/"""
        route = self.get_object()
        if route.status in ('completed', 'cancelled', 'failed'):
            return response.Response(
                {'error': f'Route is already {route.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        route.complete()
        return response.Response(WorkflowEntityRouteSerializer(route).data)

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """POST /api/v1/workflow/entity-routes/{id}/fail/"""
        route = self.get_object()
        reason = request.data.get('reason', '')
        route.fail(reason=reason)
        return response.Response(WorkflowEntityRouteSerializer(route).data)


# ------------------------------------------------------------------ #
# Actor Assignments  (read-only + revoke action)                       #
# ------------------------------------------------------------------ #

class WorkflowActorAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/v1/workflow/actor-assignments/
    GET  /api/v1/workflow/actor-assignments/{id}/
    POST /api/v1/workflow/actor-assignments/{id}/revoke/
    """
    queryset = WorkflowActorAssignment.objects.select_related('workflow_instance').all()
    serializer_class = WorkflowActorAssignmentSerializer

    def get_queryset(self):
        qs = self.queryset
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        instance_id = self.request.query_params.get('workflow_instance_id')
        if instance_id:
            qs = qs.filter(workflow_instance_id=instance_id)
        stage_id = self.request.query_params.get('stage_id')
        if stage_id:
            qs = qs.filter(stage_id=stage_id)
        actor_type = self.request.query_params.get('actor_type')
        if actor_type:
            qs = qs.filter(actor_type=actor_type)
        assignment_status = self.request.query_params.get('status')
        if assignment_status:
            qs = qs.filter(status=assignment_status)
        return qs

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """POST /api/v1/workflow/actor-assignments/{id}/revoke/"""
        assignment = self.get_object()
        assignment.revoke()
        return response.Response(WorkflowActorAssignmentSerializer(assignment).data)


# ------------------------------------------------------------------ #
# Handoff Checkpoints  (read-only + acknowledge/complete/fail actions) #
# ------------------------------------------------------------------ #

class WorkflowHandoffCheckpointViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/v1/workflow/handoff-checkpoints/
    GET  /api/v1/workflow/handoff-checkpoints/{id}/
    POST /api/v1/workflow/handoff-checkpoints/{id}/acknowledge/
    POST /api/v1/workflow/handoff-checkpoints/{id}/complete/
    POST /api/v1/workflow/handoff-checkpoints/{id}/fail/
    """
    queryset = WorkflowHandoffCheckpoint.objects.select_related(
        'workflow_instance', 'stage_execution'
    ).all()
    serializer_class = WorkflowHandoffCheckpointSerializer

    def get_queryset(self):
        qs = self.queryset
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        instance_id = self.request.query_params.get('workflow_instance_id')
        if instance_id:
            qs = qs.filter(workflow_instance_id=instance_id)
        checkpoint_status = self.request.query_params.get('status')
        if checkpoint_status:
            qs = qs.filter(status=checkpoint_status)
        handoff_type = self.request.query_params.get('handoff_type')
        if handoff_type:
            qs = qs.filter(handoff_type=handoff_type)
        return qs

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """POST /api/v1/workflow/handoff-checkpoints/{id}/acknowledge/"""
        checkpoint = self.get_object()
        ser = AcknowledgeHandoffSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        checkpoint.acknowledge(response_payload=ser.validated_data.get('response_payload'))
        return response.Response(WorkflowHandoffCheckpointSerializer(checkpoint).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """POST /api/v1/workflow/handoff-checkpoints/{id}/complete/"""
        checkpoint = self.get_object()
        ser = CompleteHandoffSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        completed_checkpoint = WorkflowCrossEntityRoutingEngine.complete_handoff(
            checkpoint_id=checkpoint.id,
            response_payload=data.get('response_payload', {}),
            triggered_by=data.get('triggered_by', 'system'),
            actor_id=data.get('actor_id'),
        )
        if completed_checkpoint is None:
            return response.Response(
                {'error': 'Checkpoint not found or already completed.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return response.Response(WorkflowHandoffCheckpointSerializer(completed_checkpoint).data)

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """POST /api/v1/workflow/handoff-checkpoints/{id}/fail/"""
        checkpoint = self.get_object()
        reason = request.data.get('reason', '')
        result = WorkflowCrossEntityRoutingEngine.fail_handoff(
            checkpoint_id=checkpoint.id,
            reason=reason,
        )
        if result is None:
            return response.Response(
                {'error': 'Checkpoint not found or already in terminal state.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return response.Response(WorkflowHandoffCheckpointSerializer(result).data)


# ------------------------------------------------------------------ #
# Routing Rules  (CRUD)                                                #
# ------------------------------------------------------------------ #

class WorkflowRoutingRuleViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET    /api/v1/workflow/routing-rules/
    POST   /api/v1/workflow/routing-rules/
    GET    /api/v1/workflow/routing-rules/{id}/
    PUT    /api/v1/workflow/routing-rules/{id}/
    PATCH  /api/v1/workflow/routing-rules/{id}/
    DELETE /api/v1/workflow/routing-rules/{id}/
    """
    queryset = WorkflowRoutingRule.objects.all()
    serializer_class = WorkflowRoutingRuleSerializer

    def get_queryset(self):
        qs = self.queryset
        workflow_id = self.request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        stage_id = self.request.query_params.get('stage_id')
        if stage_id:
            qs = qs.filter(stage_id=stage_id)
        entity_type = self.request.query_params.get('route_to_entity_type')
        if entity_type:
            qs = qs.filter(route_to_entity_type=entity_type)
        if self.request.query_params.get('active') == 'true':
            qs = qs.filter(is_active=True)
        return qs


# ------------------------------------------------------------------ #
# Route Timeline Logs  (read-only)                                     #
# ------------------------------------------------------------------ #

class WorkflowRouteTimelineLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/workflow/route-timeline/
    GET /api/v1/workflow/route-timeline/{id}/
    """
    queryset = WorkflowRouteTimelineLog.objects.select_related(
        'workflow_instance', 'route'
    ).all()
    serializer_class = WorkflowRouteTimelineLogSerializer

    def get_queryset(self):
        qs = self.queryset
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        instance_id = self.request.query_params.get('workflow_instance_id')
        if instance_id:
            qs = qs.filter(workflow_instance_id=instance_id)
        route_id = self.request.query_params.get('route_id')
        if route_id:
            qs = qs.filter(route_id=route_id)
        return qs
