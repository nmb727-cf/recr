"""
Multi-Channel Observability Views
===================================
Admin/support endpoints for monitoring the multi-channel communication engine.

All views require staff-level authentication (IsAdminUser or custom RBAC check).
These are internal operational endpoints, not exposed to regular users.

Endpoints:
    GET  /api/v1/communications/deliveries/           — list all channel deliveries
    GET  /api/v1/communications/deliveries/<id>/      — delivery detail
    POST /api/v1/communications/deliveries/<id>/retry/ — retry a failed delivery
    GET  /api/v1/communications/channel-health/       — provider health check per channel
    GET  /api/v1/communications/fallback-jobs/        — pending/recent fallback jobs
    GET  /api/v1/communications/channel-stats/        — delivery stats by channel

All responses are scoped to the requesting tenant (tenant_id from auth).
Super-admin users can pass ?tenant_id=<uuid> to inspect other tenants.
"""
import logging
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------

def _get_tenant_id_for_request(request):
    """Return tenant_id scoped to the request user."""
    user = request.user
    # Allow super_admin to query any tenant
    if getattr(user, 'role', '') in ('super_admin',) and request.query_params.get('tenant_id'):
        return request.query_params['tenant_id']
    return getattr(user, 'tenant_id', None)


def _is_admin_or_staff(user):
    return (
        getattr(user, 'is_staff', False)
        or getattr(user, 'role', '') in ('super_admin', 'tenant_admin')
    )


# ---------------------------------------------------------------------------
# CommunicationDeliveryListView
# ---------------------------------------------------------------------------

class CommunicationDeliveryListView(APIView):
    """
    GET /api/v1/communications/deliveries/

    Query params:
        channel_type  — filter by channel (whatsapp, sms, push)
        status        — filter by status
        notification_id — filter by notification
        page          — pagination (default page_size=50)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.communications.channel_config_models import CommunicationDelivery

        tenant_id = _get_tenant_id_for_request(request)
        if not _is_admin_or_staff(request.user):
            return Response({'detail': 'Permission denied.'}, status=403)

        qs = CommunicationDelivery.objects.filter(tenant_id=tenant_id)

        channel = request.query_params.get('channel_type')
        if channel:
            qs = qs.filter(channel_type=channel)

        st = request.query_params.get('status')
        if st:
            qs = qs.filter(status=st)

        notif_id = request.query_params.get('notification_id')
        if notif_id:
            qs = qs.filter(notification_id=notif_id)

        qs = qs.order_by('-created_at')[:100]

        data = [_serialise_delivery(d) for d in qs]
        return Response({'results': data, 'count': len(data)})


# ---------------------------------------------------------------------------
# CommunicationDeliveryDetailView
# ---------------------------------------------------------------------------

class CommunicationDeliveryDetailView(APIView):
    """GET /api/v1/communications/deliveries/<id>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, delivery_id):
        from apps.communications.channel_config_models import CommunicationDelivery

        tenant_id = _get_tenant_id_for_request(request)
        if not _is_admin_or_staff(request.user):
            return Response({'detail': 'Permission denied.'}, status=403)

        try:
            d = CommunicationDelivery.objects.get(id=delivery_id, tenant_id=tenant_id)
        except CommunicationDelivery.DoesNotExist:
            raise NotFound('Delivery not found.')

        return Response(_serialise_delivery(d, full=True))


# ---------------------------------------------------------------------------
# CommunicationDeliveryRetryView
# ---------------------------------------------------------------------------

class CommunicationDeliveryRetryView(APIView):
    """
    POST /api/v1/communications/deliveries/<id>/retry/

    Retry a FAILED or DEFERRED delivery.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, delivery_id):
        from apps.communications.channel_config_models import (
            CommunicationDelivery,
            CommunicationDeliveryStatus,
        )
        from apps.communications.channel_tasks import retry_channel_delivery_task

        if not _is_admin_or_staff(request.user):
            return Response({'detail': 'Permission denied.'}, status=403)

        tenant_id = _get_tenant_id_for_request(request)
        try:
            d = CommunicationDelivery.objects.get(id=delivery_id, tenant_id=tenant_id)
        except CommunicationDelivery.DoesNotExist:
            raise NotFound('Delivery not found.')

        if not d.can_retry():
            return Response(
                {'detail': f'Delivery cannot be retried (status={d.status}, attempts={d.attempt_number}/{d.max_attempts}).'},
                status=400,
            )

        # Reset to PENDING
        d.status = CommunicationDeliveryStatus.PENDING
        d.save(update_fields=['status', 'updated_at'])
        retry_channel_delivery_task.apply_async(args=[str(delivery_id)], countdown=0)

        return Response({'detail': 'Retry queued.', 'delivery_id': str(delivery_id)})


# ---------------------------------------------------------------------------
# ChannelHealthView
# ---------------------------------------------------------------------------

class ChannelHealthView(APIView):
    """
    GET /api/v1/communications/channel-health/

    Run health checks on all configured channel providers for the tenant.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.communications.channel_config_models import TenantChannelConfig
        from apps.communications.channel_services import resolve_channel_provider

        if not _is_admin_or_staff(request.user):
            return Response({'detail': 'Permission denied.'}, status=403)

        tenant_id = _get_tenant_id_for_request(request)
        results = {}

        configs = TenantChannelConfig.objects.filter(
            tenant_id=tenant_id,
            is_active=True,
            is_deleted=False,
        )

        for cfg in configs:
            try:
                provider = resolve_channel_provider(tenant_id, cfg.channel_type)
                if provider:
                    health = provider.health_check()
                    results[cfg.channel_type] = {
                        'healthy': health.healthy,
                        'provider': cfg.provider,
                        'latency_ms': health.latency_ms,
                        'detail': health.detail,
                    }
                else:
                    results[cfg.channel_type] = {
                        'healthy': False,
                        'provider': cfg.provider,
                        'detail': 'Provider could not be resolved',
                    }
            except Exception as exc:
                results[cfg.channel_type] = {
                    'healthy': False,
                    'provider': cfg.provider,
                    'detail': str(exc)[:200],
                }

        if not results:
            results['status'] = 'No channel configs found for this tenant'

        return Response(results)


# ---------------------------------------------------------------------------
# FallbackJobListView
# ---------------------------------------------------------------------------

class FallbackJobListView(APIView):
    """
    GET /api/v1/communications/fallback-jobs/

    List recent/pending automation jobs related to multi-channel delivery.
    Query params: status (pending/executed/cancelled), channel_type
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.communications.notification_orchestration_models import (
            NotificationAutomationJob,
            NotificationAutomationJobType,
        )

        if not _is_admin_or_staff(request.user):
            return Response({'detail': 'Permission denied.'}, status=403)

        tenant_id = _get_tenant_id_for_request(request)
        multi_channel_types = [
            NotificationAutomationJobType.WHATSAPP_FALLBACK,
            NotificationAutomationJobType.SMS_ESCALATION,
            NotificationAutomationJobType.PUSH_NOTIFICATION,
            NotificationAutomationJobType.CHANNEL_DELIVERY,
            NotificationAutomationJobType.FALLBACK_EMAIL,
        ]

        qs = NotificationAutomationJob.objects.filter(
            tenant_id=tenant_id,
            job_type__in=multi_channel_types,
        )

        st = request.query_params.get('status')
        if st:
            qs = qs.filter(status=st)

        qs = qs.order_by('-scheduled_for')[:100]

        data = [
            {
                'id': str(job.id),
                'job_type': job.job_type,
                'status': job.status,
                'event_key': job.event_key,
                'scheduled_for': job.scheduled_for.isoformat() if job.scheduled_for else None,
                'executed_at': job.executed_at.isoformat() if job.executed_at else None,
                'cancel_reason': job.cancel_reason,
                'notification_id': str(job.notification_id) if job.notification_id else None,
                'metadata': job.metadata,
            }
            for job in qs
        ]
        return Response({'results': data, 'count': len(data)})


# ---------------------------------------------------------------------------
# ChannelStatsView
# ---------------------------------------------------------------------------

class ChannelStatsView(APIView):
    """
    GET /api/v1/communications/channel-stats/

    Delivery stats per channel over the last 7 days.
    Returns: sent, failed, skipped, cancelled counts per channel.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.communications.channel_config_models import CommunicationDelivery

        if not _is_admin_or_staff(request.user):
            return Response({'detail': 'Permission denied.'}, status=403)

        tenant_id = _get_tenant_id_for_request(request)
        since = timezone.now() - timedelta(days=7)

        stats = (
            CommunicationDelivery.objects
            .filter(tenant_id=tenant_id, created_at__gte=since)
            .values('channel_type', 'status')
            .annotate(count=Count('id'))
            .order_by('channel_type', 'status')
        )

        # Pivot into {channel: {status: count}}
        result = {}
        for row in stats:
            ch = row['channel_type']
            st = row['status']
            result.setdefault(ch, {})
            result[ch][st] = row['count']

        return Response({
            'period_days': 7,
            'tenant_id': str(tenant_id),
            'channels': result,
        })


# ---------------------------------------------------------------------------
# TenantChannelConfigView
# ---------------------------------------------------------------------------

class TenantChannelConfigListView(APIView):
    """
    GET  /api/v1/communications/channel-configs/    — list configs
    POST /api/v1/communications/channel-configs/    — create config
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.communications.channel_config_models import TenantChannelConfig

        if not _is_admin_or_staff(request.user):
            return Response({'detail': 'Permission denied.'}, status=403)

        tenant_id = _get_tenant_id_for_request(request)
        configs = TenantChannelConfig.objects.filter(
            tenant_id=tenant_id,
            is_deleted=False,
        ).order_by('channel_type', '-created_at')

        data = [_serialise_channel_config(c) for c in configs]
        return Response({'results': data})

    def post(self, request):
        from apps.communications.channel_config_models import TenantChannelConfig
        from apps.communications.utils import encrypt_string

        if not _is_admin_or_staff(request.user):
            return Response({'detail': 'Permission denied.'}, status=403)

        tenant_id = _get_tenant_id_for_request(request)
        d = request.data

        channel_type = d.get('channel_type', '')
        provider     = d.get('provider', '')

        if channel_type not in ('whatsapp', 'sms', 'push'):
            return Response(
                {'detail': 'channel_type must be whatsapp, sms, or push'},
                status=400,
            )

        # Encrypt sensitive fields
        api_token_raw   = d.get('api_token', '')
        webhook_secret  = d.get('webhook_secret', '')
        vapid_private   = d.get('push_vapid_private_key', '')

        cfg = TenantChannelConfig.objects.create(
            tenant_id=tenant_id,
            channel_type=channel_type,
            provider=provider,
            sender_name=d.get('sender_name', ''),
            sender_identifier=d.get('sender_identifier', ''),
            api_key_id=d.get('api_key_id', ''),
            api_token_encrypted=encrypt_string(api_token_raw) if api_token_raw else '',
            webhook_secret_encrypted=encrypt_string(webhook_secret) if webhook_secret else '',
            whatsapp_phone_number_id=d.get('whatsapp_phone_number_id', ''),
            whatsapp_business_account_id=d.get('whatsapp_business_account_id', ''),
            whatsapp_api_version=d.get('whatsapp_api_version', 'v19.0'),
            sms_http_endpoint=d.get('sms_http_endpoint', ''),
            sms_http_method=d.get('sms_http_method', 'POST'),
            push_vapid_public_key=d.get('push_vapid_public_key', ''),
            push_vapid_private_key_encrypted=encrypt_string(vapid_private) if vapid_private else '',
            push_fcm_project_id=d.get('push_fcm_project_id', ''),
            is_active=d.get('is_active', True),
            config_json=d.get('config_json', {}),
            created_by=request.user.id,
        )
        return Response(_serialise_channel_config(cfg), status=201)


class TenantChannelConfigDetailView(APIView):
    """
    GET    /api/v1/communications/channel-configs/<id>/
    PATCH  /api/v1/communications/channel-configs/<id>/
    DELETE /api/v1/communications/channel-configs/<id>/
    """
    permission_classes = [IsAuthenticated]

    def _get_config(self, request, config_id):
        from apps.communications.channel_config_models import TenantChannelConfig
        tenant_id = _get_tenant_id_for_request(request)
        try:
            return TenantChannelConfig.objects.get(
                id=config_id, tenant_id=tenant_id, is_deleted=False
            )
        except TenantChannelConfig.DoesNotExist:
            raise NotFound('Channel config not found.')

    def get(self, request, config_id):
        if not _is_admin_or_staff(request.user):
            return Response({'detail': 'Permission denied.'}, status=403)
        cfg = self._get_config(request, config_id)
        return Response(_serialise_channel_config(cfg))

    def patch(self, request, config_id):
        from apps.communications.utils import encrypt_string

        if not _is_admin_or_staff(request.user):
            return Response({'detail': 'Permission denied.'}, status=403)

        cfg = self._get_config(request, config_id)
        d = request.data
        updatable = [
            'sender_name', 'sender_identifier', 'api_key_id',
            'whatsapp_phone_number_id', 'whatsapp_business_account_id', 'whatsapp_api_version',
            'sms_http_endpoint', 'sms_http_method', 'push_vapid_public_key',
            'push_fcm_project_id', 'is_active', 'is_default', 'config_json', 'provider',
        ]
        for field in updatable:
            if field in d:
                setattr(cfg, field, d[field])

        if 'api_token' in d and d['api_token']:
            cfg.api_token_encrypted = encrypt_string(d['api_token'])
        if 'webhook_secret' in d and d['webhook_secret']:
            cfg.webhook_secret_encrypted = encrypt_string(d['webhook_secret'])
        if 'push_vapid_private_key' in d and d['push_vapid_private_key']:
            cfg.push_vapid_private_key_encrypted = encrypt_string(d['push_vapid_private_key'])

        cfg.save()
        return Response(_serialise_channel_config(cfg))

    def delete(self, request, config_id):
        if not _is_admin_or_staff(request.user):
            return Response({'detail': 'Permission denied.'}, status=403)
        cfg = self._get_config(request, config_id)
        cfg.soft_delete()
        return Response(status=204)


# ---------------------------------------------------------------------------
# Serialisers (inline — no DRF ModelSerializer overhead for admin views)
# ---------------------------------------------------------------------------

def _serialise_delivery(d, full: bool = False) -> dict:
    data = {
        'id': str(d.id),
        'channel_type': d.channel_type,
        'provider': d.provider,
        'status': d.status,
        'priority': d.priority,
        'recipient_user_id': str(d.recipient_user_id) if d.recipient_user_id else None,
        'notification_id': str(d.notification_id) if d.notification_id else None,
        'template_used': d.template_used,
        'attempt_number': d.attempt_number,
        'scheduled_for': d.scheduled_for.isoformat() if d.scheduled_for else None,
        'attempted_at': d.attempted_at.isoformat() if d.attempted_at else None,
        'delivered_at': d.delivered_at.isoformat() if d.delivered_at else None,
        'created_at': d.created_at.isoformat(),
        'external_message_id': d.external_message_id,
        'skip_reason': d.skip_reason,
    }
    if full:
        data.update({
            'error_message': d.error_message,
            'external_status_payload': d.external_status_payload,
            'metadata': d.metadata,
        })
    return data


def _serialise_channel_config(cfg) -> dict:
    return {
        'id': str(cfg.id),
        'channel_type': cfg.channel_type,
        'provider': cfg.provider,
        'sender_name': cfg.sender_name,
        'sender_identifier': cfg.sender_identifier,
        'api_key_id': cfg.api_key_id,
        'api_token_masked': cfg.masked_api_token(),
        'whatsapp_phone_number_id': cfg.whatsapp_phone_number_id,
        'whatsapp_business_account_id': cfg.whatsapp_business_account_id,
        'whatsapp_api_version': cfg.whatsapp_api_version,
        'sms_http_endpoint': cfg.sms_http_endpoint,
        'push_vapid_public_key': cfg.push_vapid_public_key,
        'push_fcm_project_id': cfg.push_fcm_project_id,
        'is_active': cfg.is_active,
        'is_default': cfg.is_default,
        'config_json': cfg.config_json,
        'created_at': cfg.created_at.isoformat(),
        'updated_at': cfg.updated_at.isoformat(),
    }
