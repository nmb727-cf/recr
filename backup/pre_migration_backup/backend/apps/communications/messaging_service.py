"""
MessagingService — High-Level In-App Messaging Engine
======================================================

Sits above the low-level ThreadService and adds:
  • Notification triggers for every new human message
  • Unread message count aggregation (separate from notification unread count)
  • Automation-accessible system message interface
  • Typed thread factories (internal, external, entity-linked)
  • Participant management with access guards

Architecture rule:
  Business modules (interviews, jobs, candidates, automation) should call
  MessagingService, not ThreadService directly.  ThreadService is the data
  layer; MessagingService is the application layer.

Public API:
  MessagingService.send_message(...)
  MessagingService.send_system_message(...)
  MessagingService.get_unread_count(user_id, tenant_id)
  MessagingService.get_thread_unread_count(thread_id, user_id, tenant_id)
  MessagingService.create_internal_thread(...)
  MessagingService.create_external_thread(...)
  MessagingService.get_or_create_entity_thread(...)
  MessagingService.add_participant(...)
  MessagingService.remove_participant(...)

Automation integration:
  from apps.communications.messaging_service import MessagingService
  MessagingService.send_system_message(
      thread_id=thread_id,
      tenant_id=tenant_id,
      body="Interview scheduled for tomorrow at 3 PM",
      metadata={'event': 'interview.scheduled', 'interview_id': str(interview_id)},
  )
"""
import logging
from typing import Optional
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.communications.communication_service import ThreadService
from apps.communications.models import (
    Message,
    MessageThread,
    ThreadParticipant,
    ThreadType,
)

logger = logging.getLogger(__name__)

# Sentinel UUID for system-generated messages (no real user)
SYSTEM_SENDER_ID = UUID('00000000-0000-0000-0000-000000000000')


class MessagingService:
    """
    High-level messaging engine.
    All methods are static — no instance state.
    """

    # ── Message sending ──────────────────────────────────────────────────────

    @staticmethod
    def send_message(
        *,
        thread_id,
        tenant_id,
        sender_user_id,
        body: str,
        message_type: str = 'text',
        attachments: list = None,
        related_entity_type: str = '',
        related_entity_id=None,
        metadata: dict = None,
        notify_participants: bool = True,
    ) -> Message:
        """
        Send a user message to a thread.

        • Validates participant access (via ThreadService)
        • Persists the message
        • Async-notifies all other participants via Celery task

        Returns the created Message instance.
        """
        msg = ThreadService.add_message(
            thread_id=thread_id,
            requesting_tenant_id=tenant_id,
            sender_user_id=sender_user_id,
            sender_tenant_id=tenant_id,
            body=body,
            message_type=message_type,
            attachments=attachments or [],
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            is_system_generated=False,
            metadata=metadata or {},
        )

        if notify_participants:
            MessagingService._queue_participant_notifications(
                thread_id=thread_id,
                message_id=str(msg.id),
                sender_user_id=str(sender_user_id),
                tenant_id=str(tenant_id),
            )

        return msg

    @staticmethod
    def send_system_message(
        *,
        thread_id,
        tenant_id,
        body: str,
        related_entity_type: str = '',
        related_entity_id=None,
        metadata: dict = None,
        notify_participants: bool = True,
    ) -> Message:
        """
        Post an automation/system event message to a thread.

        No participant check — system messages can always be posted.
        Intended for automation engine, event handlers, and background tasks.

        Example:
            MessagingService.send_system_message(
                thread_id=thread_id,
                tenant_id=tenant_id,
                body="Interview scheduled: Friday 9 AM with John Smith",
                metadata={'event': 'interview.scheduled', 'interview_id': str(iid)},
            )
        """
        msg = ThreadService.add_system_message(
            thread_id=thread_id,
            tenant_id=tenant_id,
            body=body,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            metadata=metadata or {},
        )

        if notify_participants:
            MessagingService._queue_participant_notifications(
                thread_id=thread_id,
                message_id=str(msg.id),
                sender_user_id=str(SYSTEM_SENDER_ID),
                tenant_id=str(tenant_id),
                is_system=True,
            )

        return msg

    # ── Unread tracking ──────────────────────────────────────────────────────

    @staticmethod
    def get_unread_count(*, user_id, tenant_id) -> int:
        """
        Total number of unread messages across all threads the user participates in.

        This is the messaging unread count — separate from notification unread count.
        Used by the UI badge on the messaging icon.
        """
        participant_thread_ids = ThreadParticipant.objects.filter(
            user_id=user_id,
            is_active=True,
            thread__tenant_id=tenant_id,
            thread__is_deleted=False,
        ).values_list('thread_id', flat=True)

        return Message.objects.filter(
            thread_id__in=participant_thread_ids,
            is_deleted=False,
            is_read=False,
            is_system_generated=False,
        ).exclude(sender_id=user_id).count()

    @staticmethod
    def mark_thread_read(*, thread_id, tenant_id, user_id) -> bool:
        """
        Mark all messages in a thread as read for the current user.
        Updates the participant's last_read_at timestamp.
        """
        return ThreadService.mark_thread_read(
            thread_id=thread_id,
            requesting_tenant_id=tenant_id,
            user_id=user_id,
        )

    @staticmethod
    def get_thread_unread_count(*, thread_id, user_id, tenant_id) -> int:
        """Unread message count for a specific thread."""
        try:
            thread = MessageThread.objects.get(
                id=thread_id,
                tenant_id=tenant_id,
                is_deleted=False,
            )
        except MessageThread.DoesNotExist:
            return 0

        return Message.objects.filter(
            thread=thread,
            is_deleted=False,
            is_read=False,
        ).exclude(sender_id=user_id).count()

    # ── Thread factories ─────────────────────────────────────────────────────

    @staticmethod
    def create_internal_thread(
        *,
        tenant_id,
        created_by_user_id,
        subject: str = '',
        participant_user_ids: list = None,
        related_entity_type: str = '',
        related_entity_id=None,
        metadata: dict = None,
    ) -> MessageThread:
        """
        Create an internal team thread (recruiter ↔ hiring manager, etc.)

        Internal threads are only visible to the creating tenant's users.
        """
        return ThreadService.create_thread(
            tenant_id=tenant_id,
            created_by_user_id=created_by_user_id,
            thread_type=ThreadType.INTERNAL,
            subject=subject,
            is_internal=True,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            participant_user_ids=participant_user_ids or [],
            metadata=metadata or {},
        )

    @staticmethod
    def create_external_thread(
        *,
        tenant_id,
        created_by_user_id,
        thread_type: str,
        subject: str = '',
        participant_user_ids: list = None,
        participant_tenant_ids: dict = None,
        related_entity_type: str = '',
        related_entity_id=None,
        metadata: dict = None,
    ) -> MessageThread:
        """
        Create an external / cross-party thread.

        thread_type must be one of:
          'company_agency'        — Company ↔ Agency
          'recruiter_candidate'   — Recruiter ↔ Candidate
          'company_candidate'     — Company ↔ Candidate (direct)
          'agency_candidate'      — Agency ↔ Candidate
          'interview_coordination'
          'submission_context'

        participant_tenant_ids: {str(user_id): external_tenant_uuid}
            Pass this for cross-tenant participants so that their external_tenant_id
            is stored correctly on ThreadParticipant.
        """
        valid_external_types = {
            ThreadType.COMPANY_AGENCY,
            ThreadType.RECRUITER_CANDIDATE,
            ThreadType.COMPANY_CANDIDATE,
            ThreadType.AGENCY_CANDIDATE,
            ThreadType.INTERVIEW_COORDINATION,
            ThreadType.SUBMISSION_CONTEXT,
        }
        if thread_type not in valid_external_types:
            raise ValueError(
                f'thread_type must be one of {valid_external_types}; got {thread_type!r}'
            )
        return ThreadService.create_thread(
            tenant_id=tenant_id,
            created_by_user_id=created_by_user_id,
            thread_type=thread_type,
            subject=subject,
            is_internal=False,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            participant_user_ids=participant_user_ids or [],
            participant_tenant_ids=participant_tenant_ids or {},
            metadata=metadata or {},
        )

    @staticmethod
    def get_or_create_entity_thread(
        *,
        tenant_id,
        entity_type: str,
        entity_id,
        thread_type: str = ThreadType.GENERAL,
        subject: str = '',
        created_by_user_id=None,
        participant_user_ids: list = None,
    ) -> tuple:
        """
        Get the existing thread for an entity or create a new one.

        Returns (thread, created: bool).

        Useful for:
          - Candidate profile discussion thread
          - Job hiring thread
          - Interview coordination thread
          - Offer negotiation thread

        Example:
            thread, created = MessagingService.get_or_create_entity_thread(
                tenant_id=tenant_id,
                entity_type='candidate',
                entity_id=candidate_id,
                thread_type='recruiter_candidate',
                subject='Discussion: Jane Doe',
                participant_user_ids=[recruiter_id, hiring_manager_id],
            )
        """
        return ThreadService.get_or_create_context_thread(
            tenant_id=tenant_id,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
            thread_type=thread_type,
            subject=subject,
            created_by_user_id=created_by_user_id,
            participant_user_ids=participant_user_ids or [],
        )

    # ── Participant management ───────────────────────────────────────────────

    @staticmethod
    def add_participant(
        *,
        thread_id,
        tenant_id,
        requesting_user_id,
        new_user_id,
        participant_type: str = 'member',
        external_tenant_id=None,
    ) -> ThreadParticipant:
        """
        Add a user to an existing thread.

        The requesting user must already be a participant (owner or member).
        External participants can be added for cross-tenant threads.
        """
        # Verify requesting user is a participant
        is_participant = ThreadParticipant.objects.filter(
            thread_id=thread_id,
            user_id=requesting_user_id,
            is_active=True,
        ).exists()
        if not is_participant:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only existing participants can add new participants.')

        return ThreadService.add_participant(
            thread_id=thread_id,
            requesting_tenant_id=tenant_id,
            user_id=new_user_id,
            participant_type=participant_type,
            external_tenant_id=external_tenant_id,
        )

    @staticmethod
    def remove_participant(
        *,
        participant_id,
        tenant_id,
        requesting_user_id,
    ) -> bool:
        """
        Remove (deactivate) a participant from a thread.

        Rules:
          • A user can remove themselves (leave thread)
          • Thread owner can remove any participant
          • Other members cannot remove others
        """
        try:
            participant = ThreadParticipant.objects.select_related('thread').get(
                id=participant_id,
                tenant_id=tenant_id,
            )
        except ThreadParticipant.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Participant not found.')

        is_self = str(participant.user_id) == str(requesting_user_id)
        is_owner = ThreadParticipant.objects.filter(
            thread=participant.thread,
            user_id=requesting_user_id,
            participant_type='owner',
            is_active=True,
        ).exists()

        if not is_self and not is_owner:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only the thread owner or the participant themselves can remove a participant.')

        participant.is_active = False
        participant.save(update_fields=['is_active'])

        # Keep legacy JSON in sync
        thread = participant.thread
        uid_str = str(participant.user_id)
        ids = [i for i in (thread.participant_ids or []) if i != uid_str]
        thread.participant_ids = ids
        thread.save(update_fields=['participant_ids', 'updated_at'])

        return True

    # ── Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _queue_participant_notifications(
        *,
        thread_id,
        message_id: str,
        sender_user_id: str,
        tenant_id: str,
        is_system: bool = False,
    ):
        """Queue async notifications to all thread participants except the sender."""
        try:
            from apps.communications.messaging_tasks import notify_message_participants_task
            notify_message_participants_task.apply_async(
                kwargs={
                    'thread_id': str(thread_id),
                    'message_id': message_id,
                    'sender_user_id': sender_user_id,
                    'tenant_id': tenant_id,
                    'is_system': is_system,
                },
                countdown=0,
            )
        except Exception as exc:
            # Task queuing failure must never crash message delivery
            logger.warning('MessagingService: failed to queue participant notifications: %s', exc)
