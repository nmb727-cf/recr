"""
Fallback Notification Tasks
============================
Celery tasks that check whether a notification was read and, if not,
send a fallback email. High-priority and critical notifications may
also trigger escalation flows.

Scheduling is driven by NotificationService._schedule_fallback_if_needed().
Timing configuration lives in notification_service.FALLBACK_DELAY_BY_SEVERITY.
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

# Module-level import so _resolve_escalation_delay can access it without
# relying on a caller having imported it into local scope first.
ESCALATION_DELAY_BY_SEVERITY = {
    'high':     3600,   # 1 hr
    'critical':  300,   # 5 min
}


@shared_task(bind=True, max_retries=2, default_retry_delay=120, name='communications.fallback.check_and_send')
def check_and_send_fallback_email(self, notification_id: str):
    """
    Check if notification is unread. If so, send fallback email.
    Scheduled by NotificationService after notification creation.
    """
    from apps.communications.models import Notification, NotificationSeverity
    from apps.communications.notification_service import NotificationService, ESCALATION_DELAY_BY_SEVERITY

    try:
        notification = Notification.objects.select_related().get(id=notification_id)
    except Notification.DoesNotExist:
        logger.info('Notification %s not found — skipping fallback.', notification_id)
        return

    # Already read — no fallback needed
    if notification.is_read:
        logger.debug('Notification %s already read — fallback skipped.', notification_id)
        return

    # Fallback already sent
    if notification.fallback_email_sent_at:
        logger.debug('Fallback already sent for notification %s.', notification_id)
        _maybe_escalate(notification)
        return

    # Send the fallback email
    _send_fallback_email(notification)

    # Schedule escalation — prefer rule settings, fall back to severity defaults
    escalation_delay = _resolve_escalation_delay(notification)
    if escalation_delay and notification.escalation_level == 0:
        escalate_notification.apply_async(
            args=[notification_id],
            countdown=escalation_delay,
        )


@shared_task(bind=True, max_retries=1, name='communications.fallback.escalate')
def escalate_notification(self, notification_id: str):
    """
    Legacy escalation task (kept for backwards compat with in-flight jobs).
    New flows use execute_escalation_job via NotificationAutomationJob.

    Delegates to the orchestration layer for actual target resolution + notification.
    """
    from apps.communications.models import Notification

    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return

    if notification.is_read:
        return

    logger.info(
        'Legacy escalation: notification %s (type=%s, severity=%s, user=%s).',
        notification_id,
        notification.get_type(),
        notification.severity,
        notification.user_id,
    )

    # Delegate to orchestration service for actual escalation logic
    try:
        from apps.communications.notification_orchestration_service import (
            resolve_notification_rule,
            resolve_escalation_target,
        )
        from apps.communications.notification_orchestration_models import (
            NotificationEscalationLog,
        )
        from apps.communications.notification_service import NotificationService
        from apps.communications.models import NotificationSeverity

        rule = resolve_notification_rule(
            tenant_id=notification.tenant_id,
            event_key=notification.get_type(),
        )
        if rule and not rule.escalation_enabled:
            return

        target_type = (rule.escalation_target_type if rule else 'tenant_admin') or 'tenant_admin'
        target_user = resolve_escalation_target(
            notification=notification,
            rule=rule,
            tenant_id=notification.tenant_id,
        )

        escalation_level = notification.escalation_level + 1

        if target_user and str(target_user.id) != str(notification.user_id):
            escalation_notif = NotificationService.create_notification(
                user_id=target_user.id,
                title=f'[Escalation] Unread: {notification.title}',
                body=(
                    f'The following notification has not been read:\n"{notification.body}"'
                ),
                notification_type=f'{notification.get_type()}.escalation',
                severity=NotificationSeverity.CRITICAL,
                action_url=notification.action_url or '',
                related_entity_type=notification.related_entity_type,
                related_entity_id=notification.related_entity_id,
                tenant_id=notification.tenant_id,
                schedule_fallback=False,
            )
            log_status = 'sent'
        else:
            escalation_notif = None
            log_status = 'skipped'

        notification.escalation_level = escalation_level
        notification.save(update_fields=['escalation_level', 'updated_at'])

        NotificationEscalationLog.objects.create(
            tenant_id=notification.tenant_id,
            notification=notification,
            escalation_level=escalation_level,
            target_user_id=target_user.id if target_user else None,
            target_type=target_type,
            channel_used='in_app',
            status=log_status,
            original_event_key=notification.get_type(),
            original_user_id=notification.user_id,
            metadata={'source': 'legacy_fallback_task'},
        )

    except Exception as exc:
        logger.error('Legacy escalate_notification failed for %s: %s', notification_id, exc)
        # Minimal fallback — just bump escalation_level so we don't loop
        try:
            from apps.communications.models import Notification as N
            N.objects.filter(id=notification_id).update(
                escalation_level=notification.escalation_level + 1
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _send_fallback_email(notification):
    """Resolve recipient email and dispatch fallback email."""
    from apps.communications.notification_service import NotificationService
    from apps.communications.email_dispatch.dispatch import EmailDispatchService
    from apps.communications.email_dispatch.types import EmailSendRequest
    from apps.communications.models import NotificationSeverity

    user_email = _resolve_user_email(notification.user_id)
    if not user_email:
        logger.warning(
            'Cannot send fallback email for notification %s — no email resolved for user %s.',
            notification.id,
            notification.user_id,
        )
        NotificationService.record_delivery_attempt(
            notification_id=str(notification.id),
            channel='email',
            provider='system',
            status='failed',
            error_message='No email address found for user.',
            tenant_id=str(notification.tenant_id) if notification.tenant_id else None,
        )
        return

    # ── Apply user-configured preference overrides ─────────────────────
    try:
        from apps.communications.notification_preference_service import UserNotificationPreferenceService
        from apps.communications.notification_control_service import NotificationControlService
        from apps.communications.models import NotificationSeverity

        # Resolve category from rule if possible
        rule = NotificationControlService.get_rule(
            tenant_id=notification.tenant_id,
            event_key=notification.get_type(),
        )
        pref_category = rule.category if rule else 'system'

        allowed = UserNotificationPreferenceService.is_notification_allowed_for_user(
            tenant_id=notification.tenant_id,
            user_id=notification.user_id,
            category=pref_category,
            channel='email',
            priority=notification.severity,
            is_system_critical=(notification.severity == NotificationSeverity.CRITICAL)
        )
        if not allowed:
            logger.info(
                'Fallback email suppressed by user preference: notification=%s user=%s',
                notification.id, notification.user_id,
            )
            # Record a 'skipped' delivery instead of 'failed' or 'sent'
            NotificationService.record_delivery_attempt(
                notification_id=str(notification.id),
                channel='email',
                provider='system',
                status='skipped',
                error_message='Suppressed by user notification preference.',
                tenant_id=str(notification.tenant_id) if notification.tenant_id else None,
            )
            return
    except Exception as exc:
        logger.warning('Could not check user preferences for fallback email %s: %s', notification.id, exc)

    subject = f'[Action Required] {notification.title}'
    body_text = (
        f'{notification.body}\n\n'
        f'This is an automated reminder because you have not yet viewed this notification.\n'
        f'Action URL: {notification.action_url or "N/A"}'
    )
    body_html = _render_fallback_html(notification, user_email)

    try:
        safe_tenant_id = str(notification.tenant_id) if notification.tenant_id else '00000000-0000-0000-0000-000000000000'
        request = EmailSendRequest(
            tenant_id=safe_tenant_id,
            actor_user_id=None,
            email_type='system',
            message_purpose='notification_fallback',
            recipients=[user_email],
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            allow_fallback=True,
            trigger_source='fallback_task',
            triggered_by_event_id=f'notification.fallback.{notification.id}',
            related_object_type='notification',
            related_object_id=str(notification.id),
        )
        email_msg = EmailDispatchService.send_now(request)
        status = 'sent' if email_msg.status in {'sent', 'delivered', 'opened', 'clicked', 'queued'} else 'failed'
        ext_id = str(email_msg.id)
    except Exception as exc:
        logger.error('Fallback email dispatch failed for notification %s: %s', notification.id, exc)
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


def _render_fallback_html(notification, user_email: str) -> str:
    return (
        f'<div style="font-family:sans-serif;max-width:600px;margin:auto;">'
        f'<h2 style="color:#1a1a2e;">{notification.title}</h2>'
        f'<p>{notification.body}</p>'
        f'{"<p><a href=" + chr(34) + notification.action_url + chr(34) + " style=" + chr(34) + "background:#4f46e5;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;" + chr(34) + ">View Now</a></p>" if notification.action_url else ""}'
        f'<hr/>'
        f'<p style="color:#888;font-size:12px;">This email was sent because you have not yet checked this notification in-app. '
        f'Severity: {notification.severity}.</p>'
        f'</div>'
    )


def _resolve_user_email(user_id) -> str:
    """Look up user email from accounts. Returns empty string if not found."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(id=user_id).first()
        return user.email if user and user.email else ''
    except Exception as exc:
        logger.debug('Could not resolve email for user %s: %s', user_id, exc)
        return ''


def _resolve_escalation_delay(notification) -> int:
    """
    Return escalation delay in seconds, using rule settings when available.
    Returns 0 / None to skip escalation.
    """
    try:
        from apps.communications.notification_control_service import NotificationControlService
        rule = NotificationControlService.get_rule(
            tenant_id=notification.tenant_id,
            event_key=notification.get_type(),
        )
        if rule:
            if not rule.escalation_enabled:
                return 0
            return rule.escalation_delay_minutes * 60
    except Exception:
        pass
    # Fallback to severity defaults
    return ESCALATION_DELAY_BY_SEVERITY.get(notification.severity, 0)


def _maybe_escalate(notification):
    """If fallback was sent but still unread, maybe escalate."""
    from apps.communications.models import NotificationSeverity
    from apps.communications.notification_service import ESCALATION_DELAY_BY_SEVERITY
    if (
        not notification.is_read
        and notification.escalation_level == 0
        and notification.severity in (NotificationSeverity.HIGH, NotificationSeverity.CRITICAL)
    ):
        escalate_notification.apply_async(args=[str(notification.id)], countdown=60)


def _emit_escalation_event(notification):
    """Emit escalation signal so automation can react (e.g., notify manager)."""
    try:
        from apps.core import events
        # Escalation events can be consumed by automation_notifications, etc.
        # Emit as a generic signal with metadata
        logger.info(
            'Escalation event for notification %s (level=%d)',
            notification.id,
            notification.escalation_level,
        )
    except Exception:
        pass
