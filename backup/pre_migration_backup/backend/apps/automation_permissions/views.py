from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import error_response, success_response

from .models import (
    WorkflowAccessAudit,
    WorkflowPermissionPolicy,
    WorkflowRestrictedAction,
)
from .permissions import CanAdmin, CanManage, CanView
from .serializers import (
    PermissionCheckSerializer,
    WorkflowAccessAuditSerializer,
    WorkflowPermissionPolicySerializer,
    WorkflowPermissionPolicyWriteSerializer,
    WorkflowRestrictedActionSerializer,
)
from .services.workflow_permission_service import WorkflowPermissionService


def _tid(request):
    return request.user.tenant_id


# ─── Policy List / Create ─────────────────────────────────────────────────────

class PolicyListView(APIView):
    """
    GET  /api/v1/workflow-permissions/policies/
    POST /api/v1/workflow-permissions/policies/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        qs = WorkflowPermissionPolicy.objects.filter(
            tenant_id=_tid(request), is_deleted=False
        ).order_by('-created_at')
        data = WorkflowPermissionPolicySerializer(qs, many=True).data
        return success_response(data={'policies': data})

    def post(self, request):
        ser = WorkflowPermissionPolicyWriteSerializer(data=request.data)
        if not ser.is_valid():
            return error_response('Validation failed', ser.errors)
        policy = ser.save(
            tenant_id=_tid(request),
            created_by=request.user.id,
        )
        return success_response(
            data={'policy': WorkflowPermissionPolicySerializer(policy).data},
            message='Policy created',
            status_code=status.HTTP_201_CREATED,
        )


# ─── Policy Detail ────────────────────────────────────────────────────────────

class PolicyDetailView(APIView):
    """
    GET    /api/v1/workflow-permissions/policies/{id}/
    PUT    /api/v1/workflow-permissions/policies/{id}/
    DELETE /api/v1/workflow-permissions/policies/{id}/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def _get_policy(self, request, pk):
        return WorkflowPermissionPolicy.objects.filter(
            id=pk, tenant_id=_tid(request), is_deleted=False
        ).first()

    def get(self, request, pk):
        policy = self._get_policy(request, pk)
        if not policy:
            return error_response('Policy not found', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data={'policy': WorkflowPermissionPolicySerializer(policy).data})

    def put(self, request, pk):
        policy = self._get_policy(request, pk)
        if not policy:
            return error_response('Policy not found', status_code=status.HTTP_404_NOT_FOUND)
        ser = WorkflowPermissionPolicyWriteSerializer(policy, data=request.data, partial=True)
        if not ser.is_valid():
            return error_response('Validation failed', ser.errors)
        policy = ser.save()
        return success_response(
            data={'policy': WorkflowPermissionPolicySerializer(policy).data},
            message='Policy updated',
        )

    def delete(self, request, pk):
        policy = self._get_policy(request, pk)
        if not policy:
            return error_response('Policy not found', status_code=status.HTTP_404_NOT_FOUND)
        policy.soft_delete()
        return success_response(message='Policy deleted')


# ─── Restricted Actions ───────────────────────────────────────────────────────

class RestrictedActionListView(APIView):
    """
    GET /api/v1/workflow-permissions/restricted-actions/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        qs = WorkflowRestrictedAction.objects.filter(
            tenant_id=_tid(request), is_deleted=False
        ).order_by('-severity', 'action_key')
        data = WorkflowRestrictedActionSerializer(qs, many=True).data
        return success_response(data={'restricted_actions': data})


class RestrictedActionDetailView(APIView):
    """
    PUT /api/v1/workflow-permissions/restricted-actions/{id}/
    """
    permission_classes = [IsAuthenticated, CanAdmin]

    def _get_obj(self, request, pk):
        return WorkflowRestrictedAction.objects.filter(
            id=pk, tenant_id=_tid(request), is_deleted=False
        ).first()

    def put(self, request, pk):
        obj = self._get_obj(request, pk)
        if not obj:
            return error_response('Restricted action not found', status_code=status.HTTP_404_NOT_FOUND)
        ser = WorkflowRestrictedActionSerializer(obj, data=request.data, partial=True)
        if not ser.is_valid():
            return error_response('Validation failed', ser.errors)
        ser.save()
        return success_response(
            data={'restricted_action': ser.data},
            message='Restricted action updated',
        )


# ─── Audit Logs ───────────────────────────────────────────────────────────────

class AuditLogListView(APIView):
    """
    GET /api/v1/workflow-permissions/audit/
    """
    permission_classes = [IsAuthenticated, CanAdmin]

    def get(self, request):
        qs = WorkflowAccessAudit.objects.filter(tenant_id=_tid(request)).order_by('-created_at')

        user_id    = request.query_params.get('user_id')
        workflow_id = request.query_params.get('workflow_id')
        decision   = request.query_params.get('decision')

        if user_id:
            qs = qs.filter(user_id=user_id)
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        if decision:
            qs = qs.filter(decision=decision)

        # Simple pagination
        limit  = min(int(request.query_params.get('limit', 50)), 200)
        offset = int(request.query_params.get('offset', 0))
        total  = qs.count()
        qs     = qs[offset: offset + limit]

        data = WorkflowAccessAuditSerializer(qs, many=True).data
        return success_response(
            data={'audit_logs': data},
            meta={'total': total, 'limit': limit, 'offset': offset},
        )


# ─── Role Matrix ──────────────────────────────────────────────────────────────

class RoleMatrixView(APIView):
    """
    GET /api/v1/workflow-permissions/matrix/
    Returns: roles × workflow-permissions matrix
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        matrix = WorkflowPermissionService.get_role_matrix(_tid(request))
        return success_response(data={'matrix': matrix})


# ─── Permission Check ─────────────────────────────────────────────────────────

class PermissionCheckView(APIView):
    """
    POST /api/v1/workflow-permissions/check/
    Body: { workflow_id?, action, resource_type? }
    Returns: { allowed, decision, reason }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = PermissionCheckSerializer(data=request.data)
        if not ser.is_valid():
            return error_response('Validation failed', ser.errors)

        workflow_id   = ser.validated_data.get('workflow_id')
        action        = ser.validated_data['action']
        resource_type = ser.validated_data.get('resource_type', 'workflow')

        workflow = None
        if workflow_id:
            try:
                from apps.orchestration_center.models.workflow import Workflow
                workflow = Workflow.objects.filter(
                    id=workflow_id, tenant_id=_tid(request), is_deleted=False
                ).first()
            except Exception:
                pass

        result = WorkflowPermissionService.can_user_access_workflow(
            request.user, workflow, action, resource_type=resource_type
        )
        return success_response(data=result)
