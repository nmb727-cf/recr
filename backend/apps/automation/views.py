from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.automation.models import AutomationRule, AutomationLog
from apps.automation.serializers import (
    AutomationRuleSerializer,
    AutomationLogSerializer,
    AutomationTriggerSerializer,
)
from apps.automation.services import AutomationEngine
from apps.core.responses import success_response, error_response


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

