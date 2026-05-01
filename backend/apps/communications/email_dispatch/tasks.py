"""
Email Dispatch Celery Tasks
============================
Two task families:

1. send_email_task        — original task for business email (EmailDispatchService)
                            Kept for backwards compatibility.

2. deliver_email_task     — new task for automation/notification email delivery
                            Uses EmailDeliveryService + TenantEmailConfig + provider layer.
                            Implements exponential-backoff retry and priority queuing.

Queue configuration (add to Celery TASK_ROUTES in settings):
    'apps.communications.email_dispatch.tasks.deliver_email_task': {
        'queue': 'email_normal'   # default; service overrides per priority
    }
"""
import logging
from datetime import datetime

from celery import shared_task
from django.utils import timezone

from apps.communications.email_dispatch.dispatch import EmailDispatchService
from apps.communications.email_dispatch.types import EmailSendRequest

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Legacy task — business email (EmailDispatchService)
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='communications.email.send_email_task',
)
def send_email_task(self, payload: dict):
    """
    Send a business email via EmailDispatchService.
    Kept for backwards compatibility with email_dispatch/views.py.
    """
    schedule_at = payload.pop('schedule_at', None)
    if schedule_at:
        parsed_schedule = datetime.fromisoformat(schedule_at)
        if parsed_schedule.tzinfo is None:
            parsed_schedule = timezone.make_aware(parsed_schedule)
        if parsed_schedule > timezone.now():
            raise self.retry(countdown=int((parsed_schedule - timezone.now()).total_seconds()))

    request = EmailSendRequest(**payload)
    message = EmailDispatchService.send_now(request)
    return str(message.id)


# ---------------------------------------------------------------------------
# Automation delivery task
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    # Max retries is NOT set here — EmailDeliveryService controls the retry
    # schedule based on EmailDelivery.max_retries and RETRY_DELAYS.
    # We set acks_late=True so a crash doesn't silently drop the task.
    acks_late=True,
    name='communications.email.deliver_email_task',
)
def deliver_email_task(self, delivery_id: str):
    """
    Execute a single EmailDelivery.

    Flow:
        1. Load EmailDelivery record
        2. Guard: skip if not PENDING/DEFERRED
        3. Resolve TenantEmailConfig → provider
        4. Call provider.send()
        5. Mark SENT or schedule retry with exponential backoff
        6. Update EmailDelivery status

    Retry backoff is managed by EmailDeliveryService.schedule_retry(),
    NOT by Celery's built-in retry — this gives us full control over
    the retry schedule, queue routing, and permanent-failure alerting.
    """
    from apps.communications.email_delivery_models import (
        EmailDelivery,
        EmailDeliveryStatus,
        TenantEmailConfig,
    )
    from apps.communications.email_dispatch.providers import get_provider

    try:
        delivery = EmailDelivery.objects.get(id=delivery_id)
    except EmailDelivery.DoesNotExist:
        logger.warning('deliver_email_task: delivery %s not found — skipping', delivery_id)
        return

    # Idempotency guard — only act on PENDING or DEFERRED records
    if delivery.status not in (EmailDeliveryStatus.PENDING, EmailDeliveryStatus.DEFERRED):
        logger.debug(
            'deliver_email_task: delivery %s already in status=%s — skipping',
            delivery_id, delivery.status,
        )
        return

    delivery.mark_sending()

    # Resolve provider
    config = TenantEmailConfig.get_for_tenant(str(delivery.tenant_id))
    provider = get_provider(config)

    # Extract send params from metadata
    meta     = delivery.metadata or {}
    from_email  = meta.get('from_email', '')
    from_name   = meta.get('from_name', '')
    html_body   = meta.get('html_body', '')
    text_body   = meta.get('text_body', '')

    # Validate provider config before attempting send
    is_valid, config_error = provider.validate_config()
    if not is_valid:
        logger.error(
            'deliver_email_task: provider config invalid for delivery %s (%s): %s',
            delivery_id, provider.key, config_error,
        )
        delivery.error_message = f'Provider config invalid: {config_error}'
        delivery.save(update_fields=['error_message', 'updated_at'])
        _maybe_retry(delivery)
        return

    result = provider.send(
        from_email=from_email,
        from_name=from_name,
        to=[delivery.recipient_email],
        subject=delivery.subject,
        html_body=html_body,
        text_body=text_body,
        metadata={'delivery_id': delivery_id},
    )

    if result.ok:
        delivery.mark_sent(provider_message_id=result.provider_message_id)
        logger.info(
            'deliver_email_task: sent delivery %s via %s → %s',
            delivery_id, provider.key, delivery.recipient_email,
        )
        # Record success on linked notification
        _record_notification_delivery(delivery, status='sent', ext_id=result.provider_message_id)
    else:
        logger.warning(
            'deliver_email_task: send failed for delivery %s (%s): %s',
            delivery_id, provider.key, result.error[:200],
        )
        # Mark as FAILED first so can_retry() works correctly in schedule_retry
        delivery.mark_failed(error=result.error)
        _record_notification_delivery(delivery, status='failed', error=result.error)
        _maybe_retry(delivery)


# ---------------------------------------------------------------------------
# Internal helpers for deliver_email_task
# ---------------------------------------------------------------------------

def _maybe_retry(delivery):
    """Delegate retry scheduling to EmailDeliveryService."""
    from apps.communications.email_delivery_service import EmailDeliveryService
    EmailDeliveryService.schedule_retry(
        delivery_id=str(delivery.id),
        current_retry_count=delivery.retry_count,
    )


def _record_notification_delivery(delivery, *, status: str, ext_id: str = '', error: str = ''):
    """Update NotificationDelivery record if this email was for a notification."""
    if not delivery.notification_id:
        return
    try:
        from apps.communications.notification_service import NotificationService
        NotificationService.record_delivery_attempt(
            notification_id=str(delivery.notification_id),
            channel='email',
            provider=delivery.provider or 'system',
            status=status,
            external_message_id=ext_id,
            error_message=error[:500] if error else '',
            tenant_id=str(delivery.tenant_id),
        )
    except Exception as exc:
        logger.debug('_record_notification_delivery error: %s', exc)
