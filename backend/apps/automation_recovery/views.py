"""
Automation Recovery Engine — API Views
"""
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import error_response, success_response

from .models import (
    DeadLetterStatus,
    InsightStatus,
    RecoveryStatus,
    WorkflowDeadLetterItem,
    WorkflowFallbackRule,
    WorkflowRecoveryCase,
    WorkflowRecoveryInsight,
)
from .permissions import CanAdmin, CanManage, CanView
from .serializers import (
    WorkflowDeadLetterItemSerializer,
    WorkflowFallbackRuleSerializer,
    WorkflowRecoveryCaseListSerializer,
    WorkflowRecoveryCaseSerializer,
    WorkflowRecoveryInsightSerializer,
)
from .services.workflow_recovery_engine import WorkflowRecoveryEngine


def _tid(request):
    return request.user.tenant_id


# ---------------------------------------------------------------------------
# Recovery Cases
# ---------------------------------------------------------------------------

class RecoveryCaseListView(APIView):
    """GET /api/v1/workflow-recovery/cases/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tid(request)
        qs = WorkflowRecoveryCase.objects.filter(tenant_id=tid, is_deleted=False)

        status_filter = request.query_params.get('status')
        strategy_filter = request.query_params.get('strategy')
        workflow_id = request.query_params.get('workflow_id')

        if status_filter:
            qs = qs.filter(recovery_status=status_filter)
        if strategy_filter:
            qs = qs.filter(recovery_strategy=strategy_filter)
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)

        serializer = WorkflowRecoveryCaseListSerializer(qs.order_by('-created_at'), many=True)
        return success_response(data=serializer.data, message='Recovery cases retrieved.')


class RecoveryCaseDetailView(APIView):
    """GET /api/v1/workflow-recovery/cases/{id}/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request, pk):
        try:
            case = WorkflowRecoveryCase.objects.prefetch_related('attempts').get(
                id=pk, tenant_id=_tid(request), is_deleted=False
            )
        except WorkflowRecoveryCase.DoesNotExist:
            return error_response(message='Recovery case not found.', status_code=404)
        serializer = WorkflowRecoveryCaseSerializer(case)
        return success_response(data=serializer.data)


class RecoveryCaseRetryView(APIView):
    """POST /api/v1/workflow-recovery/cases/{id}/retry/"""
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request, pk):
        try:
            attempt = WorkflowRecoveryEngine.retry_execution(
                case_id=pk, tenant_id=_tid(request)
            )
        except WorkflowRecoveryCase.DoesNotExist:
            return error_response(message='Recovery case not found.', status_code=404)
        except Exception as exc:  # noqa: BLE001
            return error_response(message=str(exc), status_code=400)
        if isinstance(attempt, dict) and attempt.get('error'):
            return error_response(message=attempt['error'], status_code=400)
        return success_response(
            data={'attempt_id': str(attempt.id), 'status': attempt.status},
            message='Retry triggered.',
        )


class RecoveryCaseResumeView(APIView):
    """POST /api/v1/workflow-recovery/cases/{id}/resume/"""
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request, pk):
        try:
            result = WorkflowRecoveryEngine.resume_execution_from_node(
                case_id=pk, tenant_id=_tid(request)
            )
        except WorkflowRecoveryCase.DoesNotExist:
            return error_response(message='Recovery case not found.', status_code=404)
        if isinstance(result, dict) and result.get('error'):
            return error_response(message=result['error'], status_code=400)
        return success_response(
            data={'attempt_id': str(result.id), 'status': result.status},
            message='Resume triggered.',
        )


class RecoveryCaseFallbackView(APIView):
    """POST /api/v1/workflow-recovery/cases/{id}/fallback/"""
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request, pk):
        try:
            result = WorkflowRecoveryEngine.execute_fallback(
                case_id=pk, tenant_id=_tid(request)
            )
        except WorkflowRecoveryCase.DoesNotExist:
            return error_response(message='Recovery case not found.', status_code=404)
        if isinstance(result, dict) and result.get('error'):
            return error_response(message=result['error'], status_code=400)
        return success_response(
            data={'attempt_id': str(result.id), 'status': result.status},
            message='Fallback executed.',
        )


class RecoveryCaseRollbackView(APIView):
    """POST /api/v1/workflow-recovery/cases/{id}/rollback/"""
    permission_classes = [IsAuthenticated, CanAdmin]

    def post(self, request, pk):
        try:
            result = WorkflowRecoveryEngine.attempt_rollback(
                case_id=pk, tenant_id=_tid(request)
            )
        except WorkflowRecoveryCase.DoesNotExist:
            return error_response(message='Recovery case not found.', status_code=404)
        if isinstance(result, dict) and result.get('error'):
            return error_response(message=result['error'], status_code=400)
        return success_response(
            data={'attempt_id': str(result.id), 'status': result.status},
            message='Rollback executed.',
        )


class RecoveryCaseResolveView(APIView):
    """POST /api/v1/workflow-recovery/cases/{id}/resolve/"""
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request, pk):
        if not WorkflowRecoveryCase.objects.filter(
            id=pk, tenant_id=_tid(request), is_deleted=False
        ).exists():
            return error_response(message='Recovery case not found.', status_code=404)
        WorkflowRecoveryEngine.resolve_recovery_case(case_id=pk, tenant_id=_tid(request))
        return success_response(message='Recovery case resolved.')


# ---------------------------------------------------------------------------
# Dead Letter Queue
# ---------------------------------------------------------------------------

class DeadLetterListView(APIView):
    """GET /api/v1/workflow-recovery/dead-letter/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tid(request)
        qs = WorkflowDeadLetterItem.objects.filter(tenant_id=tid, is_deleted=False)

        status_filter = request.query_params.get('status')
        workflow_id = request.query_params.get('workflow_id')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)

        serializer = WorkflowDeadLetterItemSerializer(qs.order_by('-created_at'), many=True)
        return success_response(data=serializer.data, message='Dead letter items retrieved.')


class DeadLetterDetailView(APIView):
    """GET /api/v1/workflow-recovery/dead-letter/{id}/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request, pk):
        try:
            item = WorkflowDeadLetterItem.objects.get(
                id=pk, tenant_id=_tid(request), is_deleted=False
            )
        except WorkflowDeadLetterItem.DoesNotExist:
            return error_response(message='Dead letter item not found.', status_code=404)
        serializer = WorkflowDeadLetterItemSerializer(item)
        return success_response(data=serializer.data)


class DeadLetterRetryView(APIView):
    """POST /api/v1/workflow-recovery/dead-letter/{id}/retry/"""
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request, pk):
        updated = WorkflowDeadLetterItem.objects.filter(
            id=pk, tenant_id=_tid(request), is_deleted=False
        ).update(status=DeadLetterStatus.RETRIED)
        if not updated:
            return error_response(message='Dead letter item not found.', status_code=404)
        return success_response(message='Item marked for retry. Background job will process it.')


class DeadLetterAssignView(APIView):
    """POST /api/v1/workflow-recovery/dead-letter/{id}/assign/"""
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request, pk):
        assignee_id = request.data.get('assignee_id')
        if not assignee_id:
            return error_response(message='assignee_id is required.', status_code=400)
        updated = WorkflowDeadLetterItem.objects.filter(
            id=pk, tenant_id=_tid(request), is_deleted=False
        ).update(
            status=DeadLetterStatus.INVESTIGATING,
            assigned_to=assignee_id,
        )
        if not updated:
            return error_response(message='Dead letter item not found.', status_code=404)
        return success_response(message='Item assigned for investigation.')


class DeadLetterResolveView(APIView):
    """POST /api/v1/workflow-recovery/dead-letter/{id}/resolve/"""
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request, pk):
        updated = WorkflowDeadLetterItem.objects.filter(
            id=pk, tenant_id=_tid(request), is_deleted=False
        ).update(
            status=DeadLetterStatus.RESOLVED,
            resolved_at=timezone.now(),
        )
        if not updated:
            return error_response(message='Dead letter item not found.', status_code=404)
        return success_response(message='Dead letter item resolved.')


# ---------------------------------------------------------------------------
# Fallback Rules
# ---------------------------------------------------------------------------

class FallbackRuleListView(APIView):
    """GET/POST /api/v1/workflow-recovery/fallback-rules/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tid(request)
        qs = WorkflowFallbackRule.objects.filter(tenant_id=tid, is_deleted=False)
        workflow_id = request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        serializer = WorkflowFallbackRuleSerializer(qs.order_by('-created_at'), many=True)
        return success_response(data=serializer.data, message='Fallback rules retrieved.')

    def post(self, request):
        serializer = WorkflowFallbackRuleSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message=serializer.errors, status_code=400)
        serializer.save(tenant_id=_tid(request))
        return success_response(
            data=serializer.data, message='Fallback rule created.', status_code=201
        )


class FallbackRuleDetailView(APIView):
    """PUT /api/v1/workflow-recovery/fallback-rules/{id}/"""
    permission_classes = [IsAuthenticated, CanManage]

    def put(self, request, pk):
        try:
            rule = WorkflowFallbackRule.objects.get(
                id=pk, tenant_id=_tid(request), is_deleted=False
            )
        except WorkflowFallbackRule.DoesNotExist:
            return error_response(message='Fallback rule not found.', status_code=404)
        serializer = WorkflowFallbackRuleSerializer(rule, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(message=serializer.errors, status_code=400)
        serializer.save()
        return success_response(data=serializer.data, message='Fallback rule updated.')


# ---------------------------------------------------------------------------
# Recovery Insights
# ---------------------------------------------------------------------------

class RecoveryInsightListView(APIView):
    """GET /api/v1/workflow-recovery/insights/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tid(request)
        qs = WorkflowRecoveryInsight.objects.filter(tenant_id=tid, is_deleted=False)

        status_filter = request.query_params.get('status')
        insight_type = request.query_params.get('type')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if insight_type:
            qs = qs.filter(insight_type=insight_type)

        serializer = WorkflowRecoveryInsightSerializer(qs.order_by('-last_seen_at'), many=True)
        return success_response(data=serializer.data, message='Recovery insights retrieved.')


# ---------------------------------------------------------------------------
# Recovery Analytics
# ---------------------------------------------------------------------------

class RecoveryAnalyticsView(APIView):
    """GET /api/v1/workflow-recovery/analytics/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        analytics = WorkflowRecoveryEngine.get_recovery_analytics(tenant_id=_tid(request))
        return success_response(data=analytics, message='Recovery analytics retrieved.')


# ---------------------------------------------------------------------------
# Command Center — Recovery Summary
# ---------------------------------------------------------------------------

class RecoverySummaryView(APIView):
    """
    GET /api/v1/workflow-recovery/summary/
    Used by the Automation Command Center to display a recovery widget.
    """
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tid(request)
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        cases = WorkflowRecoveryCase.objects.filter(tenant_id=tid, is_deleted=False)

        open_cases = cases.filter(recovery_status=RecoveryStatus.OPEN).count()
        retrying = cases.filter(recovery_status=RecoveryStatus.RETRYING).count()
        dead_letter = WorkflowDeadLetterItem.objects.filter(
            tenant_id=tid, status=DeadLetterStatus.PENDING, is_deleted=False
        ).count()
        manual_required = cases.filter(
            recovery_status=RecoveryStatus.MANUAL_INTERVENTION_REQUIRED
        ).count()
        recovered_today = cases.filter(
            recovery_status=RecoveryStatus.RESOLVED,
            resolved_at__gte=today,
        ).count()
        unrecoverable = cases.filter(recovery_status=RecoveryStatus.FAILED).count()

        return success_response(
            data={
                'open_recovery_cases': open_cases,
                'retrying_executions': retrying,
                'dead_letter_pending': dead_letter,
                'manual_intervention_required': manual_required,
                'recovered_today': recovered_today,
                'unrecoverable_failures': unrecoverable,
            },
            message='Recovery summary retrieved.',
        )
