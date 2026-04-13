"""
Notification Orchestration Celery Tasks
=========================================
All tasks are:
  - Idempotent: safe to re-run if Celery retries
  - Job-status-gated: check NotificationAutomationJob.status before acting
  - Cross-tenant safe: each job carries tenant_id and validates it
  - Logged: failures recorded on the job, not silently swallowed

Task naming:
  communications.orchestration.*

All tasks import models lazily (inside the function body) to avoid
Django app-registry issues when Celery workers start.
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# execute_fallback_job
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    name='communications.orchestration.execute_fallback_job',
)
def execute_fallback_job(self, job_id: str):
    """
    Execute a fallback email job.

    Guards:
      - Job must still be PENDING (not cancelled, not already executed)
      - Notification must still be unread
      - Fallback email must not have been sent already
    """
    from apps.communications.notification_orchestration_models import (
        NotificationAutomationJob,
        NotificationAutomationJobStatus,
    )

    job = _load_job(job_id)
    if job is None:
        return

    if job.status != NotificationAutomationJobStatus.PENDING:
        logger.debug(
            'execute_fallback_job: job %s is %s — skipping.', job_id, job.status
        )
        return

    notification = job.notification
    if notification is None:
        job.mark_skipped()
        return

    # Guard: already read
    if notification.is_read:
        job.cancel(reason='notification_read')
        logger.debug('Fallback skipped — notification %s already read.', notification.id)
        return

    # Guard: fallback already sent
    if notification.fallback_email_sent_at:
        job.mark_skipped()
        _maybe_schedule_escalation(job, notification)
        return

    # Send fallback email
    success = _send_fallback_email_for_notification(notification, job)

    if success:
        job.mark_executed()
        # Schedule escalation job if rule says so
        _maybe_schedule_escalation(job, notification)
    else:
        job.mark_failed()
        try:
            raise self.retry(countdown=120)
        except self.MaxRetriesExceededError:
            logger.error('Fallback job %s exhausted retries.', job_id)


# ---------------------------------------------------------------------------
# execute_escalation_job
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    name='communications.orchestration.execute_escalation_job',
)
def execute_escalation_job(self, job_id: str):
    """
    Execute an escalation job.

    - Resolves the escalation target from the rule's escalation_target_type
    - Creates an in-app notification for the target
    - Sends an email if the email channel is enabled
    - Records a NotificationEscalationLog entry
    - Guards against notification already read, job already cancelled, etc.
    """
    from apps.communications.notification_orchestration_models import (
        NotificationAutomationJob,
        NotificationAutomationJobStatus,
    )

    job = _load_job(job_id)
    if job is None:
        return

    if job.status != NotificationAutomationJobStatus.PENDING:
        logger.debug(
            'execute_escalation_job: job %s is %s — skipping.', job_id, job.status
        )
        return

    notification = job.notification
    if notification is None:
        job.mark_skipped()
        return

    # Guard: already read — no need to escalate
    if notification.is_read:
        job.cancel(reason='notification_read')
        return

    _perform_escalation(job, notification)


# ---------------------------------------------------------------------------
# execute_reminder_job
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    name='communications.orchestration.execute_reminder_job',
)
def execute_reminder_job(self, job_id: str):
    """
    Execute a reminder job.

    Reminders are safe-repeat: they re-check whether the underlying entity
    is still unresolved before sending.  The job metadata carries:
      - reminder_count: how many have been sent so far
      - max_reminders: maximum allowed
      - entity_resolved_check: type / id to verify is still pending
    """
    from apps.communications.notification_orchestration_models import (
        NotificationAutomationJob,
        NotificationAutomationJobStatus,
    )

    job = _load_job(job_id)
    if job is None:
        return

    if job.status != NotificationAutomationJobStatus.PENDING:
        return

    notification = job.notification
    if notification is None:
        job.mark_skipped()
        return

    meta = job.metadata or {}
    reminder_count = meta.get('reminder_count', 0)
    max_reminders = meta.get('max_reminders', 3)

    # Guard: max reminders reached
    if reminder_count >= max_reminders:
        job.mark_skipped()
        logger.debug(
            'Reminder job %s: max_reminders=%d reached — skipping.', job_id, max_reminders
        )
        return

    # Guard: notification read
    if notification.is_read:
        job.cancel(reason='notification_read')
        return

    # Guard: entity already resolved
    entity_resolved = _check_entity_resolved(
        entity_type=job.related_entity_type,
        entity_id=job.related_entity_id,
        meta=meta,
    )
    if entity_resolved:
        job.cancel(reason='entity_resolved')
        return

    # Send reminder email
    success = _send_fallback_email_for_notification(notification, job, is_reminder=True)

    if success:
        job.mark_executed()
        # Schedule next reminder if under max
        _schedule_next_reminder(job, notification, reminder_count + 1, max_reminders)
    else:
        job.mark_failed()


# ---------------------------------------------------------------------------
# cancel_pending_notification_jobs  (async wrapper)
# ---------------------------------------------------------------------------

@shared_task(
    name='communications.orchestration.cancel_pending_notification_jobs',
)
def cancel_pending_notification_jobs(notification_id: str, reason: str = 'notification_read'):
    """
    Async wrapper around orchestration_service.cancel_pending_jobs.
    Safe to call from high-traffic code paths as a Celery task.
    """
    from apps.communications.notification_orchestration_service import cancel_pending_jobs
    cancelled = cancel_pending_jobs(notification_id=notification_id, reason=reason)
    logger.debug('Cancelled %d jobs for notification %s.', cancelled, notification_id)


# ---------------------------------------------------------------------------
# send_notification_email  (manual / admin trigger)
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    name='communications.orchestration.send_notification_email',
)
def send_notification_email(self, notification_id: str):
    """
    Dispatch an email for a notification via the EmailDeliveryService.

    Primary path: EmailDeliveryService.send_email_for_notification()
      → creates EmailDelivery record → queues deliver_email_task
      → exponential-backoff retry managed by EmailDeliveryService

    Fallback: legacy _send_fallback_email_for_notification() if the
    delivery service raises an unexpected exception.
    """
    notification = _load_notification(notification_id)
    if notification is None:
        return

    try:
        from apps.communications.email_delivery_service import EmailDeliveryService
        delivery = EmailDeliveryService.send_email_for_notification(notification_id)
        if delivery is not None:
            logger.info(
                'send_notification_email: queued delivery %s for notification %s',
                getattr(delivery, 'id', '?'), notification_id,
            )
            return
        # delivery is None means no email address — fall through to legacy path
    except Exception as exc:
        logger.warning(
            'send_notification_email: EmailDeliveryService failed (%s) — using legacy path', exc,
        )

    # Legacy fallback path
    success = _send_fallback_email_for_notification(notification, job=None)
    if not success:
        try:
            raise self.retry(countdown=60)
        except self.MaxRetriesExceededError:
            logger.error('send_notification_email exhausted retries for %s.', notification_id)


# ---------------------------------------------------------------------------
# send_notification_reminder  (schedule a reminder directly by notification_id)
# ---------------------------------------------------------------------------

@shared_task(
    name='communications.orchestration.send_notification_reminder',
)
def send_notification_reminder(
    notification_id: str,
    reminder_key: str = '',
    max_reminders: int = 3,
    delay_seconds: int = 3600,
):
    """
    Schedule a reminder flow for an existing notification.
    Creates a REMINDER job and queues execute_reminder_job.
    """
    from apps.communications.models import Notification
    from apps.communications.notification_orchestration_service import schedule_automation_job
    from apps.communications.notification_orchestration_models import NotificationAutomationJobType

    notification = _load_notification(notification_id)
    if notification is None:
        return

    if notification.is_read:
        return

    schedule_automation_job(
        tenant_id=notification.tenant_id,
        notification_id=notification_id,
        event_key=notification.get_type(),
        job_type=NotificationAutomationJobType.REMINDER,
        delay_seconds=delay_seconds,
        related_entity_type=notification.related_entity_type,
        related_entity_id=notification.related_entity_id,
        metadata={
            'reminder_key':    reminder_key,
            'reminder_count':  0,
            'max_reminders':   max_reminders,
        },
    )


# ---------------------------------------------------------------------------
# handle_notification_event  (generic async event entry point)
# ---------------------------------------------------------------------------

@shared_task(
    name='communications.orchestration.handle_notification_event',
)
def handle_notification_event(event_key: str, tenant_id: str, context: dict):
    """
    Async entry point for event-driven notification orchestration.
    Delegates to orchestrate_notification_event for the full flow.
    """
    from apps.communications.notification_orchestration_service import orchestrate_notification_event
    orchestrate_notification_event(
        event_key=event_key,
        tenant_id=tenant_id,
        entity_type=context.get('entity_type', ''),
        entity_id=context.get('entity_id'),
        extra_context=context,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_job(job_id: str):
    from apps.communications.notification_orchestration_models import NotificationAutomationJob
    try:
        return (
            NotificationAutomationJob.objects
            .select_related('notification')
            .get(id=job_id)
        )
    except NotificationAutomationJob.DoesNotExist:
        logger.info('NotificationAutomationJob %s not found — skipping.', job_id)
        return None


def _load_notification(notification_id: str):
    from apps.communications.models import Notification
    try:
        return Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.info('Notification %s not found — skipping.', notification_id)
        return None


def _send_fallback_email_for_notification(notification, job=None, is_reminder: bool = False) -> bool:
    """
    Resolve user email, render template, dispatch email, record delivery.
    Returns True on success.
    """
    from apps.communications.notification_service import NotificationService
    from apps.communications.notification_orchestration_service import (
        resolve_notification_rule,
        build_template_context,
        render_notification_email,
    )
    from apps.communications.email_dispatch.dispatch import EmailDispatchService
    from apps.communications.email_dispatch.types import EmailSendRequest

    user_email = _resolve_user_email(notification.user_id)
    if not user_email:
        logger.warning(
            'No email for user %s — cannot send %s for notification %s.',
            notification.user_id,
            'reminder' if is_reminder else 'fallback',
            notification.id,
        )
        NotificationService.record_delivery_attempt(
            notification_id=str(notification.id),
            channel='email',
            provider='system',
            status='failed',
            error_message='No email address found for user.',
            tenant_id=str(notification.tenant_id) if notification.tenant_id else None,
        )
        return False

    try:
        rule = resolve_notification_rule(
            tenant_id=notification.tenant_id,
            event_key=notification.get_type(),
        )
        ctx = build_template_context(
            event_key=notification.get_type(),
            entity_type=notification.related_entity_type,
            entity_id=notification.related_entity_id,
            notification=notification,
        )
        subject, body_html, body_text = render_notification_email(
            notification=notification,
            rule=rule,
            context=ctx,
        )

        if is_reminder:
            subject = f'[Reminder] {subject}'

        safe_tenant_id = str(notification.tenant_id) if notification.tenant_id else '00000000-0000-0000-0000-000000000000'
        request = EmailSendRequest(
            tenant_id=safe_tenant_id,
            actor_user_id=None,
            email_type='system',
            message_purpose='notification_reminder' if is_reminder else 'notification_fallback',
            recipients=[user_email],
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            allow_fallback=True,
            trigger_source='orchestration_task',
            triggered_by_event_id=f'notification.{"reminder" if is_reminder else "fallback"}.{notification.id}',
            related_object_type='notification',
            related_object_id=str(notification.id),
        )
        email_msg = EmailDispatchService.send_now(request)
        status = 'sent' if email_msg.status in {'sent', 'delivered', 'opened', 'clicked', 'queued'} else 'failed'
        ext_id = str(email_msg.id)

    except Exception as exc:
        logger.error(
            'Email dispatch failed for notification %s: %s', notification.id, exc
        )
        status = 'failed'
        ext_id = ''

    NotificationService.record_delivery_attempt(
        notification_id=str(notification.id),
        channel='email',
        provider='system',
        status=status,
        external_message_id=ext_id,
        tenant_id=str(notification.tenant_id) if notification.tenant_id else None,
    )
    return status == 'sent'


def _perform_escalation(job, notification):
    """
    Resolve the escalation target, create their notification, log the escalation.
    """
    from apps.communications.notification_orchestration_models import (
        NotificationEscalationLog,
    )
    from apps.communications.notification_orchestration_service import (
        resolve_escalation_target,
        resolve_notification_rule,
    )
    from apps.communications.notification_service import NotificationService
    from apps.communications.models import NotificationSeverity

    rule = resolve_notification_rule(
        tenant_id=notification.tenant_id,
        event_key=notification.get_type(),
    )

    target_type = (rule.escalation_target_type if rule else 'tenant_admin') or 'tenant_admin'
    target_user = resolve_escalation_target(
        notification=notification,
        rule=rule,
        tenant_id=notification.tenant_id,
    )

    escalation_level = notification.escalation_level + 1

    if target_user is None:
        logger.warning(
            'Escalation job %s: could not resolve target (type=%s) for notification %s.',
            job.id, target_type, notification.id,
        )
        NotificationEscalationLog.objects.create(
            tenant_id=notification.tenant_id,
            notification=notification,
            escalation_level=escalation_level,
            target_user_id=None,
            target_type=target_type,
            channel_used='none',
            status='skipped',
            original_event_key=notification.get_type(),
            original_user_id=notification.user_id,
            metadata={'job_id': str(job.id)},
        )
        job.mark_skipped()
        return

    # Do not escalate to the same user who already received the notification
    if str(target_user.id) == str(notification.user_id):
        logger.debug(
            'Escalation target is the same as original recipient — skipping escalation for %s.',
            notification.id,
        )
        job.mark_skipped()
        return

    # Create in-app notification for escalation target
    escalation_title = f'[Escalation] Unread notification: {notification.title}'
    escalation_body = (
        f'The following notification has not been read by the assigned user and requires your attention:\n'
        f'"{notification.body}"'
    )
    action_url = notification.action_url or ''

    try:
        escalation_notif = NotificationService.create_notification(
            user_id=target_user.id,
            title=escalation_title,
            body=escalation_body,
            notification_type=f'{notification.get_type()}.escalation',
            severity=NotificationSeverity.CRITICAL,
            action_url=action_url,
            related_entity_type=notification.related_entity_type,
            related_entity_id=notification.related_entity_id,
            tenant_id=notification.tenant_id,
            schedule_fallback=False,  # Do not chain further fallback on escalation
            metadata={
                'escalation_level': escalation_level,
                'original_notification_id': str(notification.id),
                'original_user_id': str(notification.user_id),
            },
        )
        notif_created = True
    except Exception as exc:
        logger.error('Failed to create escalation notification: %s', exc)
        notif_created = False

    # Update escalation_level on original notification
    notification.escalation_level = escalation_level
    notification.save(update_fields=['escalation_level', 'updated_at'])

    # Record escalation log
    NotificationEscalationLog.objects.create(
        tenant_id=notification.tenant_id,
        notification=notification,
        escalation_level=escalation_level,
        target_user_id=target_user.id,
        target_type=target_type,
        channel_used='in_app',
        status='sent' if notif_created else 'failed',
        original_event_key=notification.get_type(),
        original_user_id=notification.user_id,
        metadata={
            'job_id': str(job.id),
            'escalation_notification_id': str(escalation_notif.id) if notif_created else '',
        },
    )

    if notif_created:
        job.mark_executed()
        logger.info(
            'Escalation L%d: notified user %s for notification %s (job=%s).',
            escalation_level, target_user.id, notification.id, job.id,
        )
    else:
        job.mark_failed()


def _maybe_schedule_escalation(job, notification):
    """
    After a fallback email is sent (or already was), schedule an escalation
    job if the rule enables it.
    """
    from apps.communications.notification_orchestration_service import (
        resolve_notification_rule,
        schedule_automation_job,
    )
    from apps.communications.notification_orchestration_models import NotificationAutomationJobType

    rule = resolve_notification_rule(
        tenant_id=notification.tenant_id,
        event_key=notification.get_type(),
    )

    if rule and rule.escalation_enabled and rule.escalation_delay_minutes > 0:
        delay = rule.escalation_delay_minutes * 60
    else:
        # Severity-based defaults when no rule
        severity_delays = {'high': 3600, 'critical': 300}
        delay = severity_delays.get(notification.severity, 0)

    if not delay or notification.escalation_level > 0:
        return

    schedule_automation_job(
        tenant_id=notification.tenant_id,
        notification_id=str(notification.id),
        event_key=notification.get_type(),
        job_type=NotificationAutomationJobType.ESCALATION,
        delay_seconds=delay,
        related_entity_type=notification.related_entity_type or '',
        related_entity_id=notification.related_entity_id,
        metadata={'parent_job_id': str(job.id)},
    )


def _schedule_next_reminder(job, notification, next_count: int, max_reminders: int):
    """Schedule the next reminder in the chain (if under max)."""
    if next_count >= max_reminders:
        return

    from apps.communications.notification_orchestration_service import schedule_automation_job
    from apps.communications.notification_orchestration_models import NotificationAutomationJobType

    meta = job.metadata or {}
    delay_seconds = meta.get('repeat_interval_seconds', 3600)

    schedule_automation_job(
        tenant_id=job.tenant_id,
        notification_id=str(notification.id),
        event_key=job.event_key,
        job_type=NotificationAutomationJobType.REMINDER,
        delay_seconds=delay_seconds,
        related_entity_type=job.related_entity_type,
        related_entity_id=job.related_entity_id,
        metadata={
            **meta,
            'reminder_count': next_count,
        },
    )


def _check_entity_resolved(entity_type: str, entity_id, meta: dict) -> bool:
    """
    Return True if the related entity is in a state that means reminders should stop.
    e.g., feedback has been submitted, approval was given, offer was responded to.
    """
    if not entity_type or not entity_id:
        return False

    resolve_type = meta.get('entity_resolved_check', entity_type)

    try:
        if resolve_type == 'interview_feedback':
            from apps.interviews.models import InterviewPanelist
            panelist_id = meta.get('panelist_id')
            if panelist_id:
                p = InterviewPanelist.objects.filter(id=panelist_id).first()
                return bool(p and p.submitted_at)
            # If no specific panelist, check all feedback for the interview
            interview_id = entity_id
            from apps.interviews.models import InterviewPanelist
            pending = InterviewPanelist.objects.filter(
                interview_id=interview_id,
                submitted_at__isnull=True,
            ).exists()
            return not pending

        if resolve_type == 'application':
            from apps.pipeline.models import Application
            app = Application.objects.filter(id=entity_id).first()
            if app:
                return app.status in ('offer', 'joined', 'rejected', 'withdrawn')

        if resolve_type == 'offer':
            from apps.pipeline.models import Application
            app = Application.objects.filter(id=entity_id).first()
            if app:
                return app.status in ('joined', 'rejected', 'withdrawn') or bool(
                    app.offer_accepted_at or app.offer_rejected_at
                )

    except Exception as exc:
        logger.debug('_check_entity_resolved error: %s', exc)

    return False


def _resolve_user_email(user_id) -> str:
    """Look up user email from accounts."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(id=user_id).first()
        return user.email if user and user.email else ''
    except Exception as exc:
        logger.debug('Could not resolve email for user %s: %s', user_id, exc)
        return ''
