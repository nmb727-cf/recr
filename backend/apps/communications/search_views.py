"""
Communication Search & Archive API Views
========================================

Endpoints for global search, thread search, history retrieval,
archive management, and recent communications.

All views:
  • Require authentication
  • Gate on tenant_id from request.user
  • Use service layer for business logic — no raw queries here
  • Return project-standard success_response / error_response envelopes
"""
import logging
from uuid import UUID

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.communications.search_service import CommunicationSearchService
from apps.core.responses import success_response, error_response

logger = logging.getLogger(__name__)


def _parse_uuid(value: str):
    """Return UUID if valid string, else None."""
    if not value:
        return None
    try:
        return str(UUID(value))
    except (ValueError, AttributeError):
        return None


def _parse_bool(value: str) -> bool:
    return str(value).lower() in ('true', '1', 'yes')


# ---------------------------------------------------------------------------
# Global Communication Search
# ---------------------------------------------------------------------------

class GlobalCommunicationSearchView(APIView):
    """
    GET /api/v1/communications/search/

    Query params:
        q             (required) — search term
        entity_type   — filter by related entity type (e.g. 'candidate', 'job')
        entity_id     — filter by related entity UUID
        thread_type   — filter by thread type (internal, company_agency, …)
        channel_type  — filter by channel (in_app, email, whatsapp, sms)
        message_type  — filter by message type (text, system_event, …)
        sender_id     — filter by sender UUID
        date_from     — ISO-8601 datetime lower bound
        date_to       — ISO-8601 datetime upper bound
        archived      — include archived threads/notifications (default: false)
        limit         — page size (default 50, max 200)
        offset        — pagination offset (default 0)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return error_response(
                "Search query 'q' is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            limit = max(1, min(int(request.query_params.get('limit', 50)), 200))
            offset = max(0, int(request.query_params.get('offset', 0)))
        except (ValueError, TypeError):
            return error_response("'limit' and 'offset' must be integers.")

        results = CommunicationSearchService.search_communications(
            tenant_id=str(request.user.tenant_id),
            user_id=str(request.user.id),
            query=query,
            entity_type=request.query_params.get('entity_type', ''),
            entity_id=_parse_uuid(request.query_params.get('entity_id')),
            thread_type=request.query_params.get('thread_type', ''),
            channel_type=request.query_params.get('channel_type', ''),
            message_type=request.query_params.get('message_type', ''),
            sender_id=_parse_uuid(request.query_params.get('sender_id')),
            date_from=request.query_params.get('date_from'),
            date_to=request.query_params.get('date_to'),
            include_archived=_parse_bool(request.query_params.get('archived', 'false')),
            limit=limit,
            offset=offset,
        )
        return success_response(
            data=results,
            message="Communication search completed.",
        )


# ---------------------------------------------------------------------------
# Thread-level Search
# ---------------------------------------------------------------------------

class ThreadMessageSearchView(APIView):
    """
    GET /api/v1/messages/threads/{pk}/search/

    Query params:
        q            (required) — search term
        sender_id    — filter by sender UUID
        message_type — filter by message type
        date_from    — ISO-8601 lower bound
        date_to      — ISO-8601 upper bound
        limit        — default 100
        offset       — default 0
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        query = request.query_params.get('q', '').strip()
        if not query:
            return error_response(
                "Search query 'q' is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            limit = max(1, min(int(request.query_params.get('limit', 100)), 200))
            offset = max(0, int(request.query_params.get('offset', 0)))
        except (ValueError, TypeError):
            return error_response("'limit' and 'offset' must be integers.")

        try:
            results = CommunicationSearchService.search_thread_messages(
                thread_id=str(pk),
                tenant_id=str(request.user.tenant_id),
                user_id=str(request.user.id),
                query=query,
                sender_id=_parse_uuid(request.query_params.get('sender_id')),
                message_type=request.query_params.get('message_type', ''),
                date_from=request.query_params.get('date_from'),
                date_to=request.query_params.get('date_to'),
                limit=limit,
                offset=offset,
            )
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_403_FORBIDDEN)

        return success_response(
            data=results,
            message="Thread search completed.",
        )


# ---------------------------------------------------------------------------
# Archive / Unarchive
# ---------------------------------------------------------------------------

class ArchiveThreadView(APIView):
    """POST /api/v1/messages/threads/{pk}/archive/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        success = CommunicationSearchService.archive_thread(
            thread_id=str(pk),
            tenant_id=str(request.user.tenant_id),
            user_id=str(request.user.id),
        )
        if not success:
            return error_response(
                "Thread not found, you are not a participant, "
                "or the thread is under legal hold.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(message="Thread archived successfully.")


class UnarchiveThreadView(APIView):
    """POST /api/v1/messages/threads/{pk}/unarchive/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        success = CommunicationSearchService.unarchive_thread(
            thread_id=str(pk),
            tenant_id=str(request.user.tenant_id),
            user_id=str(request.user.id),
        )
        if not success:
            return error_response(
                "Thread not found or you are not a participant.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(message="Thread unarchived successfully.")


# ---------------------------------------------------------------------------
# Archived Threads List
# ---------------------------------------------------------------------------

class ArchivedThreadListView(APIView):
    """
    GET /api/v1/messages/archived/

    Query params:
        thread_type — optional filter
        limit       — default 50
        offset      — default 0
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = max(1, min(int(request.query_params.get('limit', 50)), 200))
            offset = max(0, int(request.query_params.get('offset', 0)))
        except (ValueError, TypeError):
            return error_response("'limit' and 'offset' must be integers.")

        results = CommunicationSearchService.get_archived_threads(
            tenant_id=str(request.user.tenant_id),
            user_id=str(request.user.id),
            thread_type=request.query_params.get('thread_type', ''),
            limit=limit,
            offset=offset,
        )
        return success_response(
            data=results,
            message="Archived threads retrieved.",
        )


# ---------------------------------------------------------------------------
# Entity Communication History
# ---------------------------------------------------------------------------

class EntityCommunicationHistoryView(APIView):
    """
    GET /api/v1/communications/history/{entity_type}/{entity_id}/

    Query params:
        limit  — default 50
        offset — default 0
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, entity_type, entity_id):
        try:
            limit = max(1, min(int(request.query_params.get('limit', 50)), 200))
            offset = max(0, int(request.query_params.get('offset', 0)))
        except (ValueError, TypeError):
            return error_response("'limit' and 'offset' must be integers.")

        results = CommunicationSearchService.get_entity_communication_history(
            tenant_id=str(request.user.tenant_id),
            user_id=str(request.user.id),
            entity_type=entity_type,
            entity_id=str(entity_id),
            limit=limit,
            offset=offset,
        )
        return success_response(
            data=results,
            message="Entity communication history retrieved.",
        )


# ---------------------------------------------------------------------------
# Recent Communications
# ---------------------------------------------------------------------------

class RecentCommunicationsView(APIView):
    """
    GET /api/v1/communications/recent/

    Returns the most recently active threads for quick navigation.

    Query params:
        limit — default 20, max 50
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = max(1, min(int(request.query_params.get('limit', 20)), 50))
        except (ValueError, TypeError):
            limit = 20

        results = CommunicationSearchService.get_recent_communications(
            tenant_id=str(request.user.tenant_id),
            user_id=str(request.user.id),
            limit=limit,
        )
        return success_response(
            data=results,
            message="Recent communications retrieved.",
        )


# ---------------------------------------------------------------------------
# Notification History
# ---------------------------------------------------------------------------

class NotificationHistoryView(APIView):
    """
    GET /api/v1/notifications/history/

    Query params:
        q                — search term (title / body)
        is_read          — true | false | (omit = all)
        include_archived — default true
        include_expired  — default true
        severity         — info | medium | high | critical
        entity_type      — filter by related entity type
        entity_id        — filter by related entity UUID
        limit            — default 100
        offset           — default 0
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = max(1, min(int(request.query_params.get('limit', 100)), 200))
            offset = max(0, int(request.query_params.get('offset', 0)))
        except (ValueError, TypeError):
            return error_response("'limit' and 'offset' must be integers.")

        # is_read: only parse when explicitly provided
        is_read = None
        if 'is_read' in request.query_params:
            is_read = _parse_bool(request.query_params['is_read'])

        results = CommunicationSearchService.get_notification_history(
            tenant_id=str(request.user.tenant_id),
            user_id=str(request.user.id),
            query=request.query_params.get('q', ''),
            is_read=is_read,
            include_archived=_parse_bool(
                request.query_params.get('include_archived', 'true')
            ),
            include_expired=_parse_bool(
                request.query_params.get('include_expired', 'true')
            ),
            severity=request.query_params.get('severity', ''),
            entity_type=request.query_params.get('entity_type', ''),
            entity_id=_parse_uuid(request.query_params.get('entity_id')),
            limit=limit,
            offset=offset,
        )
        return success_response(
            data=results,
            message="Notification history retrieved.",
        )
