"""
Email Delivery Service
=======================
Central entry point for all automation-triggered email sending.

This service is the ONLY way notification automation, escalation tasks,
and system alerts should dispatch emails.  Business/UI modules must NOT
call this directly — they go through the notification event system.

Architecture:
    Event → NotificationService → orchestration_tasks → EmailDeliveryService
                                                          ↓
                                                    TenantEmailConfig
                                                          ↓
                                                    Provider (SMTP/SG/SES)
                                                          ↓
                                                    EmailDelivery (tracked)

Key entry points:
    EmailDeliveryService.send_email(...)
    EmailDeliveryService.send_email_for_notification(notification_id)

Both are async — they create an EmailDelivery record and queue a Celery task.
They do NOT block the caller.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from django.utils import timezone

logger = logging.getLogger(__name__)

# Retry delays in seconds: 1 min, 5 min, 15 min, 1 hr
RETRY_DELAYS: list[int] = [60, 300, 900, 3600]

# Celery queue names by priority
PRIORITY_QUEUE_MAP: dict[str, str] = {
    'urgent': 'email_high',
    'high':   'email_high',
    'normal': 'email_normal',
    'low':    'email_low',
}


class EmailDeliveryService:
    """
    Automation email delivery service.

    All methods are class-level — no instantiation required.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def send_email(
        cls,
        *,
        tenant_id,
        recipients: list[str],
        subject: str,
        template_slug: str = '',
        context: Optional[dict] = None,
        html_body: str = '',
        text_body: str = '',
        priority: str = 'normal',
        notification_id=None,
        metadata: Optional[dict] = None,
    ):
        """
        Queue an automation email for delivery.

        Either (template_slug + context) OR (html_body + text_body) must
        be supplied.  template_slug takes precedence — if both are given,
        the template is rendered and overwrites the raw bodies.

        Returns the EmailDelivery record (status=PENDING).
        The actual send happens in a background Celery task.
        """
        from apps.communications.email_delivery_models import (
            EmailDelivery,
            EmailDeliveryPriority,
            TenantEmailConfig,
        )
        from apps.communications.email_dispatch.renderer import EmailTemplateRenderer

        safe_tenant_id = str(tenant_id) if tenant_id else '00000000-0000-0000-0000-000000000000'
        priority = priority if priority in EmailDeliveryPriority.values else 'normal'

        # Resolve from_email / from_name from tenant config
        config = TenantEmailConfig.get_for_tenant(safe_tenant_id)
        from_email, from_name = cls._resolve_sender(config)

        # Render template if slug provided
        template_used = template_slug
        if template_slug:
            renderer = EmailTemplateRenderer()
            rendered = renderer.render(
                template_slug=template_slug,
                context=context or {},
                tenant_id=safe_tenant_id,
            )
            subject = rendered.subject or subject
            html_body = rendered.html_body
            text_body = rendered.text_body
            template_used = rendered.template_used or template_slug

        if not subject:
            subject = '(no subject)'

        # Create one EmailDelivery per recipient
        deliveries = []
        for recipient in recipients:
            if not recipient or not recipient.strip():
                continue
            delivery = EmailDelivery.objects.create(
                tenant_id=safe_tenant_id,
                notification_id=notification_id,
                recipient_email=recipient.strip(),
                subject=subject,
                template_used=template_used,
                provider=getattr(config, 'provider', 'system') if config else 'system',
                priority=priority,
                max_retries=len(RETRY_DELAYS),
                metadata={
                    'from_email':  from_email,
                    'from_name':   from_name,
                    'html_body':   html_body[:10000],   # trim for storage
                    'text_body':   text_body[:5000],
                    **(metadata or {}),
                },
            )
            cls._queue_delivery(delivery)
            deliveries.append(delivery)

        return deliveries[0] if len(deliveries) == 1 else deliveries

    @classmethod
    def send_email_for_notification(cls, notification_id: str):
        """
        Integration point for notification automation.

        Resolves the notification, renders the appropriate template,
        and sends an email to the notification recipient.

        Called by:
        - orchestration_tasks.execute_fallback_job
        - orchestration_tasks.send_notification_email (admin retry)
        - orchestration_tasks.execute_reminder_job

        Returns EmailDelivery or None if notification not found / user has no email.
        """
        from apps.communications.models import Notification
        from apps.communications.notification_orchestration_service import (
            build_template_context,
            render_notification_email,
            resolve_notification_rule,
        )

        try:
            notification = Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            logger.info('EmailDeliveryService: notification %s not found', notification_id)
            return None

        user_email = cls._resolve_user_email(notification.user_id)
        if not user_email:
            logger.warning(
                'EmailDeliveryService: no email for user %s (notification %s)',
                notification.user_id,
                notification_id,
            )
            cls._record_no_email_failure(notification)
            return None

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
            subject, html_body, text_body = render_notification_email(
                notification=notification,
                rule=rule,
                context=ctx,
            )
        except Exception as exc:
            logger.error(
                'EmailDeliveryService: template render failed for notification %s: %s',
                notification_id, exc,
            )
            subject = notification.title
            html_body = f'<p>{notification.body}</p>'
            text_body = notification.body

        priority = cls._severity_to_priority(getattr(notification, 'severity', 'medium'))

        return cls.send_email(
            tenant_id=notification.tenant_id,
            recipients=[user_email],
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            priority=priority,
            notification_id=str(notification.id),
            metadata={
                'trigger': 'notification_fallback',
                'event_key': notification.get_type(),
            },
        )

    # ------------------------------------------------------------------
    # Retry scheduling (called by deliver_email_task on failure)
    # ------------------------------------------------------------------

    @classmethod
    def schedule_retry(cls, delivery_id: str, current_retry_count: int):
        """
        Queue a retry task with exponential backoff.

        Backoff schedule (RETRY_DELAYS):
            retry 0 → 60s
            retry 1 → 300s  (5 min)
            retry 2 → 900s  (15 min)
            retry 3 → 3600s (1 hr)

        Returns False if max retries exhausted.
        """
        from apps.communications.email_delivery_models import EmailDelivery, EmailDeliveryStatus

        try:
            delivery = EmailDelivery.objects.get(id=delivery_id)
        except EmailDelivery.DoesNotExist:
            logger.warning('EmailDeliveryService.schedule_retry: delivery %s not found', delivery_id)
            return False

        if not delivery.can_retry():
            logger.info(
                'EmailDeliveryService: delivery %s exhausted retries (%d/%d) — marking failed',
                delivery_id, delivery.retry_count, delivery.max_retries,
            )
            delivery.mark_failed(error=delivery.error_message or 'Max retries exhausted')
            cls._maybe_alert_admin(delivery)
            return False

        delay_index = min(current_retry_count, len(RETRY_DELAYS) - 1)
        delay_seconds = RETRY_DELAYS[delay_index]
        next_retry_at = timezone.now() + timezone.timedelta(seconds=delay_seconds)
        delivery.mark_deferred(next_retry_at=next_retry_at)

        from apps.communications.email_dispatch.tasks import deliver_email_task
        queue = PRIORITY_QUEUE_MAP.get(delivery.priority, 'email_normal')
        deliver_email_task.apply_async(
            args=[str(delivery_id)],
            countdown=delay_seconds,
            queue=queue,
        )
        logger.info(
            'EmailDeliveryService: scheduled retry for delivery %s in %ds (attempt %d/%d)',
            delivery_id, delay_seconds, delivery.retry_count, delivery.max_retries,
        )
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _queue_delivery(cls, delivery):
        """Queue the initial delivery Celery task respecting priority."""
        from apps.communications.email_dispatch.tasks import deliver_email_task
        queue = PRIORITY_QUEUE_MAP.get(delivery.priority, 'email_normal')
        deliver_email_task.apply_async(
            args=[str(delivery.id)],
            queue=queue,
        )

    @classmethod
    def _resolve_sender(cls, config) -> tuple[str, str]:
        """Return (from_email, from_name) from config or system defaults."""
        from django.conf import settings
        if config:
            from_email = config.from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@talentos.com')
            from_name  = config.from_name  or getattr(settings, 'DEFAULT_FROM_NAME', 'Talentos')
        else:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@talentos.com')
            from_name  = getattr(settings, 'DEFAULT_FROM_NAME', 'Talentos')
        return from_email, from_name

    @staticmethod
    def _resolve_user_email(user_id) -> str:
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(id=user_id).values('email').first()
            return (user or {}).get('email') or ''
        except Exception as exc:
            logger.debug('_resolve_user_email error for %s: %s', user_id, exc)
            return ''

    @staticmethod
    def _severity_to_priority(severity: str) -> str:
        return {
            'critical': 'urgent',
            'high':     'high',
            'medium':   'normal',
            'info':     'low',
        }.get(severity, 'normal')

    @staticmethod
    def _record_no_email_failure(notification):
        """Record a failed delivery attempt for observability."""
        try:
            from apps.communications.notification_service import NotificationService
            NotificationService.record_delivery_attempt(
                notification_id=str(notification.id),
                channel='email',
                provider='system',
                status='failed',
                error_message='No email address found for user.',
                tenant_id=str(notification.tenant_id) if notification.tenant_id else None,
            )
        except Exception:
            pass

    @staticmethod
    def _maybe_alert_admin(delivery):
        """Log a prominent warning for permanently failed deliveries."""
        logger.warning(
            'EMAIL DELIVERY PERMANENTLY FAILED — delivery_id=%s tenant=%s recipient=%s subject=%r',
            delivery.id, delivery.tenant_id, delivery.recipient_email, delivery.subject[:60],
        )
