"""
Messaging Engine — Celery Tasks
================================

Tasks for async notification delivery, message fallback, and system
message dispatch.

Task names (for monitoring/routing):
  communications.messaging.notify_participants
  communications.messaging.message_fallback_email
  communications.messaging.send_automation_system_message

All tasks are idempotent and safe to retry.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# notify_message_participants_task
# ---------------------------------------------------------------------------

@shared_task(
    name='communications.messaging.notify_participants',
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def notify_message_participants_task(
    self,
    *,
    thread_id: str,
    message_id: str,
    sender_user_id: str,
    tenant_id: str,
    is_system: bool = False,
):
    """
    Send in-app notifications to all active thread participants,
    excluding the message sender.

    If the message is a system event, the title is formatted accordingly
    so participants know it is an automated notification rather than a
    personal message.

    After creating in-app notifications this task also schedules a
    fallback email via the notification orchestration engine — so if the
    user does not open the notification after the configured fallback
    delay, an email is sent automatically.
    """
    try:
        from apps.communications.models import (
            Message,
            MessageThread,
            ThreadParticipant,
        )
        from apps.communications.notification_service import NotificationService

        # Load message and thread
        try:
            message = Message.objects.get(id=message_id)
            thread = MessageThread.objects.get(id=thread_id, tenant_id=tenant_id)
        except (Message.DoesNotExist, MessageThread.DoesNotExist) as exc:
            logger.warning('notify_participants: message or thread not found — %s', exc)
            return

        # Load active participants (excluding sender)
        participants = ThreadParticipant.objects.filter(
            thread=thread,
            is_active=True,
        ).exclude(user_id=sender_user_id)

        if not participants.exists():
            return

        # Build notification content
        body_preview = (message.body or message.content or '')[:200]
        if is_system:
            title = f'System update: {body_preview[:80]}'
            notification_type = 'messaging.system_event'
        else:
            thread_subject = thread.subject or 'New message'
            title = f'New message: {thread_subject}'
            notification_type = 'messaging.new_message'

        action_url = f'/communications?thread={thread_id}'

        # Create notification for each participant
        for participant in participants:
            try:
                NotificationService.create_notification(
                    tenant_id=tenant_id,
                    user_id=str(participant.user_id),
                    title=title,
                    body=body_preview,
                    notification_type=notification_type,
                    action_url=action_url,
                    related_entity_type='message_thread',
                    related_entity_id=thread_id,
                    metadata={
                        'thread_id': thread_id,
                        'message_id': message_id,
                        'sender_user_id': sender_user_id,
                        'thread_type': thread.thread_type,
                        'is_system': is_system,
                    },
                )
            except Exception as exc:
                logger.warning(
                    'notify_participants: failed to notify user %s: %s',
                    participant.user_id, exc,
                )

        # Schedule fallback email if message is unread after delay
        fallback_delay_seconds = 2400  # 40 minutes (medium priority default)
        for participant in participants:
            if not participant.is_muted:
                message_fallback_email_task.apply_async(
                    kwargs={
                        'thread_id': thread_id,
                        'message_id': message_id,
                        'recipient_user_id': str(participant.user_id),
                        'tenant_id': tenant_id,
                    },
                    countdown=fallback_delay_seconds,
                )

    except Exception as exc:
        logger.error('notify_participants task error: %s', exc, exc_info=True)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# message_fallback_email_task
# ---------------------------------------------------------------------------

@shared_task(
    name='communications.messaging.message_fallback_email',
    bind=True,
    max_retries=1,
    acks_late=True,
)
def message_fallback_email_task(
    self,
    *,
    thread_id: str,
    message_id: str,
    recipient_user_id: str,
    tenant_id: str,
):
    """
    Send a fallback email if the message has not been read after the delay.

    Checks:
      1. The message still exists and is not deleted.
      2. The recipient has NOT read it yet (last_read_at < message.sent_at).
      3. No duplicate fallback email has been sent already.

    If all checks pass, queues an email via the email delivery engine.
    """
    try:
        from apps.communications.models import Message, ThreadParticipant

        # Check message is still unread by recipient
        try:
            message = Message.objects.get(id=message_id, is_deleted=False)
        except Message.DoesNotExist:
            return  # Message deleted, skip

        participant = ThreadParticipant.objects.filter(
            thread_id=thread_id,
            user_id=recipient_user_id,
            is_active=True,
        ).first()

        if not participant:
            return  # Participant removed

        # If participant read after this message was sent, skip
        if participant.last_read_at and participant.last_read_at >= message.sent_at:
            logger.debug(
                'message_fallback_email: user %s already read thread, skipping',
                recipient_user_id,
            )
            return

        # Check if we already sent a fallback (stored in message metadata)
        fallback_key = f'fallback_email_sent_to_{recipient_user_id}'
        if message.metadata.get(fallback_key):
            return

        # Load recipient user
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=recipient_user_id)
        except Exception:
            return

        if not user.email:
            return

        # Build email body
        from apps.communications.models import MessageThread
        try:
            thread = MessageThread.objects.get(id=thread_id)
        except MessageThread.DoesNotExist:
            return

        body_preview = (message.body or message.content or '')[:500]
        subject = f'Unread message: {thread.subject or "New message in Talentos"}'
        body_text = (
            f'You have an unread message in Talentos.\n\n'
            f'{body_preview}\n\n'
            f'Reply by logging in at: /communications?thread={thread_id}'
        )
        body_html = (
            f'<p>You have an unread message in Talentos.</p>'
            f'<blockquote>{body_preview}</blockquote>'
            f'<p><a href="/communications?thread={thread_id}">View message</a></p>'
        )

        # Queue via email dispatch engine
        try:
            from apps.communications.email_dispatch.dispatch import EmailDispatchService
            from apps.communications.email_dispatch.types import EmailSendRequest
            request = EmailSendRequest(
                tenant_id=str(tenant_id),
                actor_user_id=None,
                email_type='system',
                message_purpose='messaging_fallback',
                recipients=[user.email],
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                allow_fallback=True,
                trigger_source='messaging_engine',
                metadata={
                    'thread_id': thread_id,
                    'message_id': message_id,
                    'fallback_for': recipient_user_id,
                },
            )
            EmailDispatchService.queue_send(request)

            # Mark as sent to prevent duplicate
            message.metadata[fallback_key] = timezone.now().isoformat()
            message.save(update_fields=['metadata'])

            logger.info(
                'message_fallback_email: queued fallback for user=%s thread=%s',
                recipient_user_id, thread_id,
            )
        except Exception as exc:
            logger.warning('message_fallback_email: email queue failed: %s', exc)

    except Exception as exc:
        logger.error('message_fallback_email task error: %s', exc, exc_info=True)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# send_automation_system_message_task
# ---------------------------------------------------------------------------

@shared_task(
    name='communications.messaging.send_automation_system_message',
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    acks_late=True,
)
def send_automation_system_message_task(
    self,
    *,
    thread_id: str,
    tenant_id: str,
    body: str,
    related_entity_type: str = '',
    related_entity_id: str = None,
    metadata: dict = None,
    notify_participants: bool = True,
):
    """
    Celery-async variant of MessagingService.send_system_message().

    Used by automation engine when a system message must be sent
    asynchronously (e.g. after a pipeline stage change, offer approval, etc.)

    Example usage from automation:
        send_automation_system_message_task.apply_async(kwargs={
            'thread_id': str(thread_id),
            'tenant_id': str(tenant_id),
            'body': 'Candidate shortlisted: moved to Technical Interview stage',
            'related_entity_type': 'application',
            'related_entity_id': str(application_id),
            'metadata': {'event': 'application.stage_changed', 'stage': 'technical_interview'},
        })
    """
    try:
        from apps.communications.messaging_service import MessagingService
        MessagingService.send_system_message(
            thread_id=thread_id,
            tenant_id=tenant_id,
            body=body,
            related_entity_type=related_entity_type or '',
            related_entity_id=related_entity_id,
            metadata=metadata or {},
            notify_participants=notify_participants,
        )
        logger.info(
            'send_automation_system_message: posted to thread=%s body=%.60r',
            thread_id, body,
        )
    except Exception as exc:
        logger.error('send_automation_system_message task error: %s', exc, exc_info=True)
        raise self.retry(exc=exc)
