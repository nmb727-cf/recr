"""
Channel Delivery Services
==========================
All outbound delivery logic for WhatsApp, SMS, and Push channels.

This module is the execution layer.  The routing layer (channel_routing.py)
decides WHAT to send and WHEN.  This module does the actual sending.

Public API:
    send_via_channel(...)                 — high-level: resolve provider, render, send, track
    execute_channel_delivery(delivery_id) — execute a CommunicationDelivery record
    schedule_channel_fallback(...)        — schedule a delayed channel send job
    cancel_channel_fallbacks(...)         — cancel pending fallback jobs for a notification
    normalize_recipient_for_channel(...)  — validate + normalise phone / push token
    record_delivery_attempt(...)          — create or update a CommunicationDelivery record
    mark_delivery_status(...)             — update delivery status

Architecture:
    • Never import business modules (candidates, jobs, etc.) at module level
    • All exceptions swallowed at the public API layer — never break notification flow
    • Each delivery attempt gets its own CommunicationDelivery row
    • Celery tasks call execute_channel_delivery(delivery_id) for idempotent sends
"""
import logging
import uuid
from datetime import timedelta
from typing import Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# send_via_channel — high-level entry point
# ---------------------------------------------------------------------------

def send_via_channel(
    *,
    tenant_id,
    channel_type: str,
    recipient_identifier: str,
    recipient_user_id=None,
    notification_id=None,
    automation_job_id=None,
    event_key: str = '',
    priority: str = 'medium',
    template=None,          # ChannelTemplate or None
    context: dict = None,
    notification=None,      # Notification model instance or None
    schedule_async: bool = True,
) -> Optional[object]:
    """
    High-level: render content, create delivery record, and dispatch.

    If schedule_async=True (default): creates CommunicationDelivery and
    queues send_channel_delivery_task for async execution.

    If schedule_async=False: executes synchronously (for immediate channels
    in the request path when needed).

    Returns the CommunicationDelivery instance, or None on fatal config failure.
    """
    from apps.communications.channel_config_models import (
        CommunicationDelivery,
        CommunicationDeliveryPriority,
        CommunicationDeliveryStatus,
    )
    from apps.communications.channel_template_service import render_channel_template

    # Validate recipient
    normalised = normalize_recipient_for_channel(
        channel_type=channel_type,
        identifier=recipient_identifier,
    )
    if not normalised:
        logger.warning(
            'send_via_channel: invalid/missing recipient for channel=%s user=%s',
            channel_type, recipient_user_id,
        )
        # Still record the attempt as skipped
        return _record_skipped(
            tenant_id=tenant_id,
            channel_type=channel_type,
            recipient_user_id=recipient_user_id,
            notification_id=notification_id,
            automation_job_id=automation_job_id,
            reason='no_recipient_identifier',
        )

    # Render content for this channel
    try:
        rendered = render_channel_template(
            channel_type=channel_type,
            template=template,
            context=context,
            notification=notification,
        )
    except Exception as exc:
        logger.error('Template render failed for channel=%s: %s', channel_type, exc)
        rendered = None

    prio_map = {
        'info': CommunicationDeliveryPriority.LOW,
        'low':  CommunicationDeliveryPriority.LOW,
        'medium': CommunicationDeliveryPriority.MEDIUM,
        'high': CommunicationDeliveryPriority.HIGH,
        'critical': CommunicationDeliveryPriority.CRITICAL,
    }

    delivery = CommunicationDelivery.objects.create(
        tenant_id=tenant_id,
        notification_id=notification_id,
        automation_job_id=automation_job_id,
        channel_type=channel_type,
        recipient_identifier=normalised,
        recipient_user_id=recipient_user_id,
        template_used=getattr(rendered, 'template_name', '') if rendered else '',
        rendered_body=getattr(rendered, 'body', '') if rendered else '',
        rendered_subject=getattr(rendered, 'subject', '') if rendered else '',
        status=CommunicationDeliveryStatus.PENDING,
        priority=prio_map.get(priority, CommunicationDeliveryPriority.MEDIUM),
        metadata={
            'event_key': event_key,
            'template_params': getattr(rendered, 'template_params', {}) if rendered else {},
        },
    )

    if schedule_async:
        try:
            from apps.communications.channel_tasks import send_channel_delivery_task
            send_channel_delivery_task.apply_async(
                args=[str(delivery.id)],
                countdown=0,
            )
        except Exception as exc:
            logger.error('Failed to enqueue send_channel_delivery_task: %s', exc)
    else:
        _perform_delivery(delivery, rendered)

    return delivery


# ---------------------------------------------------------------------------
# execute_channel_delivery — called by Celery task
# ---------------------------------------------------------------------------

def execute_channel_delivery(delivery_id: str) -> bool:
    """
    Load a CommunicationDelivery by ID and execute it.

    Idempotency guards:
      - Only execute PENDING deliveries
      - Check notification is still unread before sending (for fallback/escalation)
      - Record outcome on the delivery record

    Returns True on successful send, False otherwise.
    """
    from apps.communications.channel_config_models import (
        CommunicationDelivery,
        CommunicationDeliveryStatus,
    )

    try:
        delivery = CommunicationDelivery.objects.get(id=delivery_id)
    except CommunicationDelivery.DoesNotExist:
        logger.info('execute_channel_delivery: delivery %s not found', delivery_id)
        return False

    if delivery.status != CommunicationDeliveryStatus.PENDING:
        logger.debug(
            'execute_channel_delivery: delivery %s is %s — skipping',
            delivery_id, delivery.status,
        )
        return delivery.status == CommunicationDeliveryStatus.SENT

    # Guard: if notification was read, cancel fallback/escalation sends
    if delivery.notification_id and delivery.channel_type not in ('in_app', 'email'):
        try:
            from apps.communications.models import Notification
            n = Notification.objects.filter(id=delivery.notification_id).first()
            if n and n.is_read:
                delivery.mark_cancelled(reason='notification_read')
                logger.debug(
                    'execute_channel_delivery: notification %s already read — cancelled delivery %s',
                    delivery.notification_id, delivery_id,
                )
                return False
        except Exception:
            pass

    # Re-build ChannelTemplate from delivery metadata
    template_params = delivery.metadata.get('template_params', {})
    template = None
    if delivery.template_used or delivery.rendered_body:
        from apps.communications.channel_template_service import ChannelTemplate
        template = ChannelTemplate(
            channel_type=delivery.channel_type,
            body_template=delivery.rendered_body,
            subject_template=delivery.rendered_subject,
            template_name=delivery.template_used,
            template_params_keys=list(template_params.keys()),
        )

    from apps.communications.channel_template_service import render_channel_template, RenderedMessage
    rendered = RenderedMessage(
        channel_type=delivery.channel_type,
        subject=delivery.rendered_subject,
        body=delivery.rendered_body,
        template_name=delivery.template_used,
        template_params=template_params,
    )

    return _perform_delivery(delivery, rendered)


# ---------------------------------------------------------------------------
# schedule_channel_fallback
# ---------------------------------------------------------------------------

def schedule_channel_fallback(
    *,
    tenant_id,
    notification_id,
    event_key: str,
    channel_step,     # ChannelStep instance
    recipient_identifier: str,
    recipient_user_id=None,
    priority: str = 'medium',
    template=None,
    context: dict = None,
    notification=None,
) -> Optional[object]:
    """
    Schedule a CommunicationDelivery to be executed after the step's delay.

    Creates the delivery record immediately in PENDING state with
    scheduled_for set, then queues the Celery task with the appropriate
    countdown.

    Returns the CommunicationDelivery or None.
    """
    from apps.communications.channel_config_models import (
        CommunicationDelivery,
        CommunicationDeliveryPriority,
        CommunicationDeliveryStatus,
    )
    from apps.communications.channel_template_service import render_channel_template
    from apps.communications.notification_orchestration_service import schedule_automation_job
    from apps.communications.notification_orchestration_models import NotificationAutomationJobType

    normalised = normalize_recipient_for_channel(
        channel_type=channel_step.channel_type,
        identifier=recipient_identifier,
    )
    if not normalised:
        logger.warning(
            'schedule_channel_fallback: no valid recipient for channel=%s',
            channel_step.channel_type,
        )
        return None

    # Render content now (at scheduling time)
    try:
        rendered = render_channel_template(
            channel_type=channel_step.channel_type,
            template=template,
            context=context,
            notification=notification,
        )
    except Exception as exc:
        logger.error('Template render failed at schedule time: %s', exc)
        rendered = None

    prio_map = {'low': 'low', 'medium': 'medium', 'high': 'high', 'critical': 'critical'}
    scheduled_for = timezone.now() + timedelta(seconds=channel_step.delay_seconds)

    delivery = CommunicationDelivery.objects.create(
        tenant_id=tenant_id,
        notification_id=notification_id,
        channel_type=channel_step.channel_type,
        recipient_identifier=normalised,
        recipient_user_id=recipient_user_id,
        template_used=getattr(rendered, 'template_name', '') if rendered else '',
        rendered_body=getattr(rendered, 'body', '') if rendered else '',
        rendered_subject=getattr(rendered, 'subject', '') if rendered else '',
        status=CommunicationDeliveryStatus.PENDING,
        priority=prio_map.get(priority, 'medium'),
        scheduled_for=scheduled_for,
        metadata={
            'event_key': event_key,
            'is_fallback': channel_step.is_fallback,
            'is_escalation': channel_step.is_escalation,
            'template_params': getattr(rendered, 'template_params', {}) if rendered else {},
        },
    )

    # Determine job type
    job_type_map = {
        'whatsapp': NotificationAutomationJobType.WHATSAPP_FALLBACK
        if channel_step.is_fallback else NotificationAutomationJobType.REMINDER,
        'sms': NotificationAutomationJobType.SMS_ESCALATION
        if channel_step.is_escalation else NotificationAutomationJobType.REMINDER,
    }
    job_type = job_type_map.get(
        channel_step.channel_type,
        NotificationAutomationJobType.REMINDER,
    )

    # Create automation job for tracking and cancellation
    try:
        job = schedule_automation_job(
            tenant_id=tenant_id,
            notification_id=notification_id,
            event_key=event_key,
            job_type=job_type,
            delay_seconds=channel_step.delay_seconds,
            metadata={
                'delivery_id': str(delivery.id),
                'channel_type': channel_step.channel_type,
            },
        )
        # Link delivery to automation job
        delivery.automation_job_id = job.id
        delivery.save(update_fields=['automation_job_id', 'updated_at'])
    except Exception as exc:
        logger.warning('Could not create automation job for channel fallback: %s', exc)

    # Queue the Celery task
    try:
        from apps.communications.channel_tasks import send_channel_delivery_task
        send_channel_delivery_task.apply_async(
            args=[str(delivery.id)],
            countdown=channel_step.delay_seconds,
        )
    except Exception as exc:
        logger.error('Failed to enqueue fallback channel task: %s', exc)

    return delivery


# ---------------------------------------------------------------------------
# cancel_channel_fallbacks
# ---------------------------------------------------------------------------

def cancel_channel_fallbacks(
    *,
    notification_id,
    reason: str = 'notification_read',
) -> int:
    """
    Cancel all PENDING CommunicationDelivery records for a notification.

    Should be called when a notification is marked as read.
    Returns count of cancelled deliveries.
    """
    from apps.communications.channel_config_models import (
        CommunicationDelivery,
        CommunicationDeliveryStatus,
    )

    cancelled = CommunicationDelivery.objects.filter(
        notification_id=notification_id,
        status=CommunicationDeliveryStatus.PENDING,
    ).update(
        status=CommunicationDeliveryStatus.CANCELLED,
        skip_reason=reason,
        updated_at=timezone.now(),
    )

    if cancelled:
        logger.debug(
            'cancel_channel_fallbacks: cancelled %d deliveries for notification %s (reason=%s)',
            cancelled, notification_id, reason,
        )
    return cancelled


# ---------------------------------------------------------------------------
# normalize_recipient_for_channel
# ---------------------------------------------------------------------------

def normalize_recipient_for_channel(
    *,
    channel_type: str,
    identifier: str,
) -> str:
    """
    Validate and normalise a recipient identifier for the given channel.

    Returns:
        Normalised identifier string, or '' if invalid.

    Rules:
        whatsapp / sms: E.164 phone number (starts with +, digits only after)
        push:           any non-empty string (push token or user ID)
        in_app:         any non-empty string (user ID)
        email:          basic @ check
    """
    if not identifier:
        return ''

    if channel_type in ('whatsapp', 'sms'):
        cleaned = ''.join(c for c in identifier if c.isdigit() or c == '+')
        if not cleaned.startswith('+'):
            cleaned = f'+{cleaned}'
        # Minimum E.164: +CCNUMBER (7 digits minimum after country code)
        digits_only = cleaned.lstrip('+')
        if len(digits_only) < 7:
            return ''
        return cleaned

    if channel_type == 'email':
        if '@' in identifier and len(identifier) > 3:
            return identifier.strip().lower()
        return ''

    # push, in_app — any non-empty string
    return identifier.strip()


# ---------------------------------------------------------------------------
# record_delivery_attempt  (for non-WhatsApp/SMS channels — compat layer)
# ---------------------------------------------------------------------------

def record_delivery_attempt(
    *,
    tenant_id,
    channel_type: str,
    notification_id=None,
    recipient_identifier: str = '',
    recipient_user_id=None,
    status: str,
    provider: str = '',
    external_message_id: str = '',
    error_message: str = '',
    metadata: dict = None,
) -> object:
    """
    Create a CommunicationDelivery record for a completed send attempt.
    Used when the send was triggered outside the standard flow (e.g. direct API call).
    """
    from apps.communications.channel_config_models import (
        CommunicationDelivery,
        CommunicationDeliveryStatus,
    )

    return CommunicationDelivery.objects.create(
        tenant_id=tenant_id,
        notification_id=notification_id,
        channel_type=channel_type,
        provider=provider,
        recipient_identifier=recipient_identifier or '',
        recipient_user_id=recipient_user_id,
        status=status,
        external_message_id=external_message_id,
        error_message=error_message[:2000] if error_message else '',
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# mark_delivery_status
# ---------------------------------------------------------------------------

def mark_delivery_status(
    *,
    delivery_id,
    status: str,
    external_message_id: str = '',
    error_message: str = '',
    payload: dict = None,
) -> bool:
    """
    Update a CommunicationDelivery record's status.
    Called from webhook handlers or status sync tasks.
    Returns True if the record was found and updated.
    """
    from apps.communications.channel_config_models import (
        CommunicationDelivery,
        CommunicationDeliveryStatus,
    )

    try:
        delivery = CommunicationDelivery.objects.get(id=delivery_id)
    except CommunicationDelivery.DoesNotExist:
        return False

    st_map = {
        'sent':      delivery.mark_sent,
        'delivered': delivery.mark_delivered,
        'read':      delivery.mark_read,
        'failed':    delivery.mark_failed,
        'cancelled': delivery.mark_cancelled,
        'skipped':   delivery.mark_skipped,
    }
    handler = st_map.get(status)
    if handler:
        try:
            if status == 'sent':
                handler(external_message_id=external_message_id, payload=payload or {})
            elif status in ('delivered', 'read'):
                handler(payload=payload or {})
            elif status in ('failed',):
                handler(error=error_message, payload=payload or {})
            elif status in ('cancelled', 'skipped'):
                handler(reason=error_message or '')
            else:
                handler()
        except Exception as exc:
            logger.warning('mark_delivery_status: handler error for %s: %s', status, exc)
    else:
        delivery.status = status
        delivery.save(update_fields=['status', 'updated_at'])

    return True


# ---------------------------------------------------------------------------
# resolve_channel_provider
# ---------------------------------------------------------------------------

def resolve_channel_provider(tenant_id, channel_type: str):
    """
    Resolve and instantiate the configured provider for (tenant_id, channel_type).

    Returns:
        BaseChannelProvider instance, or None if not configured.
    """
    from apps.communications.channel_config_models import TenantChannelConfig
    from apps.communications.providers import get_provider, ProviderConfigError

    config_obj = TenantChannelConfig.get_active(tenant_id, channel_type)
    if config_obj is None:
        logger.debug(
            'resolve_channel_provider: no active config for tenant=%s channel=%s',
            tenant_id, channel_type,
        )
        return None

    # Build config dict for provider
    config = {
        'api_token':                   config_obj.decrypted_api_token,
        'api_key_id':                  config_obj.api_key_id,
        'sender_identifier':           config_obj.sender_identifier,
        'sender_name':                 config_obj.sender_name,
        'whatsapp_phone_number_id':    config_obj.whatsapp_phone_number_id,
        'whatsapp_business_account_id': config_obj.whatsapp_business_account_id,
        'whatsapp_api_version':        config_obj.whatsapp_api_version,
        'sms_http_endpoint':           config_obj.sms_http_endpoint,
        'sms_http_method':             config_obj.sms_http_method,
        'push_vapid_public_key':       config_obj.push_vapid_public_key,
        'push_vapid_private_key':      config_obj.decrypted_vapid_private_key,
        'push_fcm_project_id':         config_obj.push_fcm_project_id,
        **config_obj.config_json,
    }

    try:
        return get_provider(
            channel_type=channel_type,
            provider_name=config_obj.provider or 'mock',
            config=config,
        )
    except ProviderConfigError as exc:
        logger.error(
            'resolve_channel_provider: config error for tenant=%s channel=%s: %s',
            tenant_id, channel_type, exc,
        )
        return None


# ---------------------------------------------------------------------------
# Internal: _perform_delivery
# ---------------------------------------------------------------------------

def _perform_delivery(delivery, rendered) -> bool:
    """
    Execute the actual send using the resolved provider.
    Updates delivery record status on success or failure.
    Returns True on success.
    """
    from apps.communications.channel_config_models import CommunicationDeliveryStatus
    from apps.communications.providers.base import (
        ProviderSendError, ProviderUnavailableError
    )

    provider = resolve_channel_provider(delivery.tenant_id, delivery.channel_type)

    if provider is None:
        delivery.mark_skipped(reason='no_provider_configured')
        logger.warning(
            '_perform_delivery: no provider for tenant=%s channel=%s — skipped delivery %s',
            delivery.tenant_id, delivery.channel_type, delivery.id,
        )
        return False

    delivery.mark_sending()

    template_params = {}
    if rendered:
        template_params = getattr(rendered, 'template_params', {}) or {}

    try:
        result = provider.send(
            recipient=delivery.recipient_identifier,
            body=rendered.body if rendered else '',
            subject=rendered.subject if rendered else '',
            template_name=rendered.template_name if rendered else '',
            template_params=template_params,
            metadata={
                'tenant_id':       str(delivery.tenant_id),
                'notification_id': str(delivery.notification_id) if delivery.notification_id else '',
                'delivery_id':     str(delivery.id),
            },
        )
    except ProviderSendError as exc:
        logger.warning(
            '_perform_delivery: send error on channel=%s delivery=%s: %s (retryable=%s)',
            delivery.channel_type, delivery.id, exc, exc.retryable,
        )
        if exc.retryable and delivery.attempt_number < delivery.max_attempts:
            retry_delay = _backoff_seconds(delivery.attempt_number)
            delivery.mark_deferred(
                next_retry_at=timezone.now() + timedelta(seconds=retry_delay),
                error=str(exc),
            )
            # Re-queue
            try:
                from apps.communications.channel_tasks import retry_channel_delivery_task
                retry_channel_delivery_task.apply_async(
                    args=[str(delivery.id)],
                    countdown=retry_delay,
                )
            except Exception:
                pass
        else:
            delivery.mark_failed(error=str(exc))
        return False

    except ProviderUnavailableError as exc:
        logger.error(
            '_perform_delivery: provider unavailable for channel=%s: %s',
            delivery.channel_type, exc,
        )
        # can_retry() checks status ∈ {FAILED, DEFERRED}, but we're still PENDING here.
        # Use raw attempt count to decide retryability.
        if delivery.attempt_number < delivery.max_attempts:
            retry_delay = _backoff_seconds(delivery.attempt_number)
            delivery.mark_deferred(
                next_retry_at=timezone.now() + timedelta(seconds=retry_delay),
                error=str(exc),
            )
            try:
                from apps.communications.channel_tasks import retry_channel_delivery_task
                retry_channel_delivery_task.apply_async(
                    args=[str(delivery.id)],
                    countdown=retry_delay,
                )
            except Exception:
                pass
        else:
            delivery.mark_failed(error=str(exc))
        return False

    except Exception as exc:
        logger.error(
            '_perform_delivery: unexpected error on channel=%s delivery=%s: %s',
            delivery.channel_type, delivery.id, exc,
        )
        delivery.mark_failed(error=str(exc)[:500])
        return False

    # Check for placeholder push (success=False with push_not_implemented)
    if not result.success and result.error == 'push_not_implemented':
        delivery.mark_skipped(reason='push_not_implemented')
        return False

    if result.success:
        delivery.mark_sent(
            external_message_id=result.external_message_id,
            payload=result.raw_response,
        )
        logger.info(
            '_perform_delivery: sent via channel=%s delivery=%s ext_id=%s',
            delivery.channel_type, delivery.id, result.external_message_id,
        )
        return True
    else:
        delivery.mark_failed(error=result.error or 'unknown provider error')
        return False


def _record_skipped(*, tenant_id, channel_type, recipient_user_id, notification_id,
                    automation_job_id, reason: str):
    from apps.communications.channel_config_models import (
        CommunicationDelivery, CommunicationDeliveryStatus
    )
    return CommunicationDelivery.objects.create(
        tenant_id=tenant_id,
        notification_id=notification_id,
        automation_job_id=automation_job_id,
        channel_type=channel_type,
        recipient_user_id=recipient_user_id,
        status=CommunicationDeliveryStatus.SKIPPED,
        skip_reason=reason,
    )


def _backoff_seconds(attempt: int) -> int:
    """Exponential backoff: 60s, 180s, 540s, cap at 900s."""
    return min(60 * (3 ** (attempt - 1)), 900)
