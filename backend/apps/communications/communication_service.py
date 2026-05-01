"""
Communication Service Layer
===========================
Reusable thread + messaging service for all modules.

Architecture rule: business modules do NOT call this directly for sending
notifications — they emit events and let the event handlers react.
For explicit thread creation (e.g., interview coordination), this service
may be called directly from views.
"""
import logging
from typing import Optional
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.communications.models import (
    ChannelType,
    Message,
    MessageThread,
    NotificationDelivery,
    ThreadParticipant,
    ThreadType,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thread Service
# ---------------------------------------------------------------------------

class ThreadService:
    """
    Create and manage message threads.
    Handles tenant isolation and explicit participant access.
    """

    @staticmethod
    def create_thread(
        *,
        tenant_id,
        created_by_user_id,
        thread_type: str = ThreadType.GENERAL,
        subject: str = '',
        is_internal: bool = True,
        related_entity_type: str = '',
        related_entity_id=None,
        participant_user_ids: list = None,
        participant_tenant_ids: dict = None,
        metadata: dict = None,
    ) -> MessageThread:
        """
        Create a new thread with explicit participants.

        participant_tenant_ids: {user_id: external_tenant_id} — for cross-tenant participants.
        """
        participant_user_ids = participant_user_ids or []
        participant_tenant_ids = participant_tenant_ids or {}

        with transaction.atomic():
            thread = MessageThread.objects.create(
                tenant_id=tenant_id,
                thread_type=thread_type,
                subject=subject,
                is_internal=is_internal,
                created_by=created_by_user_id,
                related_entity_type=related_entity_type or '',
                related_entity_id=related_entity_id,
                participant_ids=[str(uid) for uid in participant_user_ids],
                metadata=metadata or {},
            )
            # Create explicit participant rows
            ThreadService._ensure_participants(
                thread=thread,
                tenant_id=tenant_id,
                user_ids=participant_user_ids,
                creator_id=created_by_user_id,
                participant_tenant_ids=participant_tenant_ids,
            )

        return thread

    @staticmethod
    def _ensure_participants(*, thread, tenant_id, user_ids, creator_id, participant_tenant_ids):
        for user_id in user_ids:
            external_tid = participant_tenant_ids.get(str(user_id))
            ThreadParticipant.objects.get_or_create(
                thread=thread,
                user_id=user_id,
                defaults=dict(
                    tenant_id=tenant_id,
                    participant_type='owner' if str(user_id) == str(creator_id) else 'member',
                    external_tenant_id=external_tid,
                    is_active=True,
                ),
            )

    @staticmethod
    def add_participant(
        *,
        thread_id,
        requesting_tenant_id,
        user_id,
        participant_type: str = 'member',
        external_tenant_id=None,
    ) -> ThreadParticipant:
        thread = ThreadService._get_thread_for_tenant(thread_id, requesting_tenant_id)
        participant, _ = ThreadParticipant.objects.update_or_create(
            thread=thread,
            user_id=user_id,
            defaults=dict(
                tenant_id=requesting_tenant_id,
                participant_type=participant_type,
                external_tenant_id=external_tenant_id,
                is_active=True,
            ),
        )
        # Keep legacy JSON list in sync
        uid_str = str(user_id)
        ids = thread.participant_ids or []
        if uid_str not in ids:
            ids.append(uid_str)
            thread.participant_ids = ids
            thread.save(update_fields=['participant_ids', 'updated_at'])
        return participant

    @staticmethod
    def get_threads_for_user(
        *,
        tenant_id,
        user_id,
        thread_type: Optional[str] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id=None,
        include_archived: bool = False,
    ):
        """
        Return threads where the user is an active participant.
        Enforces tenant isolation.
        """
        # Get thread IDs for user via participant table (preferred)
        participant_thread_ids = ThreadParticipant.objects.filter(
            user_id=user_id,
            is_active=True,
            thread__tenant_id=tenant_id,
            thread__is_deleted=False,
        ).values_list('thread_id', flat=True)

        qs = MessageThread.objects.filter(
            id__in=participant_thread_ids,
            tenant_id=tenant_id,
            is_deleted=False,
        )
        if not include_archived:
            qs = qs.filter(is_archived=False)
        if thread_type:
            qs = qs.filter(thread_type=thread_type)
        if related_entity_type:
            qs = qs.filter(related_entity_type=related_entity_type)
        if related_entity_id:
            qs = qs.filter(related_entity_id=related_entity_id)
        return qs.order_by('-last_message_at')

    @staticmethod
    def get_thread(*, thread_id, requesting_tenant_id, requesting_user_id):
        """
        Get a thread, ensuring the requesting user is a valid participant.
        Raises PermissionError on cross-tenant or non-participant access.
        """
        thread = ThreadService._get_thread_for_tenant(thread_id, requesting_tenant_id)
        ThreadService._assert_participant(thread, requesting_user_id)
        return thread

    @staticmethod
    def get_messages(*, thread_id, requesting_tenant_id, requesting_user_id, include_deleted=False):
        """Return messages in thread, in chronological order."""
        thread = ThreadService.get_thread(
            thread_id=thread_id,
            requesting_tenant_id=requesting_tenant_id,
            requesting_user_id=requesting_user_id,
        )
        qs = Message.objects.filter(thread=thread)
        if not include_deleted:
            qs = qs.filter(is_deleted=False)
        return qs.order_by('sent_at')

    @staticmethod
    def add_message(
        *,
        thread_id,
        requesting_tenant_id,
        sender_user_id,
        sender_tenant_id=None,
        body: str,
        message_type: str = 'text',
        channel_type: str = ChannelType.IN_APP,
        attachments: list = None,
        related_entity_type: str = '',
        related_entity_id=None,
        is_system_generated: bool = False,
        metadata: dict = None,
    ) -> Message:
        """
        Add a message to a thread. Validates participant access.
        Publishes real-time event after save.
        """
        thread = ThreadService._get_thread_for_tenant(thread_id, requesting_tenant_id)

        if not is_system_generated:
            ThreadService._assert_participant(thread, sender_user_id)

        with transaction.atomic():
            msg = Message.objects.create(
                tenant_id=requesting_tenant_id,
                thread=thread,
                sender_id=sender_user_id,
                sender_tenant_id=sender_tenant_id or requesting_tenant_id,
                message_type=message_type,
                channel_type=channel_type,
                body=body,
                content=body,  # keep legacy field in sync
                attachments_json=attachments or [],
                attachments=attachments or [],
                related_entity_type=related_entity_type or '',
                related_entity_id=related_entity_id,
                is_system_generated=is_system_generated,
                metadata=metadata or {},
            )
            preview = (body or '')[:200]
            thread.last_message_at = msg.sent_at
            thread.last_message_preview = preview
            thread.save(update_fields=['last_message_at', 'last_message_preview', 'updated_at'])

        # Publish real-time event (no-op if channels not installed)
        try:
            from apps.communications.realtime import RealtimePublisher
            RealtimePublisher.publish_message(thread_id=str(thread_id), message_id=str(msg.id))
        except Exception:
            pass

        return msg

    @staticmethod
    def add_system_message(
        *,
        thread_id,
        tenant_id,
        body: str,
        related_entity_type: str = '',
        related_entity_id=None,
        metadata: dict = None,
    ) -> Message:
        """Add a system-generated event message to a thread (no participant check)."""
        return ThreadService.add_message(
            thread_id=thread_id,
            requesting_tenant_id=tenant_id,
            sender_user_id='00000000-0000-0000-0000-000000000000',
            body=body,
            message_type='system_event',
            is_system_generated=True,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            metadata=metadata or {},
        )

    @staticmethod
    def mark_thread_read(*, thread_id, requesting_tenant_id, user_id):
        """Mark all messages in thread as read for this user and update participant.last_read_at."""
        thread = ThreadService._get_thread_for_tenant(thread_id, requesting_tenant_id)
        now = timezone.now()
        Message.objects.filter(
            thread=thread,
            is_deleted=False,
        ).exclude(sender_id=user_id).update(is_read=True, read_at=now)

        ThreadParticipant.objects.filter(
            thread=thread,
            user_id=user_id,
        ).update(last_read_at=now)

        # Broadcast read receipt
        try:
            from apps.communications.realtime import RealtimePublisher
            RealtimePublisher.publish_read_receipt(
                thread_id=str(thread_id),
                user_id=str(user_id),
                last_read_at=now.isoformat()
            )
        except Exception:
            pass

        return True

    @staticmethod
    def get_or_create_context_thread(
        *,
        tenant_id,
        related_entity_type: str,
        related_entity_id,
        thread_type: str = ThreadType.GENERAL,
        subject: str = '',
        created_by_user_id=None,
        participant_user_ids: list = None,
    ) -> tuple:
        """
        Get existing context thread for an entity or create a new one.
        Useful for application timeline, interview coordination, etc.
        Returns (thread, created).
        """
        thread = MessageThread.objects.filter(
            tenant_id=tenant_id,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            thread_type=thread_type,
            is_deleted=False,
        ).first()
        if thread:
            return thread, False

        thread = ThreadService.create_thread(
            tenant_id=tenant_id,
            created_by_user_id=created_by_user_id or '00000000-0000-0000-0000-000000000000',
            thread_type=thread_type,
            subject=subject,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            participant_user_ids=participant_user_ids or [],
        )
        return thread, True

    # ── Private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _get_thread_for_tenant(thread_id, tenant_id) -> MessageThread:
        try:
            return MessageThread.objects.get(
                id=thread_id,
                tenant_id=tenant_id,
                is_deleted=False,
            )
        except MessageThread.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Thread not found.')

    @staticmethod
    def _assert_participant(thread: MessageThread, user_id):
        is_participant = ThreadParticipant.objects.filter(
            thread=thread,
            user_id=user_id,
            is_active=True,
        ).exists()
        if not is_participant:
            # Fallback: check legacy JSON list
            if str(user_id) not in (thread.participant_ids or []):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You are not a participant of this thread.')
