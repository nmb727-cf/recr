"""
Multi-Channel Celery Tasks
===========================
All async tasks for WhatsApp, SMS, and Push channel delivery.

Task naming:  communications.channel.*

All tasks are:
  • Idempotent    — safe to retry; check delivery status before acting
  • Multi-tenant safe — delivery record carries tenant_id
  • Failure-logged — errors recorded on CommunicationDelivery, never swallowed silently
  • Guard-gated   — won't double-send if already sent/skipped/cancelled

Dependency on channel_services.py for all actual send logic.
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# send_channel_delivery_task
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    name='communications.channel.send_channel_delivery',
)
def send_channel_delivery_task(self, delivery_id: str):
    """
    Execute a CommunicationDelivery record.

    Called immediately for immediate channel sends, or after a countdown
    for fallback/escalation sends.

    Guards:
      - Delivery must be PENDING
      - Notification must still be unread (for non-immediate sends)
    """
    from apps.communications.channel_config_models import (
        CommunicationDelivery,
        CommunicationDeliveryStatus,
    )

    try:
        delivery = CommunicationDelivery.objects.get(id=delivery_id)
    except CommunicationDelivery.DoesNotExist:
        logger.info('send_channel_delivery_task: delivery %s not found', delivery_id)
        return

    if delivery.status != CommunicationDeliveryStatus.PENDING:
        logger.debug(
            'send_channel_delivery_task: delivery %s is %s — skipping',
            delivery_id, delivery.status,
        )
        return

    from apps.communications.channel_services import execute_channel_delivery
    success = execute_channel_delivery(delivery_id)

    if not success and delivery.status == CommunicationDeliveryStatus.DEFERRED:
        # Already re-queued by execute_channel_delivery via retry_channel_delivery_task
        pass
    elif not success and delivery.status == CommunicationDeliveryStatus.FAILED:
        logger.warning(
            'send_channel_delivery_task: delivery %s failed (no retry scheduled)',
            delivery_id,
        )


# ---------------------------------------------------------------------------
# retry_channel_delivery_task
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=180,
    name='communications.channel.retry_channel_delivery',
)
def retry_channel_delivery_task(self, delivery_id: str):
    """
    Retry a DEFERRED or FAILED CommunicationDelivery.

    Called by _perform_delivery() when a retryable error is returned.
    Resets delivery to PENDING and delegates to execute_channel_delivery.
    """
    from apps.communications.channel_config_models import (
        CommunicationDelivery,
        CommunicationDeliveryStatus,
    )

    try:
        delivery = CommunicationDelivery.objects.get(id=delivery_id)
    except CommunicationDelivery.DoesNotExist:
        logger.info('retry_channel_delivery_task: delivery %s not found', delivery_id)
        return

    if not delivery.can_retry():
        logger.debug(
            'retry_channel_delivery_task: delivery %s cannot retry (status=%s, attempts=%d/%d)',
            delivery_id, delivery.status, delivery.attempt_number, delivery.max_attempts,
        )
        return

    # Reset to pending for re-execution
    delivery.status = CommunicationDeliveryStatus.PENDING
    delivery.save(update_fields=['status', 'updated_at'])

    from apps.communications.channel_services import execute_channel_delivery
    success = execute_channel_delivery(delivery_id)

    if not success:
        try:
            # Re-check after execute — if still failed and can retry, raise to trigger Celery retry
            delivery.refresh_from_db()
            if delivery.can_retry():
                raise self.retry(countdown=180)
        except self.MaxRetriesExceededError:
            logger.error(
                'retry_channel_delivery_task: delivery %s exhausted all retries', delivery_id
            )


# ---------------------------------------------------------------------------
# execute_channel_fallback_task
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    name='communications.channel.execute_channel_fallback',
)
def execute_channel_fallback_task(self, delivery_id: str):
    """
    Execute a scheduled channel fallback delivery (WhatsApp fallback, SMS escalation).

    Additional guard: checks that the notification is still unread before sending.
    If read, marks delivery as CANCELLED.
    """
    from apps.communications.channel_config_models import (
        CommunicationDelivery,
        CommunicationDeliveryStatus,
    )

    try:
        delivery = CommunicationDelivery.objects.get(id=delivery_id)
    except CommunicationDelivery.DoesNotExist:
        logger.info('execute_channel_fallback_task: delivery %s not found', delivery_id)
        return

    if delivery.status != CommunicationDeliveryStatus.PENDING:
        logger.debug(
            'execute_channel_fallback_task: delivery %s is %s — skipping',
            delivery_id, delivery.status,
        )
        return

    # Guard: notification read check for fallback/escalation sends
    if delivery.notification_id:
        try:
            from apps.communications.models import Notification
            n = Notification.objects.filter(id=delivery.notification_id).first()
            if n and n.is_read:
                delivery.mark_cancelled(reason='notification_read')
                logger.debug(
                    'execute_channel_fallback_task: notification %s read — cancelled delivery %s',
                    delivery.notification_id, delivery_id,
                )
                return
        except Exception as exc:
            logger.debug('Could not check notification read state: %s', exc)

    from apps.communications.channel_services import execute_channel_delivery
    success = execute_channel_delivery(delivery_id)

    if not success:
        try:
            delivery.refresh_from_db()
            if delivery.can_retry():
                raise self.retry(countdown=120)
        except self.MaxRetriesExceededError:
            logger.error(
                'execute_channel_fallback_task: exhausted retries for delivery %s', delivery_id
            )


# ---------------------------------------------------------------------------
# cancel_pending_channel_jobs_for_notification
# ---------------------------------------------------------------------------

@shared_task(
    name='communications.channel.cancel_pending_channel_jobs_for_notification',
)
def cancel_pending_channel_jobs_for_notification(notification_id: str, reason: str = 'notification_read'):
    """
    Cancel all PENDING CommunicationDelivery records for a notification.

    Called when a notification is marked as read/resolved.
    Also cancels corresponding NotificationAutomationJob records.
    Safe to call from high-traffic code paths.
    """
    from apps.communications.channel_services import cancel_channel_fallbacks
    from apps.communications.notification_orchestration_service import cancel_pending_jobs

    # Cancel channel deliveries
    cancelled_deliveries = cancel_channel_fallbacks(
        notification_id=notification_id,
        reason=reason,
    )

    # Cancel orchestration jobs (covers fallback_email, whatsapp_fallback, sms_escalation, etc.)
    cancelled_jobs = cancel_pending_jobs(
        notification_id=notification_id,
        reason=reason,
    )

    logger.debug(
        'cancel_pending_channel_jobs: notification=%s cancelled %d deliveries + %d jobs (reason=%s)',
        notification_id, cancelled_deliveries, cancelled_jobs, reason,
    )


# ---------------------------------------------------------------------------
# send_whatsapp_notification (direct, non-fallback path)
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    name='communications.channel.send_whatsapp_notification',
)
def send_whatsapp_notification_task(
    self,
    tenant_id: str,
    recipient_phone: str,
    body: str,
    template_name: str = '',
    template_params: dict = None,
    notification_id: str = None,
    metadata: dict = None,
):
    """
    Direct WhatsApp send task (bypasses the standard delivery flow).

    Used for manual sends or direct API calls from business modules.
    Creates a CommunicationDelivery record for tracking.
    """
    from apps.communications.channel_services import (
        resolve_channel_provider,
        normalize_recipient_for_channel,
        record_delivery_attempt,
    )
    from apps.communications.providers.base import ProviderSendError, ProviderUnavailableError

    normalised = normalize_recipient_for_channel(
        channel_type='whatsapp', identifier=recipient_phone
    )
    if not normalised:
        logger.warning(
            'send_whatsapp_notification_task: invalid phone %s',
            recipient_phone[-4:] if len(recipient_phone) >= 4 else '****',
        )
        return

    provider = resolve_channel_provider(tenant_id, 'whatsapp')
    if provider is None:
        logger.warning(
            'send_whatsapp_notification_task: no WhatsApp provider for tenant=%s', tenant_id
        )
        return

    try:
        result = provider.send(
            recipient=normalised,
            body=body,
            template_name=template_name,
            template_params=template_params or {},
            metadata=metadata or {},
        )
        status = 'sent' if result.success else 'failed'
        ext_id = result.external_message_id
    except ProviderSendError as exc:
        status = 'failed'
        ext_id = ''
        if exc.retryable:
            try:
                raise self.retry(countdown=60)
            except self.MaxRetriesExceededError:
                pass
    except ProviderUnavailableError as exc:
        try:
            raise self.retry(countdown=120)
        except self.MaxRetriesExceededError:
            status = 'failed'
            ext_id = ''
    except Exception as exc:
        logger.error('send_whatsapp_notification_task error: %s', exc)
        status = 'failed'
        ext_id = ''

    record_delivery_attempt(
        tenant_id=tenant_id,
        channel_type='whatsapp',
        notification_id=notification_id,
        recipient_identifier=normalised,
        status=status,
        provider=getattr(provider, 'PROVIDER_NAME', ''),
        external_message_id=ext_id,
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# send_sms_notification_task (direct, non-fallback path)
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    name='communications.channel.send_sms_notification',
)
def send_sms_notification_task(
    self,
    tenant_id: str,
    recipient_phone: str,
    body: str,
    notification_id: str = None,
    metadata: dict = None,
):
    """Direct SMS send task."""
    from apps.communications.channel_services import (
        resolve_channel_provider,
        normalize_recipient_for_channel,
        record_delivery_attempt,
    )
    from apps.communications.providers.base import ProviderSendError, ProviderUnavailableError

    normalised = normalize_recipient_for_channel(
        channel_type='sms', identifier=recipient_phone
    )
    if not normalised:
        return

    provider = resolve_channel_provider(tenant_id, 'sms')
    if provider is None:
        logger.warning('send_sms_notification_task: no SMS provider for tenant=%s', tenant_id)
        return

    # Truncate to SMS safe limit
    body = body[:306]

    try:
        result = provider.send(
            recipient=normalised,
            body=body,
            metadata=metadata or {},
        )
        status = 'sent' if result.success else 'failed'
        ext_id = result.external_message_id
    except ProviderSendError as exc:
        status = 'failed'
        ext_id = ''
        if exc.retryable:
            try:
                raise self.retry(countdown=60)
            except self.MaxRetriesExceededError:
                pass
    except ProviderUnavailableError:
        try:
            raise self.retry(countdown=120)
        except self.MaxRetriesExceededError:
            status = 'failed'
            ext_id = ''
    except Exception as exc:
        logger.error('send_sms_notification_task error: %s', exc)
        status = 'failed'
        ext_id = ''

    record_delivery_attempt(
        tenant_id=tenant_id,
        channel_type='sms',
        notification_id=notification_id,
        recipient_identifier=normalised,
        status=status,
        provider=getattr(provider, 'PROVIDER_NAME', ''),
        external_message_id=ext_id,
        metadata=metadata or {},
    )
