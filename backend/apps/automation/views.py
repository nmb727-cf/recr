from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import success_response, error_response
from apps.automation.models import AutomationRule, AutomationLog
from apps.automation.serializers import (
    AutomationRuleSerializer,
    AutomationLogSerializer,
    AutomationTriggerSerializer,
)
from apps.automation.orchestrator import GlobalAutomationOrchestratorService
from apps.automation.autonomous_engine import AutonomousHiringService
from shared.actor_access import (
    COMPANY_OPERATIONAL_ROLES,
    role_of,
    require_non_candidate,
    require_tenant_or_platform_admin,
)


def _require_automation_operator(user):
    require_non_candidate(user, "You do not have permission to perform automation operations.")
    if user.is_staff or role_of(user) in (COMPANY_OPERATIONAL_ROLES | {'super_admin'}):
        return
    raise PermissionDenied("You do not have permission to perform automation operations.")

class AutonomousHiringView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        allowed_roles = COMPANY_OPERATIONAL_ROLES | {'super_admin'}
        if request.user.role not in allowed_roles and not request.user.is_staff:
            return error_response("Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            
        try:
            data = AutonomousHiringService.get_autonomous_dashboard(request.user.tenant_id)
            return success_response(data={'autonomous': data}, message="Autonomous Engine data retrieved.")
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return error_response(str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AutonomousActionUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            _require_automation_operator(request.user)
        except PermissionDenied:
            return error_response("Unauthorized", status_code=status.HTTP_403_FORBIDDEN)

        action = request.data.get('action') # 'approve' or 'reject'
        item_type = request.data.get('item_type', 'suggestion') # 'suggestion' or 'approval'
        
        try:
            if action == 'approve':
                result = AutonomousHiringService.approve_action(request.user.tenant_id, request.user.id, pk, item_type)
            elif action == 'reject':
                result = AutonomousHiringService.reject_action(request.user.tenant_id, request.user.id, pk, item_type)
            else:
                return error_response("Invalid action. Use 'approve' or 'reject'.")
                
            return success_response(data=result, message=f"Action successfully {action}d.")
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return error_response(str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GlobalOrchestratorDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in (COMPANY_OPERATIONAL_ROLES | {'super_admin'}):
            return error_response("Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            
        try:
            data = GlobalAutomationOrchestratorService.get_orchestrator_dashboard(request.user.tenant_id)
            return success_response(data={'orchestrator': data}, message="Global Orchestrator data retrieved.")
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return error_response(str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AutomationRuleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = AutomationRule.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).order_by('-created_at')
        trigger_event = request.query_params.get('trigger_event')
        if trigger_event:
            qs = qs.filter(trigger_event=trigger_event)
        return success_response(
            data={'rules': AutomationRuleSerializer(qs, many=True).data},
            message="Automation rules retrieved.",
            meta={'total': qs.count()},
        )

    def post(self, request):
        try:
            require_tenant_or_platform_admin(
                request.user,
                "Admin access required for automation rule management.",
            )
        except PermissionDenied:
            return error_response("Unauthorized", status_code=status.HTTP_403_FORBIDDEN)

        serializer = AutomationRuleSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        rule = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        return success_response(
            data={'rule': AutomationRuleSerializer(rule).data},
            message="Automation rule created.",
            status_code=status.HTTP_201_CREATED,
        )


class AutomationRuleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return AutomationRule.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()

    def get(self, request, pk):
        rule = self.get_object(request, pk)
        if not rule:
            return error_response("Automation rule not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'rule': AutomationRuleSerializer(rule).data},
            message="Automation rule retrieved.",
        )

    def put(self, request, pk):
        try:
            require_tenant_or_platform_admin(
                request.user,
                "Admin access required for automation rule management.",
            )
        except PermissionDenied:
            return error_response("Unauthorized", status_code=status.HTTP_403_FORBIDDEN)

        rule = self.get_object(request, pk)
        if not rule:
            return error_response("Automation rule not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = AutomationRuleSerializer(rule, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        return success_response(
            data={'rule': serializer.data},
            message="Automation rule updated.",
        )

    def delete(self, request, pk):
        try:
            require_tenant_or_platform_admin(
                request.user,
                "Admin access required for automation rule management.",
            )
        except PermissionDenied:
            return error_response("Unauthorized", status_code=status.HTTP_403_FORBIDDEN)

        rule = self.get_object(request, pk)
        if not rule:
            return error_response("Automation rule not found.", status_code=status.HTTP_404_NOT_FOUND)
        rule.soft_delete()
        return success_response(
            message="Automation rule deleted.",
            status_code=status.HTTP_204_NO_CONTENT,
        )


class AutomationTriggerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            _require_automation_operator(request.user)
        except PermissionDenied:
            return error_response("Unauthorized", status_code=status.HTTP_403_FORBIDDEN)

        serializer = AutomationTriggerSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        d = serializer.validated_data
        result = AutomationEngine.execute_trigger(
            trigger_event=d['trigger_event'],
            tenant_id=request.user.tenant_id,
            context=d.get('context') or {},
            actor_user_id=request.user.id,
            entity_type=d.get('entity_type', ''),
            entity_id=d.get('entity_id'),
        )
        return success_response(
            data={'result': result},
            message="Automation trigger executed.",
        )


class AutomationLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = AutomationLog.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).order_by('-executed_at')
        trigger_event = request.query_params.get('trigger_event')
        if trigger_event:
            qs = qs.filter(trigger_event=trigger_event)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return success_response(
            data={'logs': AutomationLogSerializer(qs[:200], many=True).data},
            message="Automation logs retrieved.",
            meta={'total': qs.count()},
        )
