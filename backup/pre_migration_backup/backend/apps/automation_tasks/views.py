from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import error_response, success_response

from .models import (
    TaskStatus,
    WorkflowTaskEscalation,
    WorkflowTaskExecution,
    WorkflowTaskRule,
)
from .permissions import CanAdmin, CanManage, CanView
from .serializers import (
    TaskTestSerializer,
    WorkflowTaskEscalationSerializer,
    WorkflowTaskExecutionSerializer,
    WorkflowTaskRuleSerializer,
)
from .services.workflow_task_orchestrator import WorkflowTaskOrchestrator


def _tid(request):
    return request.user.tenant_id


# ─── Task Rules ───────────────────────────────────────────────────────────────

class TaskRuleListView(APIView):
    """
    GET  /api/v1/workflow-tasks/rules/
    POST /api/v1/workflow-tasks/rules/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        qs = WorkflowTaskRule.objects.filter(
            tenant_id=_tid(request), is_deleted=False
        ).order_by('-created_at')

        wf = request.query_params.get('workflow_id')
        if wf:
            qs = qs.filter(workflow_id=wf)

        data = WorkflowTaskRuleSerializer(qs, many=True).data
        return success_response(data={'rules': data})

    def post(self, request):
        ser = WorkflowTaskRuleSerializer(data=request.data)
        if not ser.is_valid():
            return error_response('Validation failed', ser.errors)
        rule = ser.save(tenant_id=_tid(request), created_by=request.user.id)
        return success_response(
            data={'rule': WorkflowTaskRuleSerializer(rule).data},
            message='Task rule created',
            status_code=status.HTTP_201_CREATED,
        )


class TaskRuleDetailView(APIView):
    """
    GET    /api/v1/workflow-tasks/rules/{id}/
    PUT    /api/v1/workflow-tasks/rules/{id}/
    DELETE /api/v1/workflow-tasks/rules/{id}/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def _get(self, request, pk):
        return WorkflowTaskRule.objects.filter(
            id=pk, tenant_id=_tid(request), is_deleted=False
        ).first()

    def get(self, request, pk):
        rule = self._get(request, pk)
        if not rule:
            return error_response('Rule not found', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data={'rule': WorkflowTaskRuleSerializer(rule).data})

    def put(self, request, pk):
        rule = self._get(request, pk)
        if not rule:
            return error_response('Rule not found', status_code=status.HTTP_404_NOT_FOUND)
        ser = WorkflowTaskRuleSerializer(rule, data=request.data, partial=True)
        if not ser.is_valid():
            return error_response('Validation failed', ser.errors)
        rule = ser.save()
        return success_response(
            data={'rule': WorkflowTaskRuleSerializer(rule).data},
            message='Rule updated',
        )

    def delete(self, request, pk):
        rule = self._get(request, pk)
        if not rule:
            return error_response('Rule not found', status_code=status.HTTP_404_NOT_FOUND)
        rule.soft_delete()
        return success_response(message='Rule deleted')


# ─── Task Executions ──────────────────────────────────────────────────────────

class TaskExecutionListView(APIView):
    """
    GET /api/v1/workflow-tasks/executions/
    """
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        qs = WorkflowTaskExecution.objects.filter(tenant_id=_tid(request)).order_by('-created_at')

        st          = request.query_params.get('status')
        assignee    = request.query_params.get('assignee_user_id')
        priority    = request.query_params.get('priority')
        workflow_id = request.query_params.get('workflow_id')
        escalated   = request.query_params.get('escalated')

        if st:
            qs = qs.filter(status=st)
        if assignee:
            qs = qs.filter(assignee_user_id=assignee)
        if priority:
            qs = qs.filter(priority=priority)
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        if escalated is not None:
            qs = qs.filter(escalated=escalated.lower() == 'true')

        # Recruiters see only their own tasks
        if getattr(request.user, 'role', '') == 'recruiter':
            qs = qs.filter(assignee_user_id=request.user.id)

        limit  = min(int(request.query_params.get('limit', 50)), 200)
        offset = int(request.query_params.get('offset', 0))
        total  = qs.count()
        data   = WorkflowTaskExecutionSerializer(qs[offset:offset + limit], many=True).data
        return success_response(
            data={'executions': data},
            meta={'total': total, 'limit': limit, 'offset': offset},
        )


class TaskCompleteView(APIView):
    """
    POST /api/v1/workflow-tasks/executions/{id}/complete/
    """
    permission_classes = [IsAuthenticated, CanView]

    def post(self, request, pk):
        task = WorkflowTaskExecution.objects.filter(
            id=pk, tenant_id=_tid(request)
        ).first()
        if not task:
            return error_response('Task not found', status_code=status.HTTP_404_NOT_FOUND)
        if task.status == TaskStatus.COMPLETED:
            return error_response('Task already completed')
        result = WorkflowTaskOrchestrator.complete_task_trigger(task)
        return success_response(data={'result': result}, message='Task completed')


# ─── Escalations ──────────────────────────────────────────────────────────────

class EscalationListView(APIView):
    """
    GET /api/v1/workflow-tasks/escalations/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        qs = WorkflowTaskEscalation.objects.filter(
            tenant_id=_tid(request)
        ).select_related('task_execution').order_by('-escalated_at')

        limit  = min(int(request.query_params.get('limit', 50)), 200)
        offset = int(request.query_params.get('offset', 0))
        total  = qs.count()
        data   = WorkflowTaskEscalationSerializer(qs[offset:offset + limit], many=True).data
        return success_response(
            data={'escalations': data},
            meta={'total': total},
        )


# ─── Analytics ────────────────────────────────────────────────────────────────

class TaskAnalyticsView(APIView):
    """
    GET /api/v1/workflow-tasks/analytics/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        analytics = WorkflowTaskOrchestrator.get_analytics(_tid(request))
        return success_response(data={'analytics': analytics})


# ─── SLA Tracker (manual trigger) ────────────────────────────────────────────

class TaskSLATrackView(APIView):
    """
    POST /api/v1/workflow-tasks/track-sla/
    Admin-only trigger to run SLA tracking for current tenant.
    """
    permission_classes = [IsAuthenticated, CanAdmin]

    def post(self, request):
        result = WorkflowTaskOrchestrator.track_task_status(_tid(request))
        return success_response(data={'result': result}, message='SLA tracking complete')


# ─── Test ─────────────────────────────────────────────────────────────────────

class TaskTestView(APIView):
    """
    POST /api/v1/workflow-tasks/test/
    """
    permission_classes = [IsAuthenticated, CanAdmin]

    def post(self, request):
        ser = TaskTestSerializer(data=request.data)
        if not ser.is_valid():
            return error_response('Validation failed', ser.errors)

        rule = WorkflowTaskRule.objects.filter(
            id=ser.validated_data['rule_id'],
            tenant_id=_tid(request),
            is_deleted=False,
        ).first()
        if not rule:
            return error_response('Rule not found', status_code=status.HTTP_404_NOT_FOUND)

        task = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=_tid(request),
            workflow_id=ser.validated_data['workflow_id'],
            rule=rule,
            context=ser.validated_data.get('context', {}),
        )
        return success_response(
            data={'task': WorkflowTaskExecutionSerializer(task).data},
            message='Test task created',
            status_code=status.HTTP_201_CREATED,
        )
