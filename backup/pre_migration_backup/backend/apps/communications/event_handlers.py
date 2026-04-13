"""
Communication Event Handlers
=============================
Consumes events emitted by other business modules and reacts by:
  - Creating in-app notifications
  - Creating system messages in context threads
  - Scheduling fallback emails

Architecture rule: this module receives events — it does NOT call business
modules back. No circular imports. No direct module dependencies.

All signal receivers use kwargs.get() pattern for forward-compatibility.
"""
import logging

from django.dispatch import receiver
from django.utils import timezone

from apps.core import events
from apps.communications.models import NotificationSeverity
from apps.communications.notification_service import NotificationService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_id(obj_or_id):
    if obj_or_id is None:
        return None
    if hasattr(obj_or_id, 'id'):
        return obj_or_id.id
    return obj_or_id


def _create_notification_safe(**kwargs):
    """Wrapper that swallows exceptions so a bad notification never breaks a business flow."""
    try:
        return NotificationService.create_notification(**kwargs)
    except Exception as exc:
        logger.error('Failed to create notification: %s | kwargs=%s', exc, kwargs)
        return None


def _add_system_message_safe(*, tenant_id, related_entity_type, related_entity_id, body, thread_type='general'):
    """Add a system message to the context thread for an entity (creates thread if needed)."""
    try:
        from apps.communications.communication_service import ThreadService
        thread, _ = ThreadService.get_or_create_context_thread(
            tenant_id=tenant_id,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            thread_type=thread_type,
            subject=f'Timeline: {related_entity_type}',
        )
        ThreadService.add_system_message(
            thread_id=thread.id,
            tenant_id=tenant_id,
            body=body,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )
    except Exception as exc:
        logger.error('Failed to add system message: %s', exc)


# ---------------------------------------------------------------------------
# Application Events
# ---------------------------------------------------------------------------

@receiver(events.application.created)
def on_application_submitted(sender, **kwargs):
    """Notify hiring manager/recruiter when a candidate applies."""
    app = kwargs.get('application')
    if not app:
        return

    # Notify recruiter/owner if available
    recipient_user_id = kwargs.get('recruiter_user_id') or kwargs.get('owner_user_id')
    if recipient_user_id:
        _create_notification_safe(
            user_id=recipient_user_id,
            title='New Application Received',
            body=f'A candidate has applied for {getattr(app, "job_title", "a position")}.',
            notification_type='application.submitted',
            severity=NotificationSeverity.INFO,
            action_url=f'/applications/{app.id}',
            related_entity_type='application',
            related_entity_id=_safe_id(app),
            tenant_id=getattr(app, 'tenant_id', None),
        )

    # Add system message to application timeline
    _add_system_message_safe(
        tenant_id=getattr(app, 'tenant_id', None),
        related_entity_type='application',
        related_entity_id=_safe_id(app),
        body='Application submitted.',
        thread_type='submission_context',
    )


@receiver(events.application.shortlisted)
def on_application_shortlisted(sender, **kwargs):
    app = kwargs.get('application')
    candidate_user_id = kwargs.get('candidate_user_id')
    if not app:
        return

    if candidate_user_id:
        _create_notification_safe(
            user_id=candidate_user_id,
            title='You have been shortlisted!',
            body='Great news — you have been shortlisted for the next stage.',
            notification_type='application.shortlisted',
            severity=NotificationSeverity.MEDIUM,
            action_url=f'/applications/{app.id}',
            related_entity_type='application',
            related_entity_id=_safe_id(app),
            tenant_id=getattr(app, 'tenant_id', None),
        )

    _add_system_message_safe(
        tenant_id=getattr(app, 'tenant_id', None),
        related_entity_type='application',
        related_entity_id=_safe_id(app),
        body='Candidate shortlisted.',
    )


@receiver(events.application.stage_changed)
def on_application_stage_changed(sender, **kwargs):
    app = kwargs.get('application')
    candidate_user_id = kwargs.get('candidate_user_id')
    new_stage = kwargs.get('new_stage', 'next stage')
    if not app:
        return

    if candidate_user_id:
        _create_notification_safe(
            user_id=candidate_user_id,
            title='Application Stage Updated',
            body=f'Your application has moved to: {new_stage}.',
            notification_type='application.stage_changed',
            severity=NotificationSeverity.INFO,
            action_url=f'/applications/{app.id}',
            related_entity_type='application',
            related_entity_id=_safe_id(app),
            tenant_id=getattr(app, 'tenant_id', None),
        )

    _add_system_message_safe(
        tenant_id=getattr(app, 'tenant_id', None),
        related_entity_type='application',
        related_entity_id=_safe_id(app),
        body=f'Stage changed to: {new_stage}.',
    )


# ---------------------------------------------------------------------------
# Interview Events
# ---------------------------------------------------------------------------

@receiver(events.interview.scheduled)
def on_interview_scheduled(sender, **kwargs):
    interview = kwargs.get('interview')
    if not interview:
        return

    tenant_id = getattr(interview, 'tenant_id', None)
    candidate_user_id = kwargs.get('candidate_user_id')
    interviewer_user_ids = kwargs.get('interviewer_user_ids') or []

    scheduled_at = getattr(interview, 'scheduled_at', None)
    title_str = getattr(interview, 'title', 'your interview')

    # Notify candidate
    if candidate_user_id:
        _create_notification_safe(
            user_id=candidate_user_id,
            title='Interview Scheduled',
            body=f'Your interview "{title_str}" has been scheduled{f" for {scheduled_at}" if scheduled_at else ""}.',
            notification_type='interview.scheduled',
            severity=NotificationSeverity.HIGH,
            action_url=f'/interviews/{interview.id}',
            related_entity_type='interview',
            related_entity_id=_safe_id(interview),
            tenant_id=tenant_id,
        )

    # Notify interviewers
    for interviewer_id in interviewer_user_ids:
        _create_notification_safe(
            user_id=interviewer_id,
            title='Interview Scheduled',
            body=f'You have been assigned to interview: "{title_str}".',
            notification_type='interview.scheduled',
            severity=NotificationSeverity.HIGH,
            action_url=f'/interviews/{interview.id}',
            related_entity_type='interview',
            related_entity_id=_safe_id(interview),
            tenant_id=tenant_id,
        )

    # Create/update interview coordination thread with system message
    _add_system_message_safe(
        tenant_id=tenant_id,
        related_entity_type='interview',
        related_entity_id=_safe_id(interview),
        body=f'Interview scheduled{f" for {scheduled_at}" if scheduled_at else ""}.',
        thread_type='interview_coordination',
    )


@receiver(events.interview.completed)
def on_interview_completed(sender, **kwargs):
    interview = kwargs.get('interview')
    if not interview:
        return

    tenant_id = getattr(interview, 'tenant_id', None)
    recruiter_user_id = kwargs.get('recruiter_user_id')

    if recruiter_user_id:
        _create_notification_safe(
            user_id=recruiter_user_id,
            title='Interview Completed — Feedback Pending',
            body='An interview has been completed. Please review and record feedback.',
            notification_type='interview.feedback_pending',
            severity=NotificationSeverity.MEDIUM,
            action_url=f'/interviews/{interview.id}/feedback',
            related_entity_type='interview',
            related_entity_id=_safe_id(interview),
            tenant_id=tenant_id,
        )

    _add_system_message_safe(
        tenant_id=tenant_id,
        related_entity_type='interview',
        related_entity_id=_safe_id(interview),
        body='Interview completed. Feedback required.',
        thread_type='interview_coordination',
    )


# ---------------------------------------------------------------------------
# Offer Events
# ---------------------------------------------------------------------------

@receiver(events.application.offer_made)
def on_offer_sent(sender, **kwargs):
    app = kwargs.get('application')
    candidate_user_id = kwargs.get('candidate_user_id')
    if not app:
        return

    tenant_id = getattr(app, 'tenant_id', None)

    if candidate_user_id:
        _create_notification_safe(
            user_id=candidate_user_id,
            title='Offer Sent',
            body='An offer has been prepared for you. Please review it.',
            notification_type='offer.sent',
            severity=NotificationSeverity.HIGH,
            action_url=f'/offers/{getattr(app, "offer_id", app.id)}',
            related_entity_type='application',
            related_entity_id=_safe_id(app),
            tenant_id=tenant_id,
        )

    _add_system_message_safe(
        tenant_id=tenant_id,
        related_entity_type='application',
        related_entity_id=_safe_id(app),
        body='Offer sent to candidate.',
    )


# ---------------------------------------------------------------------------
# Agency Events
# ---------------------------------------------------------------------------

@receiver(events.agency.candidate_submitted)
def on_agency_candidate_submitted(sender, **kwargs):
    """Notify the client company when an agency submits a candidate."""
    submission = kwargs.get('submission')
    company_recruiter_user_id = kwargs.get('company_recruiter_user_id')
    agency_name = kwargs.get('agency_name', 'Agency')
    candidate_name = kwargs.get('candidate_name', 'candidate')

    if not submission or not company_recruiter_user_id:
        return

    tenant_id = kwargs.get('company_tenant_id') or getattr(submission, 'company_tenant_id', None)

    _create_notification_safe(
        user_id=company_recruiter_user_id,
        title='Agency Candidate Submitted',
        body=f'{agency_name} submitted {candidate_name} for review.',
        notification_type='agency.candidate_submitted',
        severity=NotificationSeverity.MEDIUM,
        action_url=f'/agency-submissions/{_safe_id(submission)}',
        related_entity_type='agency_submission',
        related_entity_id=_safe_id(submission),
        tenant_id=tenant_id,
    )

    _add_system_message_safe(
        tenant_id=tenant_id,
        related_entity_type='agency_submission',
        related_entity_id=_safe_id(submission),
        body=f'{agency_name} submitted candidate {candidate_name}.',
        thread_type='submission_context',
    )


# ---------------------------------------------------------------------------
# Deadline / SLA Events (consumed from automation_sla)
# ---------------------------------------------------------------------------

@receiver(events.application.rejected)
def on_application_rejected(sender, **kwargs):
    app = kwargs.get('application')
    candidate_user_id = kwargs.get('candidate_user_id')
    if not app:
        return

    if candidate_user_id:
        _create_notification_safe(
            user_id=candidate_user_id,
            title='Application Update',
            body='Thank you for applying. Unfortunately, your application was not selected at this time.',
            notification_type='application.rejected',
            severity=NotificationSeverity.MEDIUM,
            action_url=f'/applications/{app.id}',
            related_entity_type='application',
            related_entity_id=_safe_id(app),
            tenant_id=getattr(app, 'tenant_id', None),
        )

    _add_system_message_safe(
        tenant_id=getattr(app, 'tenant_id', None),
        related_entity_type='application',
        related_entity_id=_safe_id(app),
        body='Application rejected.',
    )


@receiver(events.passport.viewed)
def on_passport_viewed(sender, **kwargs):
    """Notify candidate when their passport/profile is viewed by a recruiter."""
    passport = kwargs.get('passport')
    candidate_user_id = kwargs.get('candidate_user_id')
    viewer_name = kwargs.get('viewer_name', 'Someone')
    if not candidate_user_id:
        return

    _create_notification_safe(
        user_id=candidate_user_id,
        title='Profile Viewed',
        body=f'{viewer_name} viewed your Talent Passport.',
        notification_type='passport.viewed',
        severity=NotificationSeverity.INFO,
        action_url='/passport/activity',
        related_entity_type='passport',
        related_entity_id=_safe_id(passport) if passport else None,
        tenant_id=kwargs.get('tenant_id'),
    )


@receiver(events.deadline.overdue)
def on_deadline_overdue(sender, **kwargs):
    """Notify responsible users when a deadline is overdue."""
    owner_user_id = kwargs.get('owner_user_id')
    entity_type = kwargs.get('entity_type', 'task')
    entity_id = kwargs.get('entity_id')
    deadline_label = kwargs.get('deadline_label', 'A deadline')
    tenant_id = kwargs.get('tenant_id')

    if not owner_user_id:
        return

    _create_notification_safe(
        user_id=owner_user_id,
        title='Deadline Overdue',
        body=f'{deadline_label} is overdue.',
        notification_type='deadline.overdue',
        severity=NotificationSeverity.CRITICAL,
        action_url=f'/{entity_type}s/{entity_id}' if entity_id else '',
        related_entity_type=entity_type,
        related_entity_id=entity_id,
        tenant_id=tenant_id,
    )


@receiver(events.interview.cancelled)
def on_interview_cancelled(sender, **kwargs):
    interview = kwargs.get('interview')
    if not interview:
        return

    tenant_id = getattr(interview, 'tenant_id', None)
    candidate_user_id = kwargs.get('candidate_user_id')

    if candidate_user_id:
        _create_notification_safe(
            user_id=candidate_user_id,
            title='Interview Cancelled',
            body='Your scheduled interview has been cancelled. You will be contacted shortly.',
            notification_type='interview.cancelled',
            severity=NotificationSeverity.HIGH,
            action_url=f'/interviews/{interview.id}',
            related_entity_type='interview',
            related_entity_id=_safe_id(interview),
            tenant_id=tenant_id,
        )

    _add_system_message_safe(
        tenant_id=tenant_id,
        related_entity_type='interview',
        related_entity_id=_safe_id(interview),
        body='Interview cancelled.',
        thread_type='interview_coordination',
    )


@receiver(events.interview.rescheduled)
def on_interview_rescheduled(sender, **kwargs):
    interview = kwargs.get('interview')
    if not interview:
        return

    tenant_id = getattr(interview, 'tenant_id', None)
    candidate_user_id = kwargs.get('candidate_user_id')
    interviewer_user_ids = kwargs.get('interviewer_user_ids') or []
    scheduled_at = getattr(interview, 'scheduled_at', None)

    if candidate_user_id:
        _create_notification_safe(
            user_id=candidate_user_id,
            title='Interview Rescheduled',
            body=f'Your interview has been rescheduled{f" to {scheduled_at}" if scheduled_at else ""}. Please check the updated details.',
            notification_type='interview.rescheduled',
            severity=NotificationSeverity.HIGH,
            action_url=f'/interviews/{interview.id}',
            related_entity_type='interview',
            related_entity_id=_safe_id(interview),
            tenant_id=tenant_id,
        )

    for interviewer_id in interviewer_user_ids:
        _create_notification_safe(
            user_id=interviewer_id,
            title='Interview Rescheduled',
            body=f'An interview you are assigned to has been rescheduled{f" to {scheduled_at}" if scheduled_at else ""}.',
            notification_type='interview.rescheduled',
            severity=NotificationSeverity.HIGH,
            action_url=f'/interviews/{interview.id}',
            related_entity_type='interview',
            related_entity_id=_safe_id(interview),
            tenant_id=tenant_id,
        )

    _add_system_message_safe(
        tenant_id=tenant_id,
        related_entity_type='interview',
        related_entity_id=_safe_id(interview),
        body=f'Interview rescheduled{f" to {scheduled_at}" if scheduled_at else ""}.',
        thread_type='interview_coordination',
    )


@receiver(events.interview.feedback_pending)
def on_interview_feedback_pending(sender, **kwargs):
    """
    Notify panelists that feedback is pending.
    Also schedules a recurring reminder job that will keep firing until
    all panelists submit feedback or the interview entity is resolved.
    """
    interview = kwargs.get('interview')
    panelist_user_ids = kwargs.get('panelist_user_ids') or []
    tenant_id = kwargs.get('tenant_id') or (getattr(interview, 'tenant_id', None) if interview else None)
    if not interview or not panelist_user_ids:
        return

    for panelist_id in panelist_user_ids:
        n = _create_notification_safe(
            user_id=panelist_id,
            title='Interview Feedback Required',
            body='Please submit your feedback for the recently completed interview.',
            notification_type='interview.feedback_pending',
            severity=NotificationSeverity.HIGH,
            action_url=f'/interviews/{interview.id}/feedback',
            related_entity_type='interview',
            related_entity_id=_safe_id(interview),
            tenant_id=tenant_id,
        )
        # Schedule reminder chain (every 24h, max 3 reminders)
        if n:
            try:
                from apps.communications.orchestration_tasks import send_notification_reminder
                send_notification_reminder.apply_async(
                    args=[str(n.id)],
                    kwargs={
                        'reminder_key':   'interview_feedback_pending',
                        'max_reminders':  3,
                        'delay_seconds':  86400,  # 24 hours
                    },
                    countdown=86400,
                )
            except Exception as exc:
                logger.warning('Could not schedule feedback reminder: %s', exc)

    _add_system_message_safe(
        tenant_id=tenant_id,
        related_entity_type='interview',
        related_entity_id=_safe_id(interview),
        body='Interview feedback pending from panelists.',
        thread_type='interview_coordination',
    )


# ---------------------------------------------------------------------------
# Offer Events (extended)
# ---------------------------------------------------------------------------

@receiver(events.offer.accepted)
def on_offer_accepted(sender, **kwargs):
    app = kwargs.get('application')
    recruiter_user_id = kwargs.get('recruiter_user_id')
    hiring_manager_user_id = kwargs.get('hiring_manager_user_id')
    if not app:
        return

    tenant_id = getattr(app, 'tenant_id', None)

    for uid in filter(None, [recruiter_user_id, hiring_manager_user_id]):
        _create_notification_safe(
            user_id=uid,
            title='Offer Accepted',
            body='A candidate has accepted their offer. Please proceed with onboarding steps.',
            notification_type='offer.accepted',
            severity=NotificationSeverity.HIGH,
            action_url=f'/applications/{app.id}',
            related_entity_type='application',
            related_entity_id=_safe_id(app),
            tenant_id=tenant_id,
        )

    _add_system_message_safe(
        tenant_id=tenant_id,
        related_entity_type='application',
        related_entity_id=_safe_id(app),
        body='Offer accepted by candidate.',
    )


@receiver(events.offer.response_pending)
def on_offer_response_pending(sender, **kwargs):
    """Reminder to candidate that their offer response is awaited."""
    app = kwargs.get('application')
    candidate_user_id = kwargs.get('candidate_user_id')
    tenant_id = kwargs.get('tenant_id') or (getattr(app, 'tenant_id', None) if app else None)
    if not candidate_user_id or not app:
        return

    n = _create_notification_safe(
        user_id=candidate_user_id,
        title='Offer Response Pending',
        body='Your offer is awaiting a response. Please review and respond at your earliest convenience.',
        notification_type='offer.response_pending',
        severity=NotificationSeverity.HIGH,
        action_url=f'/offers/{app.id}',
        related_entity_type='application',
        related_entity_id=_safe_id(app),
        tenant_id=tenant_id,
    )
    # Schedule reminder chain (every 24h, max 2 reminders)
    if n:
        try:
            from apps.communications.orchestration_tasks import send_notification_reminder
            send_notification_reminder.apply_async(
                args=[str(n.id)],
                kwargs={
                    'reminder_key':   'offer_response_pending',
                    'max_reminders':  2,
                    'delay_seconds':  86400,
                },
                countdown=86400,
            )
        except Exception as exc:
            logger.warning('Could not schedule offer response reminder: %s', exc)


# ---------------------------------------------------------------------------
# Approval Events
# ---------------------------------------------------------------------------

@receiver(events.approval.requested)
def on_approval_requested(sender, **kwargs):
    approver_user_id = kwargs.get('approver_user_id')
    entity_type = kwargs.get('entity_type', 'approval')
    entity_id = kwargs.get('entity_id')
    tenant_id = kwargs.get('tenant_id')
    label = kwargs.get('label', 'An item')
    if not approver_user_id:
        return

    n = _create_notification_safe(
        user_id=approver_user_id,
        title='Approval Required',
        body=f'{label} requires your approval.',
        notification_type='approval.requested',
        severity=NotificationSeverity.HIGH,
        action_url=f'/{entity_type}s/{entity_id}' if entity_id else '/approvals',
        related_entity_type=entity_type,
        related_entity_id=entity_id,
        tenant_id=tenant_id,
    )
    # Schedule an overdue check after 24h
    if n and entity_id:
        try:
            from apps.communications.orchestration_tasks import send_notification_reminder
            send_notification_reminder.apply_async(
                args=[str(n.id)],
                kwargs={
                    'reminder_key':   'approval_pending',
                    'max_reminders':  2,
                    'delay_seconds':  86400,
                },
                countdown=86400,
            )
        except Exception as exc:
            logger.warning('Could not schedule approval reminder: %s', exc)


@receiver(events.approval.overdue)
def on_approval_overdue(sender, **kwargs):
    approver_user_id = kwargs.get('approver_user_id')
    entity_type = kwargs.get('entity_type', 'approval')
    entity_id = kwargs.get('entity_id')
    tenant_id = kwargs.get('tenant_id')
    label = kwargs.get('label', 'An approval item')
    if not approver_user_id:
        return

    _create_notification_safe(
        user_id=approver_user_id,
        title='Approval Overdue',
        body=f'{label} is overdue and requires immediate action.',
        notification_type='approval.overdue',
        severity=NotificationSeverity.CRITICAL,
        action_url=f'/{entity_type}s/{entity_id}' if entity_id else '/approvals',
        related_entity_type=entity_type,
        related_entity_id=entity_id,
        tenant_id=tenant_id,
    )


# ---------------------------------------------------------------------------
# Message / Thread Events
# ---------------------------------------------------------------------------

@receiver(events.message.created)
def on_message_created(sender, **kwargs):
    """Notify recipients of a new in-app message."""
    message = kwargs.get('message')
    thread = kwargs.get('thread')
    sender_user_id = kwargs.get('sender_user_id')
    recipient_user_ids = kwargs.get('recipient_user_ids') or []
    if not recipient_user_ids:
        return

    tenant_id = kwargs.get('tenant_id') or (
        getattr(thread, 'tenant_id', None) if thread else None
    )
    thread_id = _safe_id(thread) if thread else None
    preview = ''
    if message:
        body = getattr(message, 'body', '') or getattr(message, 'content', '') or ''
        preview = body[:120] + ('…' if len(body) > 120 else '')

    for recipient_id in recipient_user_ids:
        if str(recipient_id) == str(sender_user_id):
            continue  # Do not notify the sender
        _create_notification_safe(
            user_id=recipient_id,
            title='New Message',
            body=preview or 'You have a new message.',
            notification_type='message.created',
            severity=NotificationSeverity.MEDIUM,
            action_url=f'/messages/{thread_id}' if thread_id else '/messages',
            related_entity_type='thread',
            related_entity_id=thread_id,
            tenant_id=tenant_id,
        )


@receiver(events.message.high_priority)
def on_high_priority_message(sender, **kwargs):
    """High-priority messages get HIGH severity notifications with faster fallback."""
    message = kwargs.get('message')
    thread = kwargs.get('thread')
    sender_user_id = kwargs.get('sender_user_id')
    recipient_user_ids = kwargs.get('recipient_user_ids') or []
    if not recipient_user_ids:
        return

    tenant_id = kwargs.get('tenant_id') or (
        getattr(thread, 'tenant_id', None) if thread else None
    )
    thread_id = _safe_id(thread) if thread else None
    preview = ''
    if message:
        body = getattr(message, 'body', '') or getattr(message, 'content', '') or ''
        preview = body[:120] + ('…' if len(body) > 120 else '')

    for recipient_id in recipient_user_ids:
        if str(recipient_id) == str(sender_user_id):
            continue
        _create_notification_safe(
            user_id=recipient_id,
            title='[Priority] New Message',
            body=preview or 'You have a high-priority message.',
            notification_type='message.high_priority',
            severity=NotificationSeverity.HIGH,
            action_url=f'/messages/{thread_id}' if thread_id else '/messages',
            related_entity_type='thread',
            related_entity_id=thread_id,
            tenant_id=tenant_id,
        )


@receiver(events.message.thread_read)
def on_thread_read(sender, **kwargs):
    """
    When a thread is marked read, cancel pending fallback/escalation jobs
    for all notifications related to that thread.
    """
    thread = kwargs.get('thread')
    user_id = kwargs.get('user_id')
    if not thread or not user_id:
        return

    thread_id = _safe_id(thread)
    try:
        from apps.communications.notification_orchestration_service import cancel_entity_jobs
        cancel_entity_jobs(
            related_entity_type='thread',
            related_entity_id=thread_id,
            reason='thread_marked_read',
        )
    except Exception as exc:
        logger.warning('Could not cancel thread jobs on thread_read for %s: %s', thread_id, exc)
