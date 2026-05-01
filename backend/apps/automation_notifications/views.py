from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import error_response, success_response

from .models import (
    WorkflowEscalationNotification,
    WorkflowNotificationDelivery,
    WorkflowNotificationInsight,
    WorkflowNotificationPreference,
    WorkflowNotificationRule,
    DeliveryStatus,
)
from .permissions import CanAdmin, CanManage, CanView
from .serializers import (
    TestSendSerializer,
    WorkflowEscalationSerializer,
    WorkflowNotificationDeliverySerializer,
    WorkflowNotificationInsightSerializer,
    WorkflowNotificationPreferenceSerializer,
    WorkflowNotificationRuleSerializer,
)
from .services.workflow_notification_orchestrator import WorkflowNotificationOrchestrator


def _tid(request):
    return request.user.tenant_id


# ─── Notification Rules ───────────────────────────────────────────────────────

class NotificationRuleListView(APIView):
    """
    GET  /api/v1/workflow-notifications/rules/
    POST /api/v1/workflow-notifications/rules/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        qs = WorkflowNotificationRule.objects.filter(
            tenant_id=_tid(request), is_deleted=False
        ).order_by('-created_at')

        workflow_id = request.query_params.get('workflow_id')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)

        data = WorkflowNotificationRuleSerializer(qs, many=True).data
        return success_response(data={'rules': data})

    def post(self, request):
        ser = WorkflowNotificationRuleSerializer(data=request.data)
        if not ser.is_valid():
            return error_response('Validation failed', ser.errors)
        rule = ser.save(tenant_id=_tid(request), created_by=request.user.id)
        return success_response(
            data={'rule': WorkflowNotificationRuleSerializer(rule).data},
            message='Notification rule created',
            status_code=status.HTTP_201_CREATED,
        )


class NotificationRuleDetailView(APIView):
    """
    GET    /api/v1/workflow-notifications/rules/{id}/
    PUT    /api/v1/workflow-notifications/rules/{id}/
    DELETE /api/v1/workflow-notifications/rules/{id}/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def _get(self, request, pk):
        return WorkflowNotificationRule.objects.filter(
            id=pk, tenant_id=_tid(request), is_deleted=False
        ).first()

    def get(self, request, pk):
        rule = self._get(request, pk)
        if not rule:
            return error_response('Rule not found', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data={'rule': WorkflowNotificationRuleSerializer(rule).data})

    def put(self, request, pk):
        rule = self._get(request, pk)
        if not rule:
            return error_response('Rule not found', status_code=status.HTTP_404_NOT_FOUND)
        ser = WorkflowNotificationRuleSerializer(rule, data=request.data, partial=True)
        if not ser.is_valid():
            return error_response('Validation failed', ser.errors)
        rule = ser.save()
        return success_response(
            data={'rule': WorkflowNotificationRuleSerializer(rule).data},
            message='Rule updated',
        )

    def delete(self, request, pk):
        rule = self._get(request, pk)
        if not rule:
            return error_response('Rule not found', status_code=status.HTTP_404_NOT_FOUND)
        rule.soft_delete()
        return success_response(message='Rule deleted')


# ─── Delivery Log ─────────────────────────────────────────────────────────────

class DeliveryLogView(APIView):
    """
    GET /api/v1/workflow-notifications/deliveries/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        qs = WorkflowNotificationDelivery.objects.filter(
            tenant_id=_tid(request)
        ).order_by('-created_at')

        workflow_id = request.query_params.get('workflow_id')
        channel     = request.query_params.get('channel')
        st          = request.query_params.get('status')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        if channel:
            qs = qs.filter(channel=channel)
        if st:
            qs = qs.filter(status=st)

        limit  = min(int(request.query_params.get('limit', 50)), 200)
        offset = int(request.query_params.get('offset', 0))
        total  = qs.count()
        data   = WorkflowNotificationDeliverySerializer(qs[offset:offset + limit], many=True).data
        return success_response(
            data={'deliveries': data},
            meta={'total': total, 'limit': limit, 'offset': offset},
        )


# ─── Retry ────────────────────────────────────────────────────────────────────

class RetryDeliveryView(APIView):
    """
    POST /api/v1/workflow-notifications/retry/{delivery_id}/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request, delivery_id):
        delivery = WorkflowNotificationDelivery.objects.filter(
            id=delivery_id, tenant_id=_tid(request)
        ).first()
        if not delivery:
            return error_response('Delivery not found', status_code=status.HTTP_404_NOT_FOUND)
        if delivery.status not in (DeliveryStatus.FAILED, DeliveryStatus.QUEUED):
            return error_response('Only failed or queued deliveries can be retried')

        delivery.status = DeliveryStatus.QUEUED
        delivery.save(update_fields=['status'])
        result = WorkflowNotificationOrchestrator.send_notification(delivery)
        return success_response(data={'result': result}, message='Retry dispatched')


# ─── Escalation Log ───────────────────────────────────────────────────────────

class EscalationLogView(APIView):
    """
    GET /api/v1/workflow-notifications/escalations/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        qs = WorkflowEscalationNotification.objects.filter(
            tenant_id=_tid(request)
        ).order_by('-created_at')

        limit  = min(int(request.query_params.get('limit', 50)), 200)
        offset = int(request.query_params.get('offset', 0))
        total  = qs.count()
        data   = WorkflowEscalationSerializer(qs[offset:offset + limit], many=True).data
        return success_response(
            data={'escalations': data},
            meta={'total': total},
        )


# ─── Channel Health ───────────────────────────────────────────────────────────

class ChannelHealthView(APIView):
    """
    GET /api/v1/workflow-notifications/channel-health/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        health = WorkflowNotificationOrchestrator.get_channel_health(_tid(request))
        return success_response(data={'channel_health': health})


# ─── User Preferences ─────────────────────────────────────────────────────────

class PreferencesView(APIView):
    """
    GET /api/v1/workflow-notifications/preferences/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        qs = WorkflowNotificationPreference.objects.filter(
            tenant_id=_tid(request), is_deleted=False
        ).order_by('user_id')

        user_id = request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(user_id=user_id)

        data = WorkflowNotificationPreferenceSerializer(qs, many=True).data
        return success_response(data={'preferences': data})


# ─── Insights ─────────────────────────────────────────────────────────────────

class InsightsView(APIView):
    """
    GET /api/v1/workflow-notifications/insights/
    """
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        qs = WorkflowNotificationInsight.objects.filter(
            tenant_id=_tid(request)
        ).order_by('-created_at')[:50]
        data = WorkflowNotificationInsightSerializer(qs, many=True).data
        return success_response(data={'insights': data})


# ─── Test Send ────────────────────────────────────────────────────────────────

class TestSendView(APIView):
    """
    POST /api/v1/workflow-notifications/test-send/
    """
    permission_classes = [IsAuthenticated, CanAdmin]

    def post(self, request):
        ser = TestSendSerializer(data=request.data)
        if not ser.is_valid():
            return error_response('Validation failed', ser.errors)

        rule = WorkflowNotificationRule.objects.filter(
            id=ser.validated_data['rule_id'],
            tenant_id=_tid(request),
            is_deleted=False,
        ).first()
        if not rule:
            return error_response('Rule not found', status_code=status.HTTP_404_NOT_FOUND)

        recipient = {}
        recipient_id = ser.validated_data.get('recipient_id')
        if recipient_id:
            recipient = {'user_id': recipient_id, 'email': '', 'phone': ''}

        result = WorkflowNotificationOrchestrator.dispatch(
            tenant_id=_tid(request),
            workflow_id=ser.validated_data['workflow_id'],
            rule=rule,
            context={'_test': True},
            recipient_override=recipient or None,
        )
        return success_response(data={'result': result}, message='Test send dispatched')
