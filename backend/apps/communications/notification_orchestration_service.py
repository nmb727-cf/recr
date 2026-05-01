"""
Notification Orchestration Service
=====================================
Central brain for all notification automation decisions.

Responsibilities:
- Resolve which notification rule applies (system default → tenant override)
- Resolve recipients for a given event + entity
- Resolve which channels to use
- Resolve which template to render
- Resolve escalation target for a rule
- Schedule automation jobs with full tracking
- Cancel pending jobs when notification is read/resolved
- Build template context for email rendering
- Render fallback notification emails

All business modules interact with NotificationService.create_notification().
This service is called internally by the notification layer — never directly
by business modules.

Architecture invariant: no circular imports from other business modules.
Safe lookups use try/except + lazy imports where required.
"""
import logging
from datetime import timedelta
from typing import Optional

from django.db import transaction
from django.utils import timezone
from shared.actor_access import COMPANY_HIRING_ROLES, TENANT_ADMIN_ROLES, PLATFORM_ADMIN_ROLES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Resolve notification rule
# ---------------------------------------------------------------------------

def resolve_notification_rule(
    *,
    tenant_id,
    event_key: str,
):
    """
    Return the best-matching NotificationRule for (tenant_id, event_key).

    Lookup order:
      1. Tenant-specific rule
      2. System default (tenant_id=None, is_system=True)
      3. None — caller uses hardcoded severity defaults
    """
    from apps.communications.notification_control_service import NotificationControlService
    return NotificationControlService.get_rule(
        tenant_id=tenant_id,
        event_key=event_key,
    )


# ---------------------------------------------------------------------------
# Resolve channels
# ---------------------------------------------------------------------------

def resolve_channels(
    *,
    rule,
    tenant_id,
) -> dict:
    """
    Return channel flags for a given rule + tenant.
    Checks global channel-level settings (can disable email entirely for a tenant).

    Returns dict: {'in_app': bool, 'email': bool, 'whatsapp': bool, 'sms': bool}
    """
    from apps.communications.notification_control_service import NotificationControlService

    if rule is None:
        return {
            'in_app': True,
            'email': False,
            'whatsapp': False,
            'sms': False,
        }

    email_globally_enabled = NotificationControlService.channel_enabled(
        tenant_id=tenant_id, channel='email'
    )
    whatsapp_globally_enabled = NotificationControlService.channel_enabled(
        tenant_id=tenant_id, channel='whatsapp'
    )
    sms_globally_enabled = NotificationControlService.channel_enabled(
        tenant_id=tenant_id, channel='sms'
    )

    return {
        'in_app':    rule.in_app_enabled,
        'email':     rule.email_enabled and email_globally_enabled,
        'whatsapp':  rule.whatsapp_enabled and whatsapp_globally_enabled,
        'sms':       rule.sms_enabled and sms_globally_enabled,
    }


# ---------------------------------------------------------------------------
# Resolve template
# ---------------------------------------------------------------------------

def resolve_template(
    *,
    event_key: str,
    tenant_id,
    rule=None,
):
    """
    Return the best email template for this event + tenant.

    Priority:
      1. Template linked to the rule (rule.template_id)
      2. System template matching event_key slug
      3. None — caller uses generic fallback HTML
    """
    if rule and rule.template_id:
        try:
            from apps.communications.models import EmailTemplateDefinition
            tpl = EmailTemplateDefinition.objects.filter(
                id=rule.template_id,
                is_active=True,
            ).first()
            if tpl:
                return tpl
        except Exception as exc:
            logger.debug('Could not load rule template %s: %s', rule.template_id, exc)

    # Fall back to slug-based lookup
    slug = event_key.replace('.', '_').replace(' ', '_').lower()
    try:
        from apps.communications.models import EmailTemplateDefinition
        return EmailTemplateDefinition.objects.filter(
            slug=slug,
            is_active=True,
        ).order_by('tenant_id').first()  # prefer tenant-specific first
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Resolve escalation target
# ---------------------------------------------------------------------------

def resolve_escalation_target(
    *,
    notification,
    rule,
    tenant_id,
) -> Optional[object]:
    """
    Resolve the user who should receive the escalation notification.

    Supports target types:
      - assigned_manager  → manager of the notification's original recipient
      - hiring_manager    → hiring manager from the related entity (if application/interview)
      - recruiter_lead    → first active recruiter with tenant_admin/hr_manager role
      - tenant_admin      → first active tenant admin
    Returns a User instance or None if not resolvable.
    """
    target_type = (rule.escalation_target_type if rule else 'tenant_admin') or 'tenant_admin'

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if target_type == 'assigned_manager':
            return _resolve_assigned_manager(notification, User)

        if target_type == 'hiring_manager':
            hiring_mgr = _resolve_hiring_manager(notification, User)
            if hiring_mgr:
                return hiring_mgr
            # Fallback to tenant admin
            return _resolve_tenant_admin(tenant_id, User)

        if target_type == 'recruiter_lead':
            return _resolve_recruiter_lead(tenant_id, User)

        # Default: tenant_admin
        return _resolve_tenant_admin(tenant_id, User)

    except Exception as exc:
        logger.warning('Could not resolve escalation target (type=%s): %s', target_type, exc)
        return None


def _resolve_assigned_manager(notification, User):
    """Find manager of the notification's original recipient."""
    # The user model may store a manager_id or manager relationship
    try:
        original_user = User.objects.filter(id=notification.user_id).first()
        if not original_user:
            return None
        manager_id = getattr(original_user, 'manager_id', None)
        if manager_id:
            return User.objects.filter(id=manager_id, is_active=True).first()
        # No direct manager field — fall back to tenant admin
        return _resolve_tenant_admin(notification.tenant_id, User)
    except Exception:
        return None


def _resolve_hiring_manager(notification, User):
    """Try to find the hiring manager from the related entity (application or interview)."""
    entity_type = notification.related_entity_type
    entity_id = notification.related_entity_id
    if not entity_type or not entity_id:
        return None

    try:
        if entity_type == 'application':
            from apps.pipeline.models import Application
            app = Application.objects.filter(id=entity_id).first()
            if app and app.requisition_id:
                from apps.jobs.models import JobRequisition
                req = JobRequisition.objects.filter(id=app.requisition_id).first()
                if req:
                    # Try approved_by or current_approver_id as hiring manager proxy
                    hm_id = getattr(req, 'approved_by', None) or getattr(req, 'current_approver_id', None)
                    if hm_id:
                        return User.objects.filter(id=hm_id, is_active=True).first()

        if entity_type == 'interview':
            from apps.interviews.models import Interview
            iv = Interview.objects.filter(id=entity_id).first()
            if iv and iv.requisition_id:
                from apps.jobs.models import JobRequisition
                req = JobRequisition.objects.filter(id=iv.requisition_id).first()
                if req:
                    hm_id = getattr(req, 'approved_by', None) or getattr(req, 'current_approver_id', None)
                    if hm_id:
                        return User.objects.filter(id=hm_id, is_active=True).first()
    except Exception:
        pass
    return None


def _resolve_recruiter_lead(tenant_id, User):
    """Return the first active HR manager or tenant admin for the tenant."""
    try:
        user = User.objects.filter(
            tenant_id=tenant_id,
            role__in=list(COMPANY_HIRING_ROLES - {'hiring_manager'}),
            is_active=True,
            is_deleted=False,
        ).order_by('created_at').first()
        if user:
            return user
        return _resolve_tenant_admin(tenant_id, User)
    except Exception:
        return None


def _resolve_tenant_admin(tenant_id, User):
    """Return the first active tenant admin for the tenant."""
    try:
        return User.objects.filter(
            tenant_id=tenant_id,
            role__in=list(TENANT_ADMIN_ROLES | PLATFORM_ADMIN_ROLES),
            is_active=True,
            is_deleted=False,
        ).order_by('created_at').first()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Recipients resolution
# ---------------------------------------------------------------------------

def resolve_recipients(
    *,
    event_key: str,
    entity_type: str,
    entity_id,
    tenant_id,
    extra_context: dict = None,
) -> list:
    """
    Resolve the list of user IDs that should receive a notification
    for the given event + entity.

    Returns a list of user ID strings.
    Business logic per event_key lives here so it is centralised.
    """
    context = extra_context or {}
    recipients = []

    try:
        if event_key in ('application.submitted', 'agency.candidate_submitted'):
            uid = context.get('recruiter_user_id') or context.get('owner_user_id')
            if uid:
                recipients.append(str(uid))

        elif event_key in ('application.shortlisted', 'application.rejected', 'offer.sent',
                           'offer.response_pending'):
            uid = context.get('candidate_user_id')
            if uid:
                recipients.append(str(uid))

        elif event_key in ('interview.scheduled', 'interview.rescheduled', 'interview.cancelled'):
            for uid in [context.get('candidate_user_id')] + list(context.get('interviewer_user_ids') or []):
                if uid:
                    recipients.append(str(uid))

        elif event_key == 'interview.feedback_pending':
            for uid in list(context.get('panelist_user_ids') or []):
                if uid:
                    recipients.append(str(uid))

        elif event_key in ('offer.accepted', 'offer.rejected'):
            for uid in [context.get('recruiter_user_id'), context.get('hiring_manager_user_id')]:
                if uid:
                    recipients.append(str(uid))

        elif event_key in ('approval.requested', 'approval.overdue'):
            uid = context.get('approver_user_id')
            if uid:
                recipients.append(str(uid))

        elif event_key == 'deadline.overdue':
            uid = context.get('owner_user_id')
            if uid:
                recipients.append(str(uid))

        elif event_key == 'message.created':
            for uid in list(context.get('recipient_user_ids') or []):
                if uid:
                    recipients.append(str(uid))

        elif event_key == 'passport.viewed':
            uid = context.get('candidate_user_id')
            if uid:
                recipients.append(str(uid))

    except Exception as exc:
        logger.warning('resolve_recipients error for %s: %s', event_key, exc)

    # Deduplicate while preserving order
    seen = set()
    return [r for r in recipients if not (r in seen or seen.add(r))]


# ---------------------------------------------------------------------------
# Template context builder
# ---------------------------------------------------------------------------

def build_template_context(
    *,
    event_key: str,
    entity_type: str = '',
    entity_id=None,
    notification=None,
    extra: dict = None,
) -> dict:
    """
    Build a safe, sanitised variable dict for email template rendering.
    Missing variables produce empty strings — never raise.
    """
    ctx = {
        'event_key':          event_key,
        'entity_type':        entity_type or '',
        'entity_id':          str(entity_id) if entity_id else '',
        'platform_name':      'Talent OS',
        'notification_title': '',
        'notification_body':  '',
        'action_url':         '',
    }

    if notification:
        ctx.update({
            'notification_title': notification.title or '',
            'notification_body':  notification.body or '',
            'action_url':         notification.action_url or '',
            'severity':           notification.severity or 'info',
        })

    if extra:
        # Sanitise: only allow string-safe values
        for k, v in extra.items():
            try:
                ctx[str(k)] = str(v) if v is not None else ''
            except Exception:
                ctx[str(k)] = ''

    # Load entity-specific context safely
    try:
        _enrich_entity_context(ctx, entity_type, entity_id)
    except Exception as exc:
        logger.debug('Could not enrich entity context for %s/%s: %s', entity_type, entity_id, exc)

    return ctx


def _enrich_entity_context(ctx: dict, entity_type: str, entity_id):
    """Enrich template context with entity fields (candidate name, job title, etc.)."""
    if not entity_type or not entity_id:
        return

    if entity_type == 'application':
        from apps.pipeline.models import Application
        app = Application.objects.filter(id=entity_id).first()
        if app:
            ctx['application_status'] = app.status or ''
            try:
                from apps.jobs.models import JobRequisition
                req = JobRequisition.objects.filter(id=app.requisition_id).first()
                if req:
                    ctx['job_title'] = req.title or ''
            except Exception:
                pass

    elif entity_type == 'interview':
        from apps.interviews.models import Interview
        iv = Interview.objects.filter(id=entity_id).first()
        if iv:
            ctx['interview_type'] = iv.interview_type or ''
            ctx['interview_title'] = iv.title or ''
            if iv.scheduled_at:
                ctx['scheduled_at'] = str(iv.scheduled_at)

    elif entity_type == 'candidate':
        from apps.candidates.models import Candidate
        cand = Candidate.objects.filter(id=entity_id).first()
        if cand:
            ctx['candidate_name'] = f'{cand.first_name} {cand.last_name}'.strip()


# ---------------------------------------------------------------------------
# Email renderer
# ---------------------------------------------------------------------------

def render_notification_email(
    *,
    notification,
    rule=None,
    context: dict = None,
) -> tuple:
    """
    Render subject + HTML body for a notification email.

    Returns: (subject: str, body_html: str, body_text: str)
    Uses template when available; falls back to generic HTML.
    """
    ctx = context or {}
    template = resolve_template(
        event_key=notification.get_type(),
        tenant_id=notification.tenant_id,
        rule=rule,
    )

    subject = f'[Action Required] {notification.title}'
    body_text = f'{notification.body}\n\nAction: {notification.action_url or "N/A"}'

    if template:
        try:
            rendered_subject = _render_string(template.subject_template, ctx)
            rendered_html = _render_string(template.body_html, ctx)
            rendered_text = _render_string(template.body_text, ctx) if template.body_text else body_text
            if rendered_subject:
                subject = rendered_subject
            if rendered_html:
                return subject, rendered_html, rendered_text
        except Exception as exc:
            logger.warning('Template render failed for notification %s: %s', notification.id, exc)

    # Generic fallback HTML
    body_html = _generic_fallback_html(notification)
    return subject, body_html, body_text


def _render_string(template_str: str, context: dict) -> str:
    """Simple {variable} substitution — never raises."""
    try:
        return template_str.format_map(_SafeDict(context))
    except Exception:
        return template_str


class _SafeDict(dict):
    """dict subclass that returns empty string for missing keys during str.format_map."""
    def __missing__(self, key):
        return ''


def _generic_fallback_html(notification) -> str:
    action_btn = ''
    if notification.action_url:
        action_btn = (
            f'<p><a href="{notification.action_url}" '
            f'style="background:#4f46e5;color:#fff;padding:10px 20px;'
            f'border-radius:6px;text-decoration:none;">View Now</a></p>'
        )
    return (
        '<div style="font-family:sans-serif;max-width:600px;margin:auto;">'
        f'<h2 style="color:#1a1a2e;">{notification.title}</h2>'
        f'<p>{notification.body}</p>'
        f'{action_btn}'
        '<hr/>'
        '<p style="color:#888;font-size:12px;">'
        'This is an automated notification reminder from Talent OS. '
        f'Severity: {notification.severity}.</p>'
        '</div>'
    )


# ---------------------------------------------------------------------------
# Automation job scheduler
# ---------------------------------------------------------------------------

def schedule_automation_job(
    *,
    tenant_id,
    notification_id,
    event_key: str,
    job_type: str,
    delay_seconds: int,
    related_entity_type: str = '',
    related_entity_id=None,
    metadata: dict = None,
) -> 'NotificationAutomationJob':
    """
    Create a NotificationAutomationJob record and enqueue the corresponding
    Celery task.  Returns the job instance.
    """
    from apps.communications.notification_orchestration_models import (
        NotificationAutomationJob,
        NotificationAutomationJobType,
    )

    scheduled_for = timezone.now() + timedelta(seconds=delay_seconds)

    job = NotificationAutomationJob.objects.create(
        tenant_id=tenant_id,
        notification_id=notification_id,
        event_key=event_key,
        job_type=job_type,
        scheduled_for=scheduled_for,
        related_entity_type=related_entity_type or '',
        related_entity_id=related_entity_id,
        metadata=metadata or {},
    )

    # Enqueue the appropriate Celery task
    try:
        from apps.communications import orchestration_tasks as tasks
        if job_type == NotificationAutomationJobType.FALLBACK_EMAIL:
            result = tasks.execute_fallback_job.apply_async(
                args=[str(job.id)],
                countdown=delay_seconds,
            )
        elif job_type == NotificationAutomationJobType.ESCALATION:
            result = tasks.execute_escalation_job.apply_async(
                args=[str(job.id)],
                countdown=delay_seconds,
            )
        elif job_type == NotificationAutomationJobType.REMINDER:
            result = tasks.execute_reminder_job.apply_async(
                args=[str(job.id)],
                countdown=delay_seconds,
            )
        else:
            result = None

        if result:
            job.celery_task_id = str(result.id)
            job.save(update_fields=['celery_task_id', 'updated_at'])

    except Exception as exc:
        logger.warning(
            'Failed to enqueue automation task for job %s (type=%s): %s',
            job.id, job_type, exc,
        )

    return job


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------

def cancel_pending_jobs(
    *,
    notification_id,
    reason: str = 'notification_read',
):
    """
    Cancel all PENDING automation jobs for a notification.
    Called when a notification is read or the related entity is resolved.

    This is a synchronous, lightweight operation — safe to call from
    NotificationService.mark_read() on the request path.
    """
    from apps.communications.notification_orchestration_models import (
        NotificationAutomationJob,
        NotificationAutomationJobStatus,
    )

    cancelled = (
        NotificationAutomationJob.objects
        .filter(
            notification_id=notification_id,
            status=NotificationAutomationJobStatus.PENDING,
        )
        .update(
            status=NotificationAutomationJobStatus.CANCELLED,
            cancel_reason=reason,
            updated_at=timezone.now(),
        )
    )
    if cancelled:
        logger.debug(
            'Cancelled %d pending automation jobs for notification %s (reason=%s)',
            cancelled, notification_id, reason,
        )
    return cancelled


def cancel_entity_jobs(
    *,
    related_entity_type: str,
    related_entity_id,
    reason: str = 'entity_resolved',
):
    """
    Cancel all PENDING automation jobs linked to a specific entity,
    across all notifications.  Used when e.g. an interview feedback
    is submitted and pending feedback reminders should stop.
    """
    from apps.communications.notification_orchestration_models import (
        NotificationAutomationJob,
        NotificationAutomationJobStatus,
    )

    cancelled = (
        NotificationAutomationJob.objects
        .filter(
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            status=NotificationAutomationJobStatus.PENDING,
        )
        .update(
            status=NotificationAutomationJobStatus.CANCELLED,
            cancel_reason=reason,
            updated_at=timezone.now(),
        )
    )
    if cancelled:
        logger.debug(
            'Cancelled %d jobs for entity %s/%s (reason=%s)',
            cancelled, related_entity_type, related_entity_id, reason,
        )
    return cancelled


# ---------------------------------------------------------------------------
# Full orchestration entry point
# ---------------------------------------------------------------------------

def orchestrate_notification_event(
    *,
    event_key: str,
    tenant_id,
    entity_type: str = '',
    entity_id=None,
    extra_context: dict = None,
) -> list:
    """
    High-level entry point called by event handlers.

    Steps:
      1. Resolve rule
      2. Resolve channel plan (immediate + fallback + escalation)
      3. Resolve recipients
      4. For each recipient:
         a. Create in-app notification
         b. Execute immediate channels (email via existing path, WA/SMS via channel_services)
         c. Schedule fallback channel jobs
         d. Schedule escalation channel jobs
      5. Return list of created notifications

    Swallows all exceptions so a bad notification never breaks business flow.
    """
    from apps.communications.notification_service import NotificationService
    from apps.communications.models import NotificationSeverity
    from apps.communications.channel_routing import resolve_channel_plan

    ctx = extra_context or {}
    notifications = []

    try:
        rule = resolve_notification_rule(tenant_id=tenant_id, event_key=event_key)
        if rule and not rule.is_active:
            logger.debug('Notification suppressed by inactive rule: %s / %s', event_key, tenant_id)
            return []

        channels = resolve_channels(rule=rule, tenant_id=tenant_id)
        if not channels['in_app'] and rule:
            # Rule explicitly disabled in-app; skip entirely
            return []

        recipients = resolve_recipients(
            event_key=event_key,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            extra_context=ctx,
        )

        title = ctx.get('title', event_key.replace('.', ' ').replace('_', ' ').title())
        body = ctx.get('body', '')
        action_url = ctx.get('action_url', '')
        severity = (rule.priority if rule else None) or NotificationSeverity.INFO

        # Resolve the full multi-channel plan
        channel_plan = resolve_channel_plan(
            tenant_id=tenant_id,
            event_key=event_key,
            priority=severity,
            recipient_context=ctx,
            rule_config=rule,
        )

        for recipient_id in recipients:
            # ── a) Create in-app notification ──────────────────────────────
            n = NotificationService.create_notification(
                user_id=recipient_id,
                title=title,
                body=body,
                notification_type=event_key,
                severity=severity,
                action_url=action_url,
                related_entity_type=entity_type,
                related_entity_id=entity_id,
                tenant_id=tenant_id,
                schedule_fallback=True,  # email fallback still handled by existing path
                metadata={
                    'event_key': event_key,
                    'entity_type': entity_type,
                    'entity_id': str(entity_id) if entity_id else '',
                    **{k: str(v) for k, v in ctx.items() if isinstance(v, (str, int, float, bool))},
                },
            )
            if n:
                notifications.append(n)

            # ── b+c+d) Execute multi-channel plan for this recipient ───────
            if n:
                _execute_channel_plan_for_recipient(
                    plan=channel_plan,
                    notification=n,
                    recipient_user_id=recipient_id,
                    tenant_id=tenant_id,
                    event_key=event_key,
                    priority=severity,
                    ctx=ctx,
                )

    except Exception as exc:
        logger.error(
            'orchestrate_notification_event failed for event=%s tenant=%s: %s',
            event_key, tenant_id, exc,
        )

    return notifications


def _execute_channel_plan_for_recipient(
    *,
    plan,
    notification,
    recipient_user_id,
    tenant_id,
    event_key: str,
    priority: str,
    ctx: dict,
):
    """
    Execute the channel plan for a single notification+recipient pair.

    - Immediate WA/SMS/Push channels: queued as async tasks (countdown=0)
    - Fallback channels: queued with delay
    - Escalation channels: queued with longer delay

    Email is intentionally excluded here — the existing email fallback path
    (NotificationService + execute_fallback_job) handles email.
    """
    from apps.communications.channel_services import (
        send_via_channel,
        schedule_channel_fallback,
        normalize_recipient_for_channel,
    )

    # Build recipient context — resolve phone number from user record
    recipient_phone = ctx.get('recipient_phone', '') or _resolve_user_phone(recipient_user_id)
    push_token      = ctx.get('push_token', '')

    def get_identifier(channel_type: str) -> str:
        if channel_type in ('whatsapp', 'sms'):
            return recipient_phone
        if channel_type == 'push':
            return push_token or str(recipient_user_id)
        return str(recipient_user_id)

    # Skip 'in_app' and 'email' — handled elsewhere
    skip_channels = {'in_app', 'email'}

    # ── Immediate non-email channels ────────────────────────────────────────
    for step in plan.immediate_channels:
        if step.channel_type in skip_channels or step.suppressed:
            continue
        try:
            send_via_channel(
                tenant_id=tenant_id,
                channel_type=step.channel_type,
                recipient_identifier=get_identifier(step.channel_type),
                recipient_user_id=recipient_user_id,
                notification_id=notification.id,
                event_key=event_key,
                priority=priority,
                context={**ctx, 'title': notification.title, 'body': notification.body,
                         'action_url': notification.action_url},
                notification=notification,
                schedule_async=True,
            )
        except Exception as exc:
            logger.error(
                '_execute_channel_plan_for_recipient: immediate send error '
                'channel=%s notification=%s: %s',
                step.channel_type, notification.id, exc,
            )

    # ── Fallback channels (scheduled) ───────────────────────────────────────
    for step in plan.fallback_channels:
        if step.channel_type in skip_channels or step.suppressed:
            continue
        try:
            schedule_channel_fallback(
                tenant_id=tenant_id,
                notification_id=notification.id,
                event_key=event_key,
                channel_step=step,
                recipient_identifier=get_identifier(step.channel_type),
                recipient_user_id=recipient_user_id,
                priority=priority,
                context={**ctx, 'title': notification.title, 'body': notification.body,
                         'action_url': notification.action_url},
                notification=notification,
            )
        except Exception as exc:
            logger.error(
                '_execute_channel_plan_for_recipient: fallback schedule error '
                'channel=%s notification=%s: %s',
                step.channel_type, notification.id, exc,
            )

    # ── Escalation channels (scheduled) ─────────────────────────────────────
    for step in plan.escalation_channels:
        if step.channel_type in skip_channels or step.suppressed:
            continue
        try:
            schedule_channel_fallback(
                tenant_id=tenant_id,
                notification_id=notification.id,
                event_key=event_key,
                channel_step=step,
                recipient_identifier=get_identifier(step.channel_type),
                recipient_user_id=recipient_user_id,
                priority=priority,
                context={**ctx, 'title': notification.title, 'body': notification.body,
                         'action_url': notification.action_url},
                notification=notification,
            )
        except Exception as exc:
            logger.error(
                '_execute_channel_plan_for_recipient: escalation schedule error '
                'channel=%s notification=%s: %s',
                step.channel_type, notification.id, exc,
            )

    # Log suppressed channels for observability
    for step in plan.suppressed_channels:
        if step.channel_type in skip_channels:
            continue
        logger.debug(
            '_execute_channel_plan_for_recipient: channel=%s suppressed for tenant=%s '
            '(reason=%s) notification=%s',
            step.channel_type, tenant_id, step.suppress_reason, notification.id,
        )


def _resolve_user_phone(user_id) -> str:
    """Look up user phone (whatsapp field preferred) from accounts."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(id=user_id).first()
        if not user:
            return ''
        # Prefer whatsapp field if available, fall back to phone
        return (
            getattr(user, 'whatsapp', '') or
            getattr(user, 'phone', '') or
            ''
        )
    except Exception as exc:
        logger.debug('_resolve_user_phone error for user %s: %s', user_id, exc)
        return ''
