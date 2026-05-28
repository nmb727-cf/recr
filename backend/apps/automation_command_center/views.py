from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import error_response, success_response
from apps.orchestration_center.models import (
    AISuggestion,
    Workflow,
    WorkflowExecution,
)
from apps.orchestration_center.constants.execution_statuses import SuggestionStatus

from .permissions import CanAdmin, CanManage, CanView


def _tenant(request):
    return request.user.tenant_id


def _today_start():
    now = timezone.now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# GET /api/v1/automation-center/overview/
# ---------------------------------------------------------------------------
class OverviewView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tenant(request)
        today = _today_start()

        active_workflows = Workflow.objects.filter(tenant_id=tid, status='active', is_deleted=False).count()

        executions_today_qs = WorkflowExecution.objects.filter(
            tenant_id=tid, started_at__gte=today
        )
        executions_today = executions_today_qs.count()
        successes_today = executions_today_qs.filter(status='completed').count()
        failures_today = executions_today_qs.filter(status='failed').count()

        success_rate = round((successes_today / executions_today * 100), 1) if executions_today else 0.0

        total_workflows = Workflow.objects.filter(tenant_id=tid, is_deleted=False).count()
        workflows_with_executions = (
            Workflow.objects.filter(
                tenant_id=tid, is_deleted=False, executions__started_at__gte=today
            )
            .distinct()
            .count()
        )
        automation_coverage = (
            round(workflows_with_executions / total_workflows * 100, 1) if total_workflows else 0.0
        )

        # Estimated hours saved: each completed execution saves ~3 minutes on average
        hours_saved = round(successes_today * 3 / 60, 1)

        return success_response(
            data={
                'active_workflows': active_workflows,
                'executions_today': executions_today,
                'success_rate': success_rate,
                'failures_today': failures_today,
                'automation_coverage': automation_coverage,
                'hours_saved': hours_saved,
            },
            message='Overview retrieved.',
        )


# ---------------------------------------------------------------------------
# GET /api/v1/automation-center/workflows/
# ---------------------------------------------------------------------------
class WorkflowListView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tenant(request)
        today = _today_start()

        search = request.query_params.get('search', '').strip()
        module = request.query_params.get('module', '').strip()
        wf_status = request.query_params.get('status', '').strip()
        trigger = request.query_params.get('trigger', '').strip()
        priority = request.query_params.get('priority', '').strip()

        qs = Workflow.objects.filter(tenant_id=tid, is_deleted=False).prefetch_related('executions')

        if search:
            qs = qs.filter(name__icontains=search)
        if wf_status:
            qs = qs.filter(status=wf_status)
        if trigger:
            qs = qs.filter(trigger_event__icontains=trigger)
        if priority:
            qs = qs.filter(priority=priority)

        results = []
        for wf in qs:
            today_execs = wf.executions.filter(started_at__gte=today)
            total_today = today_execs.count()
            success_today = today_execs.filter(status='completed').count()
            last_exec = wf.executions.order_by('-started_at').first()
            results.append({
                'id': str(wf.id),
                'name': wf.name,
                'trigger': wf.trigger_event,
                'status': wf.status,
                'priority': wf.priority,
                'executions_today': total_today,
                'success_rate': round(success_today / total_today * 100, 1) if total_today else 0.0,
                'last_run': last_exec.started_at.isoformat() if last_exec else None,
                'is_critical': wf.is_critical,
                'require_approval': wf.require_approval,
            })

        return success_response(data=results, message='Workflows retrieved.')


# ---------------------------------------------------------------------------
# GET /api/v1/automation-center/activity/
# ---------------------------------------------------------------------------
class ActivityFeedView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tenant(request)
        limit = min(int(request.query_params.get('limit', 50)), 200)

        executions = (
            WorkflowExecution.objects.filter(tenant_id=tid)
            .select_related('workflow')
            .order_by('-started_at')[:limit]
        )

        events = []
        for ex in executions:
            events.append({
                'id': str(ex.id),
                'time': ex.started_at.isoformat(),
                'workflow_name': ex.workflow.name,
                'action': ex.workflow.trigger_event,
                'entity_type': ex.entity_type,
                'entity_id': ex.entity_id,
                'status': ex.status,
            })

        return success_response(data=events, message='Activity feed retrieved.')


# ---------------------------------------------------------------------------
# GET /api/v1/automation-center/ai-suggestions/
# ---------------------------------------------------------------------------
class AISuggestionsView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tenant(request)

        suggestions = AISuggestion.objects.filter(
            tenant_id=tid,
            status=SuggestionStatus.PENDING,
        ).order_by('-created_at')[:20]

        results = [
            {
                'id': str(s.id),
                'title': s.title,
                'summary': s.summary,
                'category': s.category,
                'confidence_score': float(s.confidence_score) if s.confidence_score else None,
                'confidence_band': s.confidence_band,
                'source_module': s.source_module,
                'created_at': s.created_at.isoformat(),
            }
            for s in suggestions
        ]

        return success_response(data=results, message='AI suggestions retrieved.')


# ---------------------------------------------------------------------------
# GET /api/v1/automation-center/health/
# ---------------------------------------------------------------------------
class HealthView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tenant(request)
        today = _today_start()

        failing = (
            Workflow.objects.filter(tenant_id=tid, is_deleted=False)
            .filter(executions__status='failed', executions__started_at__gte=today)
            .distinct()
            .count()
        )
        paused = Workflow.objects.filter(tenant_id=tid, status='paused', is_deleted=False).count()

        # Conflicts: workflows with same trigger event (potential overlap)
        from django.db.models import Count
        conflicts = (
            Workflow.objects.filter(tenant_id=tid, is_deleted=False, status='active')
            .values('trigger_event')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)
            .count()
        )

        # Delayed: running executions older than 30 minutes
        threshold = timezone.now() - timezone.timedelta(minutes=30)
        delays = WorkflowExecution.objects.filter(
            tenant_id=tid, status='running', started_at__lt=threshold
        ).count()

        return success_response(
            data={
                'failing_workflows': failing,
                'paused_workflows': paused,
                'conflicts_detected': conflicts,
                'execution_delays': delays,
            },
            message='Health data retrieved.',
        )


# ---------------------------------------------------------------------------
# GET /api/v1/automation-center/executions/
# ---------------------------------------------------------------------------
class ExecutionMonitorView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tenant(request)

        qs = (
            WorkflowExecution.objects.filter(tenant_id=tid, status='running')
            .select_related('workflow')
            .order_by('-started_at')[:100]
        )

        now = timezone.now()
        results = []
        for ex in qs:
            duration_s = int((now - ex.started_at).total_seconds())
            results.append({
                'id': str(ex.id),
                'workflow': ex.workflow.name,
                'entity_type': ex.entity_type,
                'entity_id': ex.entity_id,
                'step': len(ex.execution_trace),
                'started_at': ex.started_at.isoformat(),
                'duration_seconds': duration_s,
                'status': ex.status,
            })

        return success_response(data=results, message='Running executions retrieved.')


# ---------------------------------------------------------------------------
# POST /api/v1/automation-center/pause-all/
# ---------------------------------------------------------------------------
class PauseAllView(APIView):
    permission_classes = [IsAuthenticated, CanAdmin]

    def post(self, request):
        tid = _tenant(request)
        updated = Workflow.objects.filter(
            tenant_id=tid, status='active', is_deleted=False
        ).update(status='paused')
        return success_response(
            data={'paused_count': updated},
            message=f'{updated} workflow(s) paused.',
        )


# ---------------------------------------------------------------------------
# POST /api/v1/automation-center/resume-all/
# ---------------------------------------------------------------------------
class ResumeAllView(APIView):
    permission_classes = [IsAuthenticated, CanAdmin]

    def post(self, request):
        tid = _tenant(request)
        updated = Workflow.objects.filter(
            tenant_id=tid, status='paused', is_deleted=False
        ).update(status='active')
        return success_response(
            data={'resumed_count': updated},
            message=f'{updated} workflow(s) resumed.',
        )


# ---------------------------------------------------------------------------
# POST /api/v1/automation-center/emergency-stop/
# ---------------------------------------------------------------------------
class EmergencyStopView(APIView):
    permission_classes = [IsAuthenticated, CanAdmin]

    def post(self, request):
        tid = _tenant(request)

        # Deactivate all active and paused workflows
        deactivated = Workflow.objects.filter(
            tenant_id=tid,
            status__in=['active', 'paused'],
            is_deleted=False,
        ).update(status='archived', is_active=False)

        # Mark all running executions as failed
        stopped_executions = WorkflowExecution.objects.filter(
            tenant_id=tid, status='running'
        ).update(status='failed', completed_at=timezone.now())

        return success_response(
            data={
                'deactivated_workflows': deactivated,
                'stopped_executions': stopped_executions,
            },
            message='Emergency stop applied. All workflows deactivated.',
        )


# ---------------------------------------------------------------------------
# GET /api/v1/automation-center/learning-summary/
# ---------------------------------------------------------------------------
class LearningSummaryView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        from apps.automation_learning.automation_self_learning_engine import AutomationSelfLearningEngine
        from apps.automation_learning.models import (
            AutomationOptimizationSuggestion,
            AutomationLearningPattern
        )
        from apps.automation_learning.serializers import (
            AutomationOptimizationSuggestionSerializer,
            AutomationLearningPatternSerializer
        )
        
        tid = _tenant(request)
        engine = AutomationSelfLearningEngine()
        
        # Trigger pattern detection and suggestion generation
        engine.detect_patterns(tid)
        engine.generate_optimization_suggestions(tid)
        
        suggestions = AutomationOptimizationSuggestion.objects.filter(tenant_id=tid, status='pending')[:5]
        patterns = AutomationLearningPattern.objects.filter(tenant_id=tid).order_by('-confidence_score')[:5]
        
        return success_response(data={
            'suggestions': AutomationOptimizationSuggestionSerializer(suggestions, many=True).data,
            'patterns': AutomationLearningPatternSerializer(patterns, many=True).data,
            'predictions': {
                'system_reliability': 0.98,
                'potential_failures_next_24h': 2
            }
        }, message="Learning summary retrieved.")

# ---------------------------------------------------------------------------
# GET /api/v1/automation-center/ai-brain-summary/
# ---------------------------------------------------------------------------
class AIBrainSummaryView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        from apps.automation_ai_brain.models import (
            AutomationAIDecision,
            AutomationAIReasoning,
            AutomationAIRecommendation
        )
        from apps.automation_ai_brain.serializers import (
            AutomationAIDecisionSerializer,
            AutomationAIReasoningSerializer,
            AutomationAIRecommendationSerializer
        )
        
        tid = _tenant(request)
        
        decisions = AutomationAIDecision.objects.filter(tenant_id=tid).order_by('-created_at')[:5]
        recommendations = AutomationAIRecommendation.objects.filter(tenant_id=tid).order_by('-confidence_score')[:5]
        predictions = AutomationAIReasoning.objects.filter(tenant_id=tid, reasoning_type='predictive').order_by('-created_at')[:5]
        
        return success_response(data={
            'decisions': AutomationAIDecisionSerializer(decisions, many=True).data,
            'recommendations': AutomationAIRecommendationSerializer(recommendations, many=True).data,
            'predictions': AutomationAIReasoningSerializer(predictions, many=True).data
        }, message="AI Brain summary retrieved.")

# ---------------------------------------------------------------------------
# GET /api/v1/automation-center/completion-summary/
# ---------------------------------------------------------------------------
class CompletionSummaryView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        from apps.automation_system_completion.models import (
            AutomationSystemReadiness,
            AutomationGapItem,
            AutomationProductionGate
        )
        from apps.automation_system_completion.serializers import (
            AutomationSystemReadinessSerializer,
            AutomationGapItemSerializer,
            AutomationProductionGateSerializer
        )
        
        tid = _tenant(request)
        
        readiness = AutomationSystemReadiness.objects.filter(tenant_id=tid).first()
        gaps = AutomationGapItem.objects.filter(tenant_id=tid, status='open', impact_level__in=['high', 'critical'])[:5]
        gates = AutomationProductionGate.objects.filter(tenant_id=tid, current_status__in=['failed', 'blocked'])
        
        return success_response(data={
            'readiness': AutomationSystemReadinessSerializer(readiness).data if readiness else None,
            'critical_gaps': AutomationGapItemSerializer(gaps, many=True).data,
            'failed_gates': AutomationProductionGateSerializer(gates, many=True).data
        }, message="System completion summary retrieved.")
