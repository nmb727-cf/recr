"""
WorkflowNotificationOrchestrator
─────────────────────────────────
Central service for routing, throttling, deduplicating, and tracking
all workflow-driven notifications.

Usage (from AutomationActionExecutor or any workflow action):

    from apps.automation_notifications.services.workflow_notification_orchestrator import (
        WorkflowNotificationOrchestrator as WNO,
    )

    result = WNO.dispatch(
        tenant_id=run.tenant_id,
        execution_id=run.id,
        workflow_id=run.rule.id,
        rule=rule_obj,            # WorkflowNotificationRule or None for ad-hoc
        context=run.trigger_payload_json,
        recipient_override=None,  # {'email': ..., 'user_id': ...}
    )
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, time
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from apps.automation_notifications.models import (
    DeliveryStatus,
    EscalationStatus,
    NotificationChannel,
    RecipientType,
    WorkflowEscalationNotification,
    WorkflowNotificationDelivery,
    WorkflowNotificationInsight,
    WorkflowNotificationPreference,
    WorkflowNotificationRule,
    InsightType,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ─── Retry / fallback configuration ──────────────────────────────────────────
MAX_RETRIES = 3

# Phase 1 active channels; others are queued but not dispatched yet
ACTIVE_CHANNELS = {NotificationChannel.EMAIL, NotificationChannel.IN_APP, NotificationChannel.WHATSAPP}


class WorkflowNotificationOrchestrator:

    # ─── Main dispatch entry point ────────────────────────────────────────────

    @staticmethod
    def dispatch(
        *,
        tenant_id,
        execution_id=None,
        workflow_id=None,
        rule: WorkflowNotificationRule | None,
        context: dict,
        recipient_override: dict | None = None,
    ) -> dict:
        """
        Resolves recipients, checks throttle/dedupe, selects channel,
        renders message, and dispatches. Returns result dict.
        """
        if rule is None:
            return {'status': 'skipped', 'reason': 'no_rule'}

        # 1. Resolve recipients
        recipients = WorkflowNotificationOrchestrator.resolve_recipients(context, rule.recipient_type)
        if recipient_override:
            recipients = [recipient_override]
        if not recipients:
            return {'status': 'skipped', 'reason': 'no_recipients'}

        results = []
        for recipient in recipients:
            result = WorkflowNotificationOrchestrator._process_one(
                tenant_id=tenant_id,
                execution_id=execution_id,
                workflow_id=workflow_id,
                rule=rule,
                context=context,
                recipient=recipient,
            )
            results.append(result)

        return {'status': 'dispatched', 'results': results}

    @staticmethod
    def _process_one(*, tenant_id, execution_id, workflow_id, rule, context, recipient):
        user_id = recipient.get('user_id')
        email   = recipient.get('email', '')
        phone   = recipient.get('phone', '')

        # 2. Build dedupe key
        dedupe_key = WorkflowNotificationOrchestrator._build_dedupe_key(
            rule=rule, recipient=recipient, context=context
        )

        # 3. Deduplication check
        if WorkflowNotificationOrchestrator.should_deduplicate(rule, recipient, context):
            WorkflowNotificationDelivery.objects.create(
                tenant_id=tenant_id,
                execution_id=execution_id,
                workflow_id=workflow_id,
                notification_rule=rule,
                recipient_user_id=user_id,
                recipient_email=email,
                recipient_phone=phone,
                channel=rule.channel,
                status=DeliveryStatus.DEDUPLICATED,
                dedupe_key=dedupe_key,
                failure_reason='Duplicate notification suppressed',
            )
            return {'status': 'deduplicated', 'dedupe_key': dedupe_key}

        # 4. Throttle check
        if WorkflowNotificationOrchestrator.should_throttle(rule, recipient, context):
            WorkflowNotificationDelivery.objects.create(
                tenant_id=tenant_id,
                execution_id=execution_id,
                workflow_id=workflow_id,
                notification_rule=rule,
                recipient_user_id=user_id,
                recipient_email=email,
                recipient_phone=phone,
                channel=rule.channel,
                status=DeliveryStatus.THROTTLED,
                dedupe_key=dedupe_key,
                failure_reason='Throttle window active',
            )
            return {'status': 'throttled'}

        # 5. Channel selection (respects preference + quiet hours)
        channel = WorkflowNotificationOrchestrator.select_channel(
            user_id=user_id, rule=rule, context=context
        )

        # 6. Render message
        subject, body = WorkflowNotificationOrchestrator.render_notification(rule, context)

        # 7. Create delivery record
        delivery = WorkflowNotificationDelivery.objects.create(
            tenant_id=tenant_id,
            execution_id=execution_id,
            workflow_id=workflow_id,
            notification_rule=rule,
            recipient_user_id=user_id,
            recipient_email=email,
            recipient_phone=phone,
            channel=channel,
            status=DeliveryStatus.QUEUED,
            subject=subject,
            rendered_message=body,
            dedupe_key=dedupe_key,
        )

        # 8. Send
        return WorkflowNotificationOrchestrator.send_notification(delivery)

    # ─── Recipient resolution ─────────────────────────────────────────────────

    @staticmethod
    def resolve_recipients(context: dict, recipient_type: str) -> list[dict]:
        """
        Resolve recipient contact info from workflow execution context.
        Returns list of dicts with keys: user_id, email, phone.
        """
        recipients = []

        if recipient_type == RecipientType.CANDIDATE:
            email  = context.get('candidate_email') or context.get('email', '')
            uid    = context.get('candidate_id') or context.get('candidate_user_id')
            phone  = context.get('candidate_phone', '')
            if email or uid:
                recipients.append({'user_id': uid, 'email': email, 'phone': phone})

        elif recipient_type == RecipientType.ASSIGNED_RECRUITER:
            uid   = context.get('recruiter_id') or context.get('assigned_recruiter_id')
            email = context.get('recruiter_email', '')
            if uid or email:
                recipients.append({'user_id': uid, 'email': email, 'phone': ''})

        elif recipient_type == RecipientType.HIRING_MANAGER:
            uid   = context.get('hiring_manager_id')
            email = context.get('hiring_manager_email', '')
            if uid or email:
                recipients.append({'user_id': uid, 'email': email, 'phone': ''})

        elif recipient_type == RecipientType.RECRUITER_MANAGER:
            uid   = context.get('recruiter_manager_id')
            email = context.get('recruiter_manager_email', '')
            if uid or email:
                recipients.append({'user_id': uid, 'email': email, 'phone': ''})

        elif recipient_type == RecipientType.AGENCY_CONTACT:
            email = context.get('agency_contact_email', '')
            uid   = context.get('agency_contact_id')
            if email or uid:
                recipients.append({'user_id': uid, 'email': email, 'phone': ''})

        elif recipient_type == RecipientType.CUSTOM_USER:
            for item in context.get('custom_recipients', []):
                recipients.append({
                    'user_id': item.get('user_id'),
                    'email':   item.get('email', ''),
                    'phone':   item.get('phone', ''),
                })

        elif recipient_type == RecipientType.WORKFLOW_OWNER:
            uid   = context.get('workflow_owner_id') or context.get('created_by')
            email = context.get('workflow_owner_email', '')
            if uid or email:
                recipients.append({'user_id': uid, 'email': email, 'phone': ''})

        return recipients

    # ─── Channel selection ────────────────────────────────────────────────────

    @staticmethod
    def select_channel(*, user_id, rule: WorkflowNotificationRule, context: dict) -> str:
        """
        Priority: user preference → rule config → fallback chain.
        Respects quiet hours unless escalation override is set.
        """
        preferred = WorkflowNotificationOrchestrator._get_user_preferred_channels(user_id, rule)

        for ch in preferred:
            if WorkflowNotificationOrchestrator._is_channel_available(ch, user_id=user_id):
                return ch

        # Fall back to rule's primary channel
        if rule.channel in ACTIVE_CHANNELS:
            return rule.channel

        # Walk fallback chain
        for ch in (rule.fallback_channels or []):
            if ch in ACTIVE_CHANNELS:
                return ch

        return NotificationChannel.IN_APP  # last resort

    @staticmethod
    def _get_user_preferred_channels(user_id, rule: WorkflowNotificationRule) -> list[str]:
        if not user_id:
            return [rule.channel] + list(rule.fallback_channels or [])
        pref = WorkflowNotificationPreference.objects.filter(
            user_id=user_id,
            notification_type=rule.notification_event,
            is_active=True,
            is_deleted=False,
        ).first()
        if pref and pref.preferred_channels:
            return list(pref.preferred_channels)
        return [rule.channel] + list(rule.fallback_channels or [])

    @staticmethod
    def _is_channel_available(channel: str, *, user_id=None) -> bool:
        """Check channel is in Phase 1 active set and not in quiet hours."""
        if channel not in ACTIVE_CHANNELS:
            return False
        if user_id and WorkflowNotificationOrchestrator._in_quiet_hours(user_id):
            # Quiet hours block non-escalation messages
            return False
        return True

    @staticmethod
    def _in_quiet_hours(user_id) -> bool:
        """
        Returns True if the current time falls within the user's configured quiet hours.
        """
        pref = WorkflowNotificationPreference.objects.filter(
            user_id=user_id, is_active=True, is_deleted=False
        ).first()
        if not pref or not pref.quiet_hours_start or not pref.quiet_hours_end:
            return False
        now = timezone.localtime().time()
        qs  = pref.quiet_hours_start
        qe  = pref.quiet_hours_end
        if qs <= qe:
            return qs <= now <= qe
        # Overnight: e.g. 22:00 – 08:00
        return now >= qs or now <= qe

    # ─── Message rendering ────────────────────────────────────────────────────

    @staticmethod
    def render_notification(rule: WorkflowNotificationRule, context: dict) -> tuple[str, str]:
        """
        Returns (subject, body) with template placeholders resolved from context.
        Uses EmailTemplateDefinition when a template_id is set; otherwise generates
        a sensible default from the notification event.
        """
        if rule.template_id:
            try:
                from apps.communications.models import EmailTemplateDefinition
                tmpl = EmailTemplateDefinition.objects.filter(
                    id=rule.template_id, is_active=True
                ).first()
                if tmpl:
                    subject = WorkflowNotificationOrchestrator._fill_placeholders(tmpl.subject, context)
                    body    = WorkflowNotificationOrchestrator._fill_placeholders(tmpl.body_text or tmpl.body_html, context)
                    return subject, body
            except Exception:
                logger.warning('Template %s not found; using default', rule.template_id)

        # System default template
        event   = rule.notification_event.replace('_', ' ').replace('.', ' ').title()
        subject = f'{event} — {context.get("company_name", "Notification")}'
        body    = (
            f'Hi {context.get("candidate_name", context.get("recipient_name", "there"))},\n\n'
            f'{event} for {context.get("job_title", "your position")}.\n\n'
            f'Regards,\n{context.get("recruiter_name", context.get("company_name", "The Team"))}'
        )
        return subject, body

    @staticmethod
    def _fill_placeholders(template_str: str, context: dict) -> str:
        """Replace {{key}} placeholders with context values."""
        def replacer(match):
            key = match.group(1).strip()
            return str(context.get(key, match.group(0)))
        return re.sub(r'\{\{(\w+)\}\}', replacer, template_str or '')

    # ─── Delivery dispatch ────────────────────────────────────────────────────

    @staticmethod
    def send_notification(delivery: WorkflowNotificationDelivery) -> dict:
        """
        Dispatches a queued delivery via the appropriate channel adapter.
        Updates the delivery record with the result.
        """
        channel = delivery.channel
        try:
            if channel == NotificationChannel.IN_APP:
                result = WorkflowNotificationOrchestrator._send_in_app(delivery)
            elif channel == NotificationChannel.EMAIL:
                result = WorkflowNotificationOrchestrator._send_email(delivery)
            elif channel == NotificationChannel.WHATSAPP:
                result = WorkflowNotificationOrchestrator._send_whatsapp(delivery)
            else:
                # SMS / Push — Phase 2; mark as queued for later dispatch
                delivery.status   = DeliveryStatus.QUEUED
                delivery.metadata = {**delivery.metadata, 'phase2_channel': channel}
                delivery.save(update_fields=['status', 'metadata'])
                return {'status': 'queued', 'channel': channel, 'reason': 'phase2_channel'}

            delivery.status              = DeliveryStatus.SENT
            delivery.sent_at             = timezone.now()
            delivery.provider_message_id = result.get('message_id', '')
            delivery.save(update_fields=['status', 'sent_at', 'provider_message_id'])
            return {'status': 'sent', 'channel': channel, 'delivery_id': str(delivery.id)}

        except Exception as exc:
            logger.exception('Notification delivery failed: %s', exc)
            return WorkflowNotificationOrchestrator.handle_delivery_failure(delivery, str(exc))

    @staticmethod
    def _send_in_app(delivery: WorkflowNotificationDelivery) -> dict:
        if not delivery.recipient_user_id:
            raise ValueError('in_app requires recipient_user_id')
        from apps.communications.models import Notification
        n = Notification.objects.create(
            tenant_id=delivery.tenant_id,
            user_id=delivery.recipient_user_id,
            title=delivery.subject or 'Workflow Notification',
            body=delivery.rendered_message,
            notification_type='workflow_automation',
            metadata={
                'workflow_id': str(delivery.workflow_id) if delivery.workflow_id else '',
                'execution_id': str(delivery.execution_id) if delivery.execution_id else '',
                'delivery_id': str(delivery.id),
            },
        )
        return {'message_id': str(n.id)}

    @staticmethod
    def _send_email(delivery: WorkflowNotificationDelivery) -> dict:
        """
        Routes through the existing CommunicationDispatchService email stack.
        Returns a message_id on success.
        """
        if not delivery.recipient_email:
            raise ValueError('email channel requires recipient_email')
        try:
            from apps.communications.email_dispatch.types import EmailSendRequest
            from apps.communications.services import CommunicationDispatchService
            from shared.owner_contracts import OwnerActionContext

            request = EmailSendRequest(
                tenant_id=str(delivery.tenant_id),
                actor_user_id=None,
                email_type='business',
                message_purpose='workflow_notification',
                recipients=[delivery.recipient_email],
                subject=delivery.subject,
                body_html=delivery.rendered_message,
                body_text=delivery.rendered_message,
                trigger_source='workflow_notification',
                metadata={'delivery_id': str(delivery.id)},
            )
            context = OwnerActionContext(
                tenant_id=delivery.tenant_id,
                actor_id=None,
                external_reference=str(delivery.id),
            )
            result = CommunicationDispatchService.enqueue_email_from_orchestration(
                context=context, request=request, dedupe_key=delivery.dedupe_key
            )
            return {'message_id': str(result)}
        except Exception as exc:
            raise RuntimeError(f'Email dispatch failed: {exc}') from exc

    @staticmethod
    def _send_whatsapp(delivery: WorkflowNotificationDelivery) -> dict:
        """
        WhatsApp delivery stub — integrates with the platform's WhatsApp provider.
        Returns a synthetic message_id; replace with real provider call when available.
        """
        phone = delivery.recipient_phone or delivery.metadata.get('phone', '')
        if not phone:
            raise ValueError('whatsapp channel requires recipient_phone')
        # Stub: in production, call the WhatsApp Business API / Twilio / etc.
        logger.info(
            'WhatsApp stub — would send to %s: %s',
            phone,
            delivery.rendered_message[:80],
        )
        return {'message_id': f'wa_stub_{delivery.id}'}

    # ─── Failure handling ─────────────────────────────────────────────────────

    @staticmethod
    def handle_delivery_failure(delivery: WorkflowNotificationDelivery, reason: str = '') -> dict:
        delivery.retry_count   += 1
        delivery.failure_reason = reason
        delivery.failed_at      = timezone.now()

        if delivery.retry_count < MAX_RETRIES:
            delivery.status = DeliveryStatus.QUEUED   # re-queued for retry
            delivery.save(update_fields=['retry_count', 'failure_reason', 'failed_at', 'status'])
            return {'status': 'retry_queued', 'retry_count': delivery.retry_count}

        delivery.status = DeliveryStatus.FAILED
        delivery.save(update_fields=['retry_count', 'failure_reason', 'failed_at', 'status'])

        # Attempt fallback channel if rule has one
        if delivery.notification_rule:
            return WorkflowNotificationOrchestrator.queue_fallback_channel(delivery)

        return {'status': 'failed', 'reason': reason}

    @staticmethod
    def queue_fallback_channel(delivery: WorkflowNotificationDelivery) -> dict:
        """
        Creates a new delivery record on the next available fallback channel.
        """
        rule = delivery.notification_rule
        if not rule:
            return {'status': 'failed', 'reason': 'no_fallback_rule'}

        fallbacks = list(rule.fallback_channels or [])
        # Remove the already-tried channel
        if delivery.channel in fallbacks:
            idx = fallbacks.index(delivery.channel)
            fallbacks = fallbacks[idx + 1:]

        for fallback_ch in fallbacks:
            if fallback_ch in ACTIVE_CHANNELS:
                fallback_delivery = WorkflowNotificationDelivery.objects.create(
                    tenant_id=delivery.tenant_id,
                    execution_id=delivery.execution_id,
                    workflow_id=delivery.workflow_id,
                    notification_rule=rule,
                    recipient_user_id=delivery.recipient_user_id,
                    recipient_email=delivery.recipient_email,
                    recipient_phone=delivery.recipient_phone,
                    channel=fallback_ch,
                    status=DeliveryStatus.QUEUED,
                    subject=delivery.subject,
                    rendered_message=delivery.rendered_message,
                    dedupe_key=f'{delivery.dedupe_key}:fallback:{fallback_ch}',
                    metadata={**delivery.metadata, 'fallback_from': delivery.channel, 'parent_delivery_id': str(delivery.id)},
                )
                return WorkflowNotificationOrchestrator.send_notification(fallback_delivery)

        return {'status': 'failed', 'reason': 'all_fallbacks_exhausted'}

    # ─── Throttle / dedupe ────────────────────────────────────────────────────

    @staticmethod
    def should_throttle(rule: WorkflowNotificationRule, recipient: dict, context: dict) -> bool:
        if not rule.throttle_window_minutes:
            return False
        dedupe_key = WorkflowNotificationOrchestrator._build_dedupe_key(rule, recipient, context)
        cutoff = timezone.now() - timezone.timedelta(minutes=rule.throttle_window_minutes)
        return WorkflowNotificationDelivery.objects.filter(
            tenant_id=rule.tenant_id,
            dedupe_key=dedupe_key,
            status__in=[DeliveryStatus.SENT, DeliveryStatus.DELIVERED, DeliveryStatus.QUEUED],
            created_at__gte=cutoff,
        ).exists()

    @staticmethod
    def should_deduplicate(rule: WorkflowNotificationRule, recipient: dict, context: dict) -> bool:
        """Deduplicate identical messages regardless of throttle window."""
        dedupe_key = WorkflowNotificationOrchestrator._build_dedupe_key(rule, recipient, context)
        if not dedupe_key:
            return False
        return WorkflowNotificationDelivery.objects.filter(
            tenant_id=rule.tenant_id,
            dedupe_key=dedupe_key,
            status__in=[DeliveryStatus.SENT, DeliveryStatus.DELIVERED],
        ).exists()

    @staticmethod
    def _build_dedupe_key(rule: WorkflowNotificationRule, recipient: dict, context: dict) -> str:
        template = rule.dedupe_key_template
        if template:
            key = WorkflowNotificationOrchestrator._fill_placeholders(template, {**context, **recipient})
        else:
            uid = recipient.get('user_id') or recipient.get('email', '')
            key = f'{rule.workflow_id}:{rule.notification_event}:{uid}'
        # Normalise to safe fixed-length key
        return hashlib.sha256(key.encode()).hexdigest()[:64]

    # ─── Quiet hours ──────────────────────────────────────────────────────────

    @staticmethod
    def _is_in_quiet_hours(user_id, *, escalation: bool = False) -> bool:
        pref = WorkflowNotificationPreference.objects.filter(
            user_id=user_id, is_active=True, is_deleted=False
        ).first()
        if not pref:
            return False
        if escalation and pref.allow_escalation_override:
            return False
        return WorkflowNotificationOrchestrator._in_quiet_hours(user_id)

    # ─── Escalation ───────────────────────────────────────────────────────────

    @staticmethod
    def send_escalation_notification(
        *,
        tenant_id,
        workflow_id,
        execution_id=None,
        reason: str,
        context: dict,
        level: int = 1,
    ) -> dict:
        """
        Creates an escalation record and dispatches a notification to the
        next responsible user in the escalation chain.
        """
        # Determine escalation target
        target_type = RecipientType.RECRUITER_MANAGER if level == 1 else RecipientType.HIRING_MANAGER
        recipients  = WorkflowNotificationOrchestrator.resolve_recipients(context, target_type)
        channel     = NotificationChannel.EMAIL

        escalation = WorkflowEscalationNotification.objects.create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            escalation_level=level,
            trigger_reason=reason,
            target_recipient_type=target_type,
            channel=channel,
            status=EscalationStatus.PENDING,
        )

        sent_count = 0
        for recipient in recipients:
            # Bypass quiet hours for escalations with override
            uid = recipient.get('user_id')
            if uid and WorkflowNotificationOrchestrator._is_in_quiet_hours(uid, escalation=True):
                continue
            subject = f'[Escalation L{level}] {reason}'
            body    = (
                f'This is an escalation alert.\n\n'
                f'Reason: {reason}\n'
                f'Workflow: {workflow_id}\n'
                f'Execution: {execution_id}\n\n'
                f'Please take action immediately.'
            )
            delivery = WorkflowNotificationDelivery.objects.create(
                tenant_id=tenant_id,
                execution_id=execution_id,
                workflow_id=workflow_id,
                recipient_user_id=recipient.get('user_id'),
                recipient_email=recipient.get('email', ''),
                channel=channel,
                status=DeliveryStatus.QUEUED,
                subject=subject,
                rendered_message=body,
                dedupe_key=f'escalation:{workflow_id}:{level}:{recipient.get("user_id", "")}',
                metadata={'escalation_id': str(escalation.id), 'level': level},
            )
            WorkflowNotificationOrchestrator.send_notification(delivery)
            sent_count += 1

        escalation.status = EscalationStatus.SENT if sent_count else EscalationStatus.PENDING
        escalation.sent_at = timezone.now() if sent_count else None
        escalation.save(update_fields=['status', 'sent_at'])

        return {'status': 'escalation_sent', 'level': level, 'recipients': sent_count}

    # ─── Channel health aggregation ───────────────────────────────────────────

    @staticmethod
    def get_channel_health(tenant_id) -> dict:
        """
        Returns delivery stats per channel for the last 7 days.
        """
        from django.db.models import Count, Q
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=7)
        qs = WorkflowNotificationDelivery.objects.filter(
            tenant_id=tenant_id, created_at__gte=cutoff
        )

        health = {}
        for ch in NotificationChannel.values:
            ch_qs   = qs.filter(channel=ch)
            total   = ch_qs.count()
            sent    = ch_qs.filter(status__in=[DeliveryStatus.SENT, DeliveryStatus.DELIVERED]).count()
            failed  = ch_qs.filter(status=DeliveryStatus.FAILED).count()
            fallback= ch_qs.filter(metadata__fallback_from__isnull=False).count()
            health[ch] = {
                'total':         total,
                'sent':          sent,
                'failed':        failed,
                'fallback_used': fallback,
                'delivery_rate': round(sent / total * 100, 1) if total else 0.0,
                'failure_rate':  round(failed / total * 100, 1) if total else 0.0,
            }
        return health

    # ─── Insight generation ───────────────────────────────────────────────────

    @staticmethod
    def generate_insights(tenant_id) -> list[dict]:
        """
        Scans recent deliveries and creates WorkflowNotificationInsight records
        for patterns that need attention.
        """
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=1)
        insights = []

        # High failure rate check
        qs    = WorkflowNotificationDelivery.objects.filter(tenant_id=tenant_id, created_at__gte=cutoff)
        total = qs.count()
        if total >= 10:
            failed      = qs.filter(status=DeliveryStatus.FAILED).count()
            failure_pct = failed / total * 100
            if failure_pct > 20:
                i = WorkflowNotificationInsight.objects.create(
                    tenant_id=tenant_id,
                    insight_type=InsightType.HIGH_FAILURE_RATE,
                    title='High notification failure rate detected',
                    description=f'{failure_pct:.1f}% of notifications failed in the last 24 hours.',
                    metric_value=failure_pct,
                )
                insights.append({'id': str(i.id), 'type': i.insight_type, 'title': i.title})

        # Duplicate risk check
        deduped = qs.filter(status=DeliveryStatus.DEDUPLICATED).count()
        if total >= 5 and deduped / max(total, 1) > 0.3:
            i = WorkflowNotificationInsight.objects.create(
                tenant_id=tenant_id,
                insight_type=InsightType.DUPLICATE_RISK,
                title='High deduplication rate — possible rule misconfiguration',
                description=f'{deduped} of {total} notifications were deduplicated.',
                metric_value=round(deduped / total * 100, 1),
            )
            insights.append({'id': str(i.id), 'type': i.insight_type, 'title': i.title})

        return insights
