"""
Notification Service Layer
===========================
Central service for creating and managing in-app notifications,
tracking delivery attempts, and scheduling fallback email/escalation.

All business modules should call create_notification() after emitting events,
or rely on event_handlers.py to do so automatically.
"""
import logging
import uuid
from datetime import timedelta
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.communications.models import (
    Notification,
    NotificationDelivery,
    NotificationSeverity,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fallback timing configuration (seconds after creation)
# ---------------------------------------------------------------------------
FALLBACK_DELAY_BY_SEVERITY = {
    NotificationSeverity.INFO: None,       # No fallback for info
    NotificationSeverity.MEDIUM: 2400,     # 40 min
    NotificationSeverity.HIGH: 600,        # 10 min
    NotificationSeverity.CRITICAL: 60,     # 1 min (near-immediate)
}

ESCALATION_DELAY_BY_SEVERITY = {
    NotificationSeverity.HIGH: 3600,       # 1 hr after first fallback
    NotificationSeverity.CRITICAL: 300,    # 5 min after first fallback
}


# ---------------------------------------------------------------------------
# Notification Service
# ---------------------------------------------------------------------------

class NotificationService:

    @staticmethod
    def create_notification(
        *,
        user_id,
        title: str,
        body: str = '',
        notification_type: str = 'platform_notification',
        severity: str = NotificationSeverity.INFO,
        action_url: str = '',
        related_entity_type: str = '',
        related_entity_id=None,
        tenant_id=None,
        expires_at=None,
        metadata: dict = None,
        schedule_fallback: bool = True,
    ) -> Notification:
        """
        Create an in-app notification and schedule fallback email if needed.
        This is the canonical entry point for all notification creation.

        When a NotificationRule exists for (tenant_id, notification_type) the rule's
        settings (severity, fallback timing, channel overrides) are applied first.
        """
        # ── Apply admin-configured rule overrides ────────────────────────────
        try:
            from apps.communications.notification_control_service import NotificationControlService
            rule = NotificationControlService.get_rule(
                tenant_id=tenant_id,
                event_key=notification_type,
            )
            if rule:
                if not rule.is_active:
                    logger.debug(
                        'Notification suppressed by rule (inactive): type=%s tenant=%s',
                        notification_type, tenant_id,
                    )
                    # Return a dummy notification-like object is unsafe; just skip
                    # by still creating but with INFO so no fallback runs.
                    severity = NotificationSeverity.INFO
                    schedule_fallback = False
                else:
                    severity = rule.priority  # rule.priority maps to NotificationSeverity values
                    if not rule.in_app_enabled:
                        schedule_fallback = False
        except Exception as exc:
            logger.warning('Could not apply notification rule for %s: %s', notification_type, exc)

        # ── Apply user-configured preference overrides ─────────────────────
        try:
            from apps.communications.notification_preference_service import UserNotificationPreferenceService
            # Resolve category from rule if possible
            pref_category = 'system'
            if rule:
                pref_category = rule.category

            allowed = UserNotificationPreferenceService.is_notification_allowed_for_user(
                tenant_id=tenant_id,
                user_id=user_id,
                category=pref_category,
                channel='in_app',
                priority=severity,
                is_system_critical=(severity == NotificationSeverity.CRITICAL)
            )
            if not allowed:
                logger.debug(
                    'Notification suppressed by user preference: type=%s user=%s',
                    notification_type, user_id,
                )
                return None
        except Exception as exc:
            logger.warning('Could not check user preferences for %s: %s', notification_type, exc)

        with transaction.atomic():
            notification = Notification.objects.create(
                tenant_id=tenant_id,
                user_id=user_id,
                type=notification_type,
                notification_type=notification_type,  # legacy alias
                title=title,
                body=body,
                severity=severity,
                action_url=action_url or '',
                related_entity_type=related_entity_type or '',
                related_entity_id=related_entity_id,
                expires_at=expires_at,
                metadata=metadata or {},
            )
            # Record in-app delivery as "delivered" immediately
            NotificationDelivery.objects.create(
                tenant_id=tenant_id,
                notification=notification,
                channel='in_app',
                provider='in_app',
                status='delivered',
                attempted_at=timezone.now(),
                delivered_at=timezone.now(),
            )

        # Publish real-time push to user's notification stream
        try:
            from apps.communications.realtime import RealtimePublisher
            RealtimePublisher.publish_notification(
                user_id=str(user_id),
                notification_id=str(notification.id),
            )
        except Exception:
            pass

        # Schedule fallback email if appropriate
        if schedule_fallback:
            NotificationService._schedule_fallback_if_needed(notification)

        return notification

    @staticmethod
    def create_bulk_notifications(
        *,
        user_ids: list,
        title: str,
        body: str = '',
        notification_type: str = 'platform_notification',
        severity: str = NotificationSeverity.INFO,
        action_url: str = '',
        related_entity_type: str = '',
        related_entity_id=None,
        tenant_id=None,
        expires_at=None,
        metadata: dict = None,
    ) -> list:
        """Create the same notification for multiple users efficiently."""
        notifications = []
        for user_id in user_ids:
            n = NotificationService.create_notification(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=notification_type,
                severity=severity,
                action_url=action_url,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                tenant_id=tenant_id,
                expires_at=expires_at,
                metadata=metadata,
                schedule_fallback=(severity != NotificationSeverity.INFO),
            )
            notifications.append(n)
        return notifications

    @staticmethod
    def mark_read(*, notification_id, user_id) -> Notification:
        notification = Notification.objects.filter(
            id=notification_id,
            user_id=user_id,
        ).first()
        if not notification:
            from rest_framework.exceptions import NotFound
            raise NotFound('Notification not found.')
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at', 'updated_at'])

            # Cancel any pending fallback/escalation jobs for this notification
            try:
                from apps.communications.notification_orchestration_service import cancel_pending_jobs
                cancel_pending_jobs(
                    notification_id=str(notification_id),
                    reason='notification_read',
                )
            except Exception as exc:
                logger.warning(
                    'Failed to cancel pending jobs for notification %s: %s',
                    notification_id, exc,
                )

            # Cancel any pending multi-channel deliveries (WA/SMS/Push fallbacks)
            try:
                from apps.communications.channel_services import cancel_channel_fallbacks
                cancel_channel_fallbacks(
                    notification_id=str(notification_id),
                    reason='notification_read',
                )
            except Exception as exc:
                logger.debug(
                    'Could not cancel channel deliveries for notification %s: %s',
                    notification_id, exc,
                )

            # Publish notification.read event
            try:
                from apps.communications.realtime import RealtimePublisher
                RealtimePublisher.publish_notification_read(
                    user_id=str(user_id),
                    notification_id=str(notification_id),
                )
            except Exception:
                pass
        return notification

    @staticmethod
    def mark_all_read(*, user_id, tenant_id=None) -> int:
        qs = Notification.objects.filter(user_id=user_id, is_read=False)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        now = timezone.now()
        count = qs.update(is_read=True, read_at=now, updated_at=now)

        try:
            from apps.communications.realtime import RealtimePublisher
            RealtimePublisher.publish_unread_count(user_id=str(user_id))
        except Exception:
            pass

        return count

    @staticmethod
    def get_unread_count(*, user_id, tenant_id=None) -> int:
        from django.db.models import Q
        now = timezone.now()
        qs = Notification.objects.filter(user_id=user_id, is_read=False)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        qs = qs.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        return qs.count()

    @staticmethod
    def get_notifications(
        *,
        user_id,
        tenant_id=None,
        is_read: Optional[bool] = None,
        severity: Optional[str] = None,
        notification_type: Optional[str] = None,
        exclude_expired: bool = True,
    ):
        from django.db.models import Q
        qs = Notification.objects.filter(user_id=user_id)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if is_read is not None:
            qs = qs.filter(is_read=is_read)
        if severity:
            qs = qs.filter(severity=severity)
        if notification_type:
            qs = qs.filter(notification_type=notification_type)
        if exclude_expired:
            now = timezone.now()
            qs = qs.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        return qs.order_by('-created_at')

    @staticmethod
    def record_delivery_attempt(
        *,
        notification_id,
        channel: str,
        provider: str = '',
        status: str = 'sent',
        external_message_id: str = '',
        error_message: str = '',
        tenant_id=None,
        metadata: dict = None,
    ) -> NotificationDelivery:
        """Record a delivery attempt for a notification (e.g., fallback email sent)."""
        now = timezone.now()
        delivery = NotificationDelivery.objects.create(
            tenant_id=tenant_id,
            notification_id=notification_id,
            channel=channel,
            provider=provider,
            status=status,
            attempted_at=now,
            delivered_at=now if status == 'delivered' else None,
            failed_at=now if status == 'failed' else None,
            external_message_id=external_message_id,
            error_message=error_message,
            metadata=metadata or {},
        )
        # Update notification's fallback timestamps
        if channel == 'email' and status in ('sent', 'delivered'):
            Notification.objects.filter(id=notification_id).update(
                fallback_email_sent_at=now
            )
        elif channel == 'whatsapp' and status in ('sent', 'delivered'):
            Notification.objects.filter(id=notification_id).update(
                fallback_whatsapp_sent_at=now
            )
        return delivery

    # ── Internal scheduling ──────────────────────────────────────────────────

    @staticmethod
    def _schedule_fallback_if_needed(notification: Notification):
        """
        Schedule fallback email via NotificationAutomationJob.

        Lookup order for timing:
          1. NotificationRule.fallback_delay_minutes  (rule-based, per tenant)
          2. FALLBACK_DELAY_BY_SEVERITY               (hardcoded severity defaults)

        Uses the new orchestration job system (execute_fallback_job) which is
        idempotent, cancellable, and fully tracked. Also retains the legacy
        check_and_send_fallback_email task as a secondary path for backwards compat.
        """
        delay_seconds = None

        # Check rule-based override first
        try:
            from apps.communications.notification_control_service import NotificationControlService
            rule = NotificationControlService.get_rule(
                tenant_id=notification.tenant_id,
                event_key=notification.get_type(),
            )
            if rule:
                if not rule.fallback_enabled:
                    return
                if not NotificationControlService.channel_enabled(
                    tenant_id=notification.tenant_id, channel='email'
                ):
                    return
                delay_seconds = rule.fallback_delay_minutes * 60
        except Exception:
            pass

        if delay_seconds is None:
            delay_seconds = FALLBACK_DELAY_BY_SEVERITY.get(notification.severity)

        if not delay_seconds:
            return

        # Primary path: use orchestration job system (tracked, cancellable)
        try:
            from apps.communications.notification_orchestration_service import schedule_automation_job
            from apps.communications.notification_orchestration_models import NotificationAutomationJobType
            schedule_automation_job(
                tenant_id=notification.tenant_id,
                notification_id=str(notification.id),
                event_key=notification.get_type(),
                job_type=NotificationAutomationJobType.FALLBACK_EMAIL,
                delay_seconds=delay_seconds,
                related_entity_type=notification.related_entity_type or '',
                related_entity_id=notification.related_entity_id,
            )
        except Exception as exc:
            logger.warning(
                'Failed to schedule orchestration fallback job for notification %s: %s — '
                'falling back to legacy task.',
                notification.id, exc,
            )
            # Legacy fallback path
            try:
                from apps.communications.fallback_tasks import check_and_send_fallback_email
                check_and_send_fallback_email.apply_async(
                    args=[str(notification.id)],
                    countdown=delay_seconds,
                )
            except Exception as exc2:
                logger.warning(
                    'Legacy fallback task also failed for notification %s: %s',
                    notification.id, exc2,
                )


