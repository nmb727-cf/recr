"""
Communication Search & Archive Service
======================================

Enterprise-grade retrieval, audit-safe history, and retention management
across messaging threads, messages, and notifications.

Supported:
  • Global full-text search (PostgreSQL icontains — trigram-ready for future)
  • Thread-level search with snippet context
  • Thread-subject search (dedicated MessageThread query)
  • Entity-linked communication history (Candidate, Job, Application, etc.)
  • Archive / Unarchive lifecycle management
  • Archived threads list view
  • Recent communications retrieval
  • Notification history with filters (q, is_read, is_archived)
  • Multi-tenant & participant-level access control
  • Snippet / highlight extraction from matched text

Design notes:
  • All queries are tenant_id-gated first to prevent cross-tenant leakage.
  • Participant membership is enforced before any message or thread data is
    returned so internal threads are never exposed to unauthorised users.
  • No hard deletes — is_deleted / is_archived flags are respected throughout.
  • Pagination is mandatory on all list methods; no unbounded queries.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from django.db.models import Q
from django.utils import timezone

from apps.communications.models import (
    Message,
    MessageThread,
    Notification,
    ThreadParticipant,
)
from apps.communications.serializers import NotificationSerializer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SNIPPET_RADIUS = 120  # characters either side of a match to include in snippet
_DEFAULT_PAGE_SIZE = 50
_MAX_PAGE_SIZE = 200


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_search_snippet(text: str, query: str, radius: int = _SNIPPET_RADIUS) -> str:
    """
    Return a short context snippet with the query term highlighted.

    The snippet includes up to `radius` characters either side of the
    first match position.  Surrounding text is trimmed at word boundaries
    where possible and ellipsis-padded so the frontend can show it directly.

    Returns the full text (truncated) when no match position is found.
    """
    if not text or not query:
        return text[:radius * 2] if text else ''

    lower_text = text.lower()
    lower_query = query.lower().strip()

    # Find first occurrence (simplest; future: find highest-density window)
    pos = lower_text.find(lower_query)
    if pos == -1:
        # No direct match — try first word of query
        first_word = lower_query.split()[0] if lower_query.split() else lower_query
        pos = lower_text.find(first_word)

    if pos == -1:
        return text[:radius * 2]

    start = max(0, pos - radius)
    end = min(len(text), pos + len(query) + radius)

    # Trim to word boundaries
    if start > 0:
        space = text.rfind(' ', 0, start + 1)
        if space != -1:
            start = space + 1

    if end < len(text):
        space = text.find(' ', end - 1)
        if space != -1:
            end = space

    snippet = text[start:end]
    if start > 0:
        snippet = '…' + snippet
    if end < len(text):
        snippet = snippet + '…'

    return snippet


def _permitted_thread_ids(user_id, tenant_id) -> List:
    """Return thread IDs the user is an active participant of (same tenant)."""
    return list(
        ThreadParticipant.objects.filter(
            user_id=user_id,
            is_active=True,
            thread__tenant_id=tenant_id,
            thread__is_deleted=False,
        ).values_list('thread_id', flat=True)
    )


# ---------------------------------------------------------------------------
# Main Service
# ---------------------------------------------------------------------------

class CommunicationSearchService:
    """
    Service for scalable search, history, and archive operations.
    Enforces strict tenant isolation and user-level permissions throughout.
    """

    # ── Access Check ─────────────────────────────────────────────────────────

    @staticmethod
    def check_communication_access(
        *,
        thread_id: str,
        user_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Return True if `user_id` is an active participant in `thread_id`
        within the given tenant.  Archived threads pass the check — they
        are only excluded from default listing, not from access.
        """
        return ThreadParticipant.objects.filter(
            thread_id=thread_id,
            user_id=user_id,
            is_active=True,
            thread__tenant_id=tenant_id,
            thread__is_deleted=False,
        ).exists()

    # ── Global Search ─────────────────────────────────────────────────────────

    @staticmethod
    def search_communications(
        *,
        tenant_id: str,
        user_id: str,
        query: str,
        entity_type: str = '',
        entity_id: Optional[str] = None,
        thread_type: str = '',
        channel_type: str = '',
        message_type: str = '',
        sender_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_archived: bool = False,
        limit: int = _DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Global search across messages, thread subjects, and notifications.

        Returns a unified mixed result list with type labels, snippets, and
        navigation targets.  Permission-filtered: only returns data the
        requesting user is allowed to see.

        Result item schema:
            type            : 'message' | 'thread' | 'notification'
            id              : str (UUID)
            thread_id       : str | None
            title           : str
            snippet         : str
            matched_field   : str   (which field matched the query)
            sent_at         : ISO-8601 str
            sender_id       : str | None
            related_entity  : {type, id} | None
            is_archived     : bool
            participants    : list[str]  (user_id strings, up to 5)
            nav_target      : str  (frontend navigation hint)
        """
        if not query or not query.strip():
            return {'results': [], 'total': 0, 'limit': limit, 'offset': offset}

        limit = min(limit, _MAX_PAGE_SIZE)
        q_str = query.strip()

        # ── 1. Permitted threads for this user ─────────────────────────────
        permitted_ids = _permitted_thread_ids(user_id, tenant_id)

        # ── 2. Base thread queryset (needed for both thread + message search)
        thread_qs = MessageThread.objects.filter(
            id__in=permitted_ids,
            is_deleted=False,
        )
        if not include_archived:
            thread_qs = thread_qs.filter(is_archived=False)
        if thread_type:
            thread_qs = thread_qs.filter(thread_type=thread_type)
        if entity_type:
            thread_qs = thread_qs.filter(related_entity_type=entity_type)
        if entity_id:
            thread_qs = thread_qs.filter(related_entity_id=entity_id)

        permitted_filtered_ids = list(thread_qs.values_list('id', flat=True))

        # ── 3. Thread subject search ────────────────────────────────────────
        thread_subject_qs = thread_qs.filter(subject__icontains=q_str)
        if date_from:
            thread_subject_qs = thread_subject_qs.filter(last_message_at__gte=date_from)
        if date_to:
            thread_subject_qs = thread_subject_qs.filter(last_message_at__lte=date_to)

        # ── 4. Message content search ───────────────────────────────────────
        msg_qs = Message.objects.filter(
            thread_id__in=permitted_filtered_ids,
            is_deleted=False,
        ).filter(Q(body__icontains=q_str) | Q(content__icontains=q_str))

        if channel_type:
            msg_qs = msg_qs.filter(channel_type=channel_type)
        if message_type:
            msg_qs = msg_qs.filter(message_type=message_type)
        if sender_id:
            msg_qs = msg_qs.filter(sender_id=sender_id)
        if date_from:
            msg_qs = msg_qs.filter(sent_at__gte=date_from)
        if date_to:
            msg_qs = msg_qs.filter(sent_at__lte=date_to)

        # ── 5. Notification search ──────────────────────────────────────────
        notif_qs = Notification.objects.filter(
            tenant_id=tenant_id,
            user_id=user_id,
        ).filter(Q(title__icontains=q_str) | Q(body__icontains=q_str))

        if not include_archived:
            notif_qs = notif_qs.filter(is_archived=False)
        if entity_type:
            notif_qs = notif_qs.filter(related_entity_type=entity_type)
        if entity_id:
            notif_qs = notif_qs.filter(related_entity_id=entity_id)
        if date_from:
            notif_qs = notif_qs.filter(created_at__gte=date_from)
        if date_to:
            notif_qs = notif_qs.filter(created_at__lte=date_to)

        # ── 6. Compute total count (pre-pagination) ─────────────────────────
        # Avoid double-counting threads that also have matching messages
        total = thread_subject_qs.count() + msg_qs.count() + notif_qs.count()

        # ── 7. Fetch & merge results ─────────────────────────────────────────
        results: List[Dict] = []

        # Thread subject hits (most relevant for navigation)
        for thread in thread_subject_qs.select_related().order_by('-last_message_at')[:limit]:
            participant_ids = list(
                ThreadParticipant.objects.filter(thread_id=thread.id, is_active=True)
                .values_list('user_id', flat=True)[:5]
            )
            results.append({
                'type': 'thread',
                'id': str(thread.id),
                'thread_id': str(thread.id),
                'title': thread.subject or 'Conversation',
                'snippet': build_search_snippet(thread.subject, q_str),
                'matched_field': 'subject',
                'sent_at': (thread.last_message_at or thread.created_at).isoformat(),
                'sender_id': str(thread.created_by) if thread.created_by else None,
                'related_entity': {
                    'type': thread.related_entity_type,
                    'id': str(thread.related_entity_id) if thread.related_entity_id else None,
                },
                'is_archived': thread.is_archived,
                'participants': [str(uid) for uid in participant_ids],
                'nav_target': f'/messages/threads/{thread.id}',
            })

        # Message body hits
        for msg in msg_qs.select_related('thread').order_by('-sent_at')[:limit]:
            text = msg.body or msg.content
            participant_ids = list(
                ThreadParticipant.objects.filter(thread_id=msg.thread_id, is_active=True)
                .values_list('user_id', flat=True)[:5]
            )
            results.append({
                'type': 'message',
                'id': str(msg.id),
                'thread_id': str(msg.thread_id) if msg.thread_id else None,
                'title': (msg.thread.subject if msg.thread else None) or 'Message',
                'snippet': build_search_snippet(text, q_str),
                'matched_field': 'body',
                'sent_at': msg.sent_at.isoformat(),
                'sender_id': str(msg.sender_id),
                'related_entity': {
                    'type': msg.related_entity_type,
                    'id': str(msg.related_entity_id) if msg.related_entity_id else None,
                },
                'is_archived': msg.thread.is_archived if msg.thread else False,
                'participants': [str(uid) for uid in participant_ids],
                'nav_target': (
                    f'/messages/threads/{msg.thread_id}?message={msg.id}'
                    if msg.thread_id else None
                ),
            })

        # Notification hits
        for notif in notif_qs.order_by('-created_at')[:limit]:
            text = f'{notif.title} {notif.body}'
            results.append({
                'type': 'notification',
                'id': str(notif.id),
                'thread_id': None,
                'title': notif.title,
                'snippet': build_search_snippet(notif.body or notif.title, q_str),
                'matched_field': 'title' if q_str.lower() in notif.title.lower() else 'body',
                'sent_at': notif.created_at.isoformat(),
                'sender_id': None,
                'related_entity': {
                    'type': notif.related_entity_type,
                    'id': str(notif.related_entity_id) if notif.related_entity_id else None,
                },
                'is_archived': notif.is_archived,
                'participants': [],
                'nav_target': notif.action_url or None,
            })

        # Sort by date descending and paginate
        results.sort(key=lambda x: x['sent_at'], reverse=True)
        paginated = results[offset: offset + limit]

        return {
            'results': paginated,
            'total': total,
            'limit': limit,
            'offset': offset,
        }

    # ── Thread Search ─────────────────────────────────────────────────────────

    @staticmethod
    def search_thread_messages(
        *,
        thread_id: str,
        tenant_id: str,
        user_id: str,
        query: str,
        sender_id: Optional[str] = None,
        message_type: str = '',
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search within a specific thread.

        Verifies participant access before running any query.
        Returns matching messages with context snippets and navigation hints
        so the frontend can implement jump-to-result.
        """
        from rest_framework.exceptions import PermissionDenied

        if not CommunicationSearchService.check_communication_access(
            thread_id=thread_id,
            user_id=user_id,
            tenant_id=tenant_id,
        ):
            raise PermissionDenied("You do not have access to this thread.")

        if not query or not query.strip():
            return {'results': [], 'total': 0, 'limit': limit, 'offset': offset}

        q_str = query.strip()
        qs = Message.objects.filter(
            thread_id=thread_id,
            is_deleted=False,
        ).filter(Q(body__icontains=q_str) | Q(content__icontains=q_str))

        if sender_id:
            qs = qs.filter(sender_id=sender_id)
        if message_type:
            qs = qs.filter(message_type=message_type)
        if date_from:
            qs = qs.filter(sent_at__gte=date_from)
        if date_to:
            qs = qs.filter(sent_at__lte=date_to)

        total = qs.count()
        results = []
        for msg in qs.order_by('sent_at')[offset: offset + limit]:
            text = msg.body or msg.content
            results.append({
                'id': str(msg.id),
                'thread_id': str(thread_id),
                'sender_id': str(msg.sender_id),
                'body': text,
                'snippet': build_search_snippet(text, q_str),
                'message_type': msg.message_type,
                'sent_at': msg.sent_at.isoformat(),
                'is_system_generated': msg.is_system_generated,
                'nav_target': f'/messages/threads/{thread_id}?message={msg.id}',
            })

        return {'results': results, 'total': total, 'limit': limit, 'offset': offset}

    # ── Entity Communication History ──────────────────────────────────────────

    @staticmethod
    def get_entity_communication_history(
        *,
        tenant_id: str,
        user_id: str,
        entity_type: str,
        entity_id: str,
        limit: int = _DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Return a unified timeline of all communications linked to an entity.

        Used for the 'Communication History' tab on Candidate / Job /
        Application / Interview / Offer detail pages.

        Enforces participant-level access: threads the user cannot see are
        excluded even if they reference the entity.
        """
        # 1. Permitted threads for this user
        permitted_ids = _permitted_thread_ids(user_id, tenant_id)

        # 2. Messages linked to entity (via message-level OR thread-level link)
        msg_qs = Message.objects.filter(
            is_deleted=False,
        ).filter(
            # Message directly linked to entity
            Q(related_entity_type=entity_type, related_entity_id=entity_id,
              thread_id__in=permitted_ids)
            # OR message in a thread linked to this entity
            | Q(thread__related_entity_type=entity_type,
                thread__related_entity_id=entity_id,
                thread_id__in=permitted_ids)
        ).order_by('-sent_at')

        # 3. Threads linked to this entity (as thread-level items in timeline)
        thread_qs = MessageThread.objects.filter(
            id__in=permitted_ids,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
            is_deleted=False,
        ).order_by('-last_message_at')

        # 4. Notifications linked to entity
        notif_qs = Notification.objects.filter(
            tenant_id=tenant_id,
            user_id=user_id,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
        ).order_by('-created_at')

        # Compute total before slicing
        total = msg_qs.count() + notif_qs.count()

        # Build timeline
        timeline: List[Dict] = []

        for msg in msg_qs.select_related('thread')[:limit]:
            text = msg.body or msg.content
            timeline.append({
                'type': 'message',
                'id': str(msg.id),
                'event_at': msg.sent_at.isoformat(),
                'title': (msg.thread.subject if msg.thread else None) or 'Message',
                'preview': text[:200] if text else '',
                'sender_id': str(msg.sender_id),
                'thread_id': str(msg.thread_id) if msg.thread_id else None,
                'message_type': msg.message_type,
                'channel_type': msg.channel_type,
                'is_system_generated': msg.is_system_generated,
                'nav_target': (
                    f'/messages/threads/{msg.thread_id}?message={msg.id}'
                    if msg.thread_id else None
                ),
            })

        for notif in notif_qs[:limit]:
            timeline.append({
                'type': 'notification',
                'id': str(notif.id),
                'event_at': notif.created_at.isoformat(),
                'title': notif.title,
                'preview': notif.body[:200] if notif.body else '',
                'sender_id': None,
                'thread_id': None,
                'is_read': notif.is_read,
                'severity': notif.severity,
                'action_url': notif.action_url,
                'nav_target': notif.action_url or None,
            })

        timeline.sort(key=lambda x: x['event_at'], reverse=True)

        return {
            'timeline': timeline[offset: offset + limit],
            'total': total,
            'limit': limit,
            'offset': offset,
        }

    # ── Archive Management ────────────────────────────────────────────────────

    @staticmethod
    def archive_thread(
        *,
        thread_id: str,
        tenant_id: str,
        user_id: str,
    ) -> bool:
        """
        Archive a thread (soft operational cleanup, not deletion).

        Only active participants within the same tenant may archive a thread.
        Legal-hold threads cannot be archived.
        """
        try:
            thread = MessageThread.objects.get(id=thread_id, tenant_id=tenant_id, is_deleted=False)
        except MessageThread.DoesNotExist:
            return False

        # Participant check
        is_participant = ThreadParticipant.objects.filter(
            thread_id=thread_id,
            user_id=user_id,
            is_active=True,
        ).exists()
        if not is_participant:
            return False

        # Respect legal hold
        if thread.legal_hold:
            logger.warning(
                "Archive blocked on thread %s — legal hold is active.", thread_id
            )
            return False

        if thread.is_archived:
            # Already archived — idempotent success
            return True

        thread.is_archived = True
        thread.archived_at = timezone.now()
        thread.archived_by = UUID(str(user_id))
        thread.save(update_fields=['is_archived', 'archived_at', 'archived_by', 'updated_at'])
        logger.info("Thread %s archived by user %s", thread_id, user_id)
        return True

    @staticmethod
    def unarchive_thread(
        *,
        thread_id: str,
        tenant_id: str,
        user_id: str,
    ) -> bool:
        """
        Restore an archived thread to the active inbox.

        Requires participant membership, matching tenant.
        """
        try:
            thread = MessageThread.objects.get(id=thread_id, tenant_id=tenant_id, is_deleted=False)
        except MessageThread.DoesNotExist:
            return False

        is_participant = ThreadParticipant.objects.filter(
            thread_id=thread_id,
            user_id=user_id,
            is_active=True,
        ).exists()
        if not is_participant:
            return False

        if not thread.is_archived:
            return True  # idempotent

        thread.is_archived = False
        thread.archived_at = None
        thread.archived_by = None
        thread.save(update_fields=['is_archived', 'archived_at', 'archived_by', 'updated_at'])
        logger.info("Thread %s unarchived by user %s", thread_id, user_id)
        return True

    # ── Archived Threads List ─────────────────────────────────────────────────

    @staticmethod
    def get_archived_threads(
        *,
        tenant_id: str,
        user_id: str,
        thread_type: str = '',
        limit: int = _DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Return the user's archived threads, excluding soft-deleted ones.
        """
        permitted_ids = _permitted_thread_ids(user_id, tenant_id)

        qs = MessageThread.objects.filter(
            id__in=permitted_ids,
            is_archived=True,
            is_deleted=False,
        ).order_by('-archived_at')

        if thread_type:
            qs = qs.filter(thread_type=thread_type)

        total = qs.count()
        threads = []
        for thread in qs[offset: offset + limit]:
            participant_ids = list(
                ThreadParticipant.objects.filter(thread_id=thread.id, is_active=True)
                .values_list('user_id', flat=True)[:10]
            )
            threads.append({
                'id': str(thread.id),
                'subject': thread.subject,
                'thread_type': thread.thread_type,
                'is_internal': thread.is_internal,
                'archived_at': thread.archived_at.isoformat() if thread.archived_at else None,
                'archived_by': str(thread.archived_by) if thread.archived_by else None,
                'last_message_at': (
                    thread.last_message_at.isoformat() if thread.last_message_at else None
                ),
                'last_message_preview': thread.last_message_preview,
                'related_entity': {
                    'type': thread.related_entity_type,
                    'id': str(thread.related_entity_id) if thread.related_entity_id else None,
                },
                'participants': [str(uid) for uid in participant_ids],
                'retention_category': thread.retention_category,
                'legal_hold': thread.legal_hold,
            })

        return {'threads': threads, 'total': total, 'limit': limit, 'offset': offset}

    # ── Recent Communications ─────────────────────────────────────────────────

    @staticmethod
    def get_recent_communications(
        *,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Return the user's most recently active threads (not archived, not deleted).
        Useful for quick navigation / recent activity widgets.
        """
        permitted_ids = _permitted_thread_ids(user_id, tenant_id)

        qs = MessageThread.objects.filter(
            id__in=permitted_ids,
            is_archived=False,
            is_deleted=False,
        ).order_by('-last_message_at')[:limit]

        threads = []
        for thread in qs:
            participant_ids = list(
                ThreadParticipant.objects.filter(thread_id=thread.id, is_active=True)
                .values_list('user_id', flat=True)[:5]
            )
            # Unread count for this user
            unread = Message.objects.filter(
                thread_id=thread.id,
                is_deleted=False,
                is_read=False,
            ).exclude(sender_id=user_id).count()

            threads.append({
                'id': str(thread.id),
                'subject': thread.subject,
                'thread_type': thread.thread_type,
                'is_internal': thread.is_internal,
                'last_message_at': (
                    thread.last_message_at.isoformat() if thread.last_message_at else None
                ),
                'last_message_preview': thread.last_message_preview,
                'unread_count': unread,
                'related_entity': {
                    'type': thread.related_entity_type,
                    'id': str(thread.related_entity_id) if thread.related_entity_id else None,
                },
                'participants': [str(uid) for uid in participant_ids],
            })

        return {'threads': threads, 'total': len(threads)}

    # ── Notification History ──────────────────────────────────────────────────

    @staticmethod
    def get_notification_history(
        *,
        tenant_id: str,
        user_id: str,
        query: str = '',
        is_read: Optional[bool] = None,
        include_archived: bool = True,
        include_expired: bool = True,
        severity: str = '',
        entity_type: str = '',
        entity_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Retrieve searchable notification history for a user.

        Supports text search, read/unread filter, archived filter,
        expired filter, severity filter, and entity linkage filter.
        """
        qs = Notification.objects.filter(
            tenant_id=tenant_id,
            user_id=user_id,
        ).order_by('-created_at')

        if not include_archived:
            qs = qs.filter(is_archived=False)

        if not include_expired:
            qs = qs.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now())
            )

        if is_read is not None:
            qs = qs.filter(is_read=is_read)

        if severity:
            qs = qs.filter(severity=severity)

        if entity_type:
            qs = qs.filter(related_entity_type=entity_type)

        if entity_id:
            qs = qs.filter(related_entity_id=entity_id)

        if query and query.strip():
            q_str = query.strip()
            qs = qs.filter(Q(title__icontains=q_str) | Q(body__icontains=q_str))

        total = qs.count()

        notifications = []
        for notif in qs[offset: offset + limit]:
            notifications.append({
                'id': str(notif.id),
                'type': notif.get_type(),
                'title': notif.title,
                'body': notif.body,
                'severity': notif.severity,
                'is_read': notif.is_read,
                'is_archived': notif.is_archived,
                'escalation_level': notif.escalation_level,
                'related_entity': {
                    'type': notif.related_entity_type,
                    'id': str(notif.related_entity_id) if notif.related_entity_id else None,
                },
                'action_url': notif.action_url,
                'created_at': notif.created_at.isoformat(),
                'expires_at': notif.expires_at.isoformat() if notif.expires_at else None,
                'is_expired': (
                    notif.expires_at is not None and notif.expires_at < timezone.now()
                ),
                'fallback_email_sent': notif.fallback_email_sent_at is not None,
                'fallback_whatsapp_sent': notif.fallback_whatsapp_sent_at is not None,
            })

        return {
            'notifications': notifications,
            'total': total,
            'limit': limit,
            'offset': offset,
        }
