"""
Messaging Engine — Additional API Views
========================================

Supplements the existing thread/message views in views.py with:
  • Participant management (add / remove)
  • Per-user unread message count
  • Entity-linked thread lookup

All views enforce multi-tenant isolation via the requesting user's tenant_id.

New routes added to urls.py:
  GET  /messages/unread-count/
  GET  /messages/threads/entity/
  POST /messages/threads/<pk>/participants/
  DELETE /messages/participants/<participant_id>/
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.communications.messaging_service import MessagingService
from apps.communications.models import ThreadParticipant
from apps.communications.serializers import ThreadParticipantSerializer, MessageThreadSerializer
from apps.core.responses import success_response, error_response

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Unread message count
# ---------------------------------------------------------------------------

class MessagingUnreadCountView(APIView):
    """
    GET /api/v1/messages/unread-count/

    Returns the number of unread messages across all threads the current
    user participates in.  This is separate from the notification unread
    count (which tracks in-app notifications, not thread messages).

    Response:
        {"unread_message_count": 7}
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = MessagingService.get_unread_count(
            user_id=request.user.id,
            tenant_id=request.user.tenant_id,
        )
        return success_response(
            data={'unread_message_count': count},
            message='Unread message count retrieved.',
        )


# ---------------------------------------------------------------------------
# Entity-linked thread lookup
# ---------------------------------------------------------------------------

class EntityThreadView(APIView):
    """
    GET /api/v1/messages/threads/entity/
        ?entity_type=candidate&entity_id=<uuid>
        &thread_type=recruiter_candidate   (optional)

    Returns the thread(s) linked to a specific entity.  Used by entity
    detail pages (candidate, job, interview, offer) to load the
    contextual conversation.

    Creates the thread if it does not yet exist when `?create=true` is
    passed and participant_user_ids is provided in the POST body.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entity_type = request.query_params.get('entity_type', '')
        entity_id = request.query_params.get('entity_id')
        thread_type = request.query_params.get('thread_type')

        if not entity_type or not entity_id:
            return error_response('entity_type and entity_id are required.')

        from apps.communications.models import MessageThread
        qs = MessageThread.objects.filter(
            tenant_id=request.user.tenant_id,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
            is_deleted=False,
        )
        if thread_type:
            qs = qs.filter(thread_type=thread_type)
        qs = qs.order_by('-last_message_at')

        serializer = MessageThreadSerializer(qs, many=True, context={'request': request})
        return success_response(
            data={'threads': serializer.data},
            message='Entity threads retrieved.',
            meta={'total': qs.count()},
        )

    def post(self, request):
        """
        POST /api/v1/messages/threads/entity/

        Get or create a thread for an entity.

        Body:
            entity_type, entity_id, thread_type, subject (optional),
            participant_user_ids (optional)
        """
        entity_type = request.data.get('entity_type', '')
        entity_id = request.data.get('entity_id')
        thread_type = request.data.get('thread_type', 'general')
        subject = request.data.get('subject', '')
        participant_ids = request.data.get('participant_user_ids', [])

        if not entity_type or not entity_id:
            return error_response('entity_type and entity_id are required.')

        # Always include the requesting user
        uid = str(request.user.id)
        if uid not in [str(p) for p in participant_ids]:
            participant_ids = [uid] + list(participant_ids)

        try:
            thread, created = MessagingService.get_or_create_entity_thread(
                tenant_id=request.user.tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                thread_type=thread_type,
                subject=subject,
                created_by_user_id=request.user.id,
                participant_user_ids=participant_ids,
            )
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)

        return success_response(
            data={
                'thread': MessageThreadSerializer(thread, context={'request': request}).data,
                'created': created,
            },
            message='Thread retrieved.' if not created else 'Thread created.',
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Participant management
# ---------------------------------------------------------------------------

class ThreadParticipantAddView(APIView):
    """
    POST /api/v1/messages/threads/<pk>/participants/

    Add a participant to an existing thread.

    Body:
        user_id:              UUID of the user to add
        participant_type:     'member' | 'observer' (default: member)
        external_tenant_id:   UUID of the external tenant (for cross-tenant threads)

    Permission: only existing active participants may add others.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user_id = request.data.get('user_id')
        if not user_id:
            return error_response('user_id is required.')

        participant_type = request.data.get('participant_type', 'member')
        if participant_type not in ('member', 'observer', 'owner'):
            return error_response('participant_type must be member, observer, or owner.')

        external_tenant_id = request.data.get('external_tenant_id')

        try:
            participant = MessagingService.add_participant(
                thread_id=pk,
                tenant_id=request.user.tenant_id,
                requesting_user_id=request.user.id,
                new_user_id=user_id,
                participant_type=participant_type,
                external_tenant_id=external_tenant_id,
            )
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_403_FORBIDDEN)

        return success_response(
            data={'participant': ThreadParticipantSerializer(participant).data},
            message='Participant added.',
            status_code=status.HTTP_201_CREATED,
        )


class ThreadParticipantRemoveView(APIView):
    """
    DELETE /api/v1/messages/participants/<participant_id>/

    Remove a participant from a thread.

    Permission:
      • The participant may remove themselves (leave thread)
      • Thread owner may remove any participant
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, participant_id):
        try:
            MessagingService.remove_participant(
                participant_id=participant_id,
                tenant_id=request.user.tenant_id,
                requesting_user_id=request.user.id,
            )
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_403_FORBIDDEN)

        return success_response(
            message='Participant removed.',
            status_code=status.HTTP_204_NO_CONTENT,
        )
