"""
Notification Orchestration Admin/Debug Views
=============================================
Internal endpoints for monitoring, retrying, and cancelling
notification automation jobs and escalation logs.

Access is restricted to tenant_admin / super_admin users.
These endpoints are NOT exposed to regular users.
"""
import logging

from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.permissions import IsAuthenticated
from apps.communications.permissions import require_communications_admin_actor

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------

def _tenant_id(request):
    return getattr(request.user, 'tenant_id', None)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

class AutomationJobSerializer(serializers.Serializer):
    id                   = serializers.UUIDField()
    tenant_id            = serializers.UUIDField()
    notification_id      = serializers.UUIDField(allow_null=True)
    event_key            = serializers.CharField()
    job_type             = serializers.CharField()
    scheduled_for        = serializers.DateTimeField()
    executed_at          = serializers.DateTimeField(allow_null=True)
    status               = serializers.CharField()
    cancel_reason        = serializers.CharField()
    retry_count          = serializers.IntegerField()
    related_entity_type  = serializers.CharField()
    related_entity_id    = serializers.UUIDField(allow_null=True)
    metadata             = serializers.DictField()
    created_at           = serializers.DateTimeField()


class EscalationLogSerializer(serializers.Serializer):
    id                = serializers.UUIDField()
    tenant_id         = serializers.UUIDField()
    notification_id   = serializers.UUIDField()
    escalation_level  = serializers.IntegerField()
    target_user_id    = serializers.UUIDField(allow_null=True)
    target_type       = serializers.CharField()
    triggered_at      = serializers.DateTimeField()
    channel_used      = serializers.CharField()
    status            = serializers.CharField()
    original_event_key = serializers.CharField()
    original_user_id  = serializers.UUIDField(allow_null=True)
    metadata          = serializers.DictField()


# ---------------------------------------------------------------------------
# GET /api/v1/notification-control/jobs/
# ---------------------------------------------------------------------------

class NotificationAutomationJobListView(APIView):
    """
    List automation jobs for the current tenant.
    Supports filters: status, job_type, event_key.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        require_communications_admin_actor(request.user)

        from apps.communications.notification_orchestration_models import NotificationAutomationJob

        tenant_id = _tenant_id(request)
        qs = NotificationAutomationJob.objects.filter(tenant_id=tenant_id).order_by('-scheduled_for')

        # Query param filters
        job_status = request.query_params.get('status')
        job_type = request.query_params.get('job_type')
        event_key = request.query_params.get('event_key')

        if job_status:
            qs = qs.filter(status=job_status)
        if job_type:
            qs = qs.filter(job_type=job_type)
        if event_key:
            qs = qs.filter(event_key=event_key)

        qs = qs[:100]  # cap at 100 for safety
        data = AutomationJobSerializer(qs, many=True).data
        return Response({'count': len(data), 'results': data})


# ---------------------------------------------------------------------------
# POST /api/v1/notification-control/jobs/<job_id>/retry/
# ---------------------------------------------------------------------------

class NotificationAutomationJobRetryView(APIView):
    """
    Re-queue a failed or skipped automation job.
    Creates a fresh PENDING job of the same type and schedules it immediately.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        require_communications_admin_actor(request.user)

        from apps.communications.notification_orchestration_models import (
            NotificationAutomationJob,
            NotificationAutomationJobStatus,
        )

        tenant_id = _tenant_id(request)
        try:
            job = NotificationAutomationJob.objects.get(id=job_id, tenant_id=tenant_id)
        except NotificationAutomationJob.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=404)

        if job.status not in (
            NotificationAutomationJobStatus.FAILED,
            NotificationAutomationJobStatus.SKIPPED,
        ):
            return Response(
                {'detail': f'Job cannot be retried from status "{job.status}".'},
                status=400,
            )

        # Create a new job with the same config, schedule immediately
        from apps.communications.notification_orchestration_service import schedule_automation_job
        new_job = schedule_automation_job(
            tenant_id=job.tenant_id,
            notification_id=str(job.notification_id) if job.notification_id else None,
            event_key=job.event_key,
            job_type=job.job_type,
            delay_seconds=0,
            related_entity_type=job.related_entity_type,
            related_entity_id=job.related_entity_id,
            metadata={**job.metadata, 'retry_of': str(job.id), 'retry_count': job.retry_count + 1},
        )
        job.retry_count += 1
        job.save(update_fields=['retry_count', 'updated_at'])

        return Response(
            {'detail': 'Job queued for immediate retry.', 'new_job_id': str(new_job.id)},
            status=202,
        )


# ---------------------------------------------------------------------------
# POST /api/v1/notification-control/jobs/<job_id>/cancel/
# ---------------------------------------------------------------------------

class NotificationAutomationJobCancelView(APIView):
    """Cancel a pending automation job."""
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        require_communications_admin_actor(request.user)

        from apps.communications.notification_orchestration_models import (
            NotificationAutomationJob,
            NotificationAutomationJobStatus,
        )

        tenant_id = _tenant_id(request)
        try:
            job = NotificationAutomationJob.objects.get(id=job_id, tenant_id=tenant_id)
        except NotificationAutomationJob.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=404)

        if job.status != NotificationAutomationJobStatus.PENDING:
            return Response(
                {'detail': f'Only PENDING jobs can be cancelled (current: "{job.status}").'},
                status=400,
            )

        reason = request.data.get('reason', 'manual_admin_cancel')
        job.cancel(reason=reason)
        return Response({'detail': 'Job cancelled.', 'job_id': str(job.id)})


# ---------------------------------------------------------------------------
# GET /api/v1/notification-control/escalations/
# ---------------------------------------------------------------------------

class NotificationEscalationLogListView(APIView):
    """
    List escalation log entries for the current tenant.
    Supports filters: status, target_user_id.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        require_communications_admin_actor(request.user)

        from apps.communications.notification_orchestration_models import NotificationEscalationLog

        tenant_id = _tenant_id(request)
        qs = NotificationEscalationLog.objects.filter(tenant_id=tenant_id).order_by('-triggered_at')

        log_status = request.query_params.get('status')
        target_user = request.query_params.get('target_user_id')

        if log_status:
            qs = qs.filter(status=log_status)
        if target_user:
            qs = qs.filter(target_user_id=target_user)

        qs = qs[:100]
        data = EscalationLogSerializer(qs, many=True).data
        return Response({'count': len(data), 'results': data})


# ---------------------------------------------------------------------------
# POST /api/v1/notification-control/rules/<event_key>/test/
# ---------------------------------------------------------------------------

class NotificationRuleTestView(APIView):
    """
    Test a notification rule by simulating what the orchestration service
    would do for a given event_key + dummy context.
    Does NOT send any actual notifications.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, event_key):
        require_communications_admin_actor(request.user)

        tenant_id = _tenant_id(request)

        from apps.communications.notification_orchestration_service import (
            resolve_notification_rule,
            resolve_channels,
            resolve_template,
        )

        rule = resolve_notification_rule(tenant_id=tenant_id, event_key=event_key)
        channels = resolve_channels(rule=rule, tenant_id=tenant_id)
        template = resolve_template(event_key=event_key, tenant_id=tenant_id, rule=rule)

        return Response({
            'event_key':      event_key,
            'rule_found':     rule is not None,
            'rule': {
                'id':                       str(rule.id) if rule else None,
                'is_active':                rule.is_active if rule else None,
                'priority':                 rule.priority if rule else None,
                'fallback_enabled':         rule.fallback_enabled if rule else None,
                'fallback_delay_minutes':   rule.fallback_delay_minutes if rule else None,
                'escalation_enabled':       rule.escalation_enabled if rule else None,
                'escalation_delay_minutes': rule.escalation_delay_minutes if rule else None,
                'escalation_target_type':   rule.escalation_target_type if rule else None,
            } if rule else None,
            'channels':       channels,
            'template_found': template is not None,
            'template_name':  template.name if template else None,
        })
