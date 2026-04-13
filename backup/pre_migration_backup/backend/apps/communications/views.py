from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.communications.models import MessageThread, Message, Notification, EmailTemplate, EmailAccount
from apps.communications.serializers import (
    MessageThreadSerializer, MessageThreadCreateSerializer,
    MessageSerializer, NotificationSerializer,
    EmailTemplateSerializer, EmailAccountSerializer,
)
from apps.communications.communication_service import ThreadService
from apps.communications.notification_service import NotificationService
from apps.core.responses import success_response, error_response
from drf_spectacular.utils import extend_schema, OpenApiResponse


class EmailAccountViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EmailAccountSerializer

    def get_queryset(self):
        return EmailAccount.objects.filter(
            user_id=self.request.user.id,
            tenant_id=self.request.user.tenant_id
        )

    def perform_create(self, serializer):
        serializer.save(
            user_id=self.request.user.id,
            tenant_id=self.request.user.tenant_id
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data={'email_accounts': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data={'email_account': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return success_response(
                data={'email_account': serializer.data},
                message="Email account connected successfully.",
                status_code=status.HTTP_201_CREATED
            )
        return error_response(message="Invalid data", errors=serializer.errors)

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Email account updated successfully"),
            404: OpenApiResponse(description="Email account not found"),
        }
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return success_response(
                data={'email_account': serializer.data},
                message="Email account updated successfully."
            )
        return error_response(message="Invalid data", errors=serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(message="Email account disconnected successfully.")


class MessageThreadListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        thread_type = request.query_params.get('thread_type')
        related_entity_type = request.query_params.get('related_entity_type')
        related_entity_id = request.query_params.get('related_entity_id')
        include_archived = request.query_params.get('include_archived', '').lower() == 'true'

        threads = ThreadService.get_threads_for_user(
            tenant_id=request.user.tenant_id,
            user_id=request.user.id,
            thread_type=thread_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            include_archived=include_archived,
        )
        serializer = MessageThreadSerializer(threads, many=True, context={'request': request})
        return success_response(
            data={'threads': serializer.data},
            message="Threads retrieved.",
            meta={'total': threads.count()}
        )

    def post(self, request):
        serializer = MessageThreadCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", errors=serializer.errors)

        data = serializer.validated_data
        participant_ids = data.get('participant_user_ids', [])
        # Always include the creator
        creator_id = request.user.id
        if creator_id not in participant_ids:
            participant_ids = [creator_id] + list(participant_ids)

        thread = ThreadService.create_thread(
            tenant_id=request.user.tenant_id,
            created_by_user_id=creator_id,
            thread_type=data.get('thread_type', 'general'),
            subject=data.get('subject', ''),
            is_internal=data.get('is_internal', True),
            related_entity_type=data.get('related_entity_type', ''),
            related_entity_id=data.get('related_entity_id'),
            participant_user_ids=participant_ids,
        )

        message = ThreadService.add_message(
            thread_id=thread.id,
            requesting_tenant_id=request.user.tenant_id,
            sender_user_id=creator_id,
            body=data['message'],
        )

        return success_response(
            data={
                'thread': MessageThreadSerializer(thread, context={'request': request}).data,
                'message': MessageSerializer(message, context={'request': request}).data,
            },
            message="Thread created.",
            status_code=status.HTTP_201_CREATED
        )


class MessageThreadDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            thread = ThreadService.get_thread(
                thread_id=pk,
                requesting_tenant_id=request.user.tenant_id,
                requesting_user_id=request.user.id,
            )
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_404_NOT_FOUND)

        return success_response(
            data={'thread': MessageThreadSerializer(thread, context={'request': request}).data},
            message="Thread retrieved."
        )


class ThreadMessagesView(APIView):
    """GET messages for a thread / POST to send a message."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            messages = ThreadService.get_messages(
                thread_id=pk,
                requesting_tenant_id=request.user.tenant_id,
                requesting_user_id=request.user.id,
            )
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_403_FORBIDDEN)

        return success_response(
            data={'messages': MessageSerializer(messages, many=True, context={'request': request}).data},
            message="Messages retrieved.",
            meta={'total': messages.count()}
        )

    def post(self, request, pk):
        body = request.data.get('message') or request.data.get('body', '')
        if not body:
            return error_response("message is required.")

        try:
            message = ThreadService.add_message(
                thread_id=pk,
                requesting_tenant_id=request.user.tenant_id,
                sender_user_id=request.user.id,
                sender_tenant_id=request.user.tenant_id,
                body=body,
                message_type=request.data.get('message_type', 'text'),
                attachments=request.data.get('attachments', []),
            )
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_403_FORBIDDEN)

        return success_response(
            data={'message': MessageSerializer(message, context={'request': request}).data},
            message="Message sent.",
            status_code=status.HTTP_201_CREATED
        )


class MessageReplyView(APIView):
    """Legacy reply endpoint — delegates to ThreadMessagesView logic."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        body = request.data.get('message', '')
        if not body:
            return error_response("message is required.")

        try:
            message = ThreadService.add_message(
                thread_id=pk,
                requesting_tenant_id=request.user.tenant_id,
                sender_user_id=request.user.id,
                sender_tenant_id=request.user.tenant_id,
                body=body,
                attachments=request.data.get('attachments', []),
            )
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_403_FORBIDDEN)

        return success_response(
            data={'message': MessageSerializer(message, context={'request': request}).data},
            message="Reply sent.",
            status_code=status.HTTP_201_CREATED
        )


class ThreadMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ThreadService.mark_thread_read(
                thread_id=pk,
                requesting_tenant_id=request.user.tenant_id,
                user_id=request.user.id,
            )
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_404_NOT_FOUND)
        return success_response(message="Thread marked as read.")


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_read_param = request.query_params.get('is_read')
        is_read = None
        if is_read_param is not None:
            is_read = is_read_param.lower() == 'true'

        severity = request.query_params.get('severity')
        notification_type = request.query_params.get('type')

        qs = NotificationService.get_notifications(
            user_id=request.user.id,
            tenant_id=getattr(request.user, 'tenant_id', None),
            is_read=is_read,
            severity=severity,
            notification_type=notification_type,
        )

        return success_response(
            data={'notifications': NotificationSerializer(qs, many=True).data},
            message="Notifications retrieved.",
            meta={
                'total': qs.count(),
                'unread': NotificationService.get_unread_count(
                    user_id=request.user.id,
                    tenant_id=getattr(request.user, 'tenant_id', None),
                ),
            }
        )


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = NotificationService.get_unread_count(
            user_id=request.user.id,
            tenant_id=getattr(request.user, 'tenant_id', None),
        )
        return success_response(data={'unread_count': count})


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = NotificationService.mark_read(
                notification_id=pk,
                user_id=request.user.id,
            )
        except Exception:
            return error_response("Notification not found.", status_code=status.HTTP_404_NOT_FOUND)

        return success_response(
            data={'notification': NotificationSerializer(notification).data},
            message="Notification marked as read."
        )


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = NotificationService.mark_all_read(
            user_id=request.user.id,
            tenant_id=getattr(request.user, 'tenant_id', None),
        )
        return success_response(
            message=f"All notifications marked as read.",
            data={'updated_count': count},
        )


class EmailTemplateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        templates = EmailTemplate.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
            is_active=True
        )
        return success_response(
            data={'templates': EmailTemplateSerializer(templates, many=True).data},
            message="Templates retrieved."
        )

    def post(self, request):
        serializer = EmailTemplateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        template = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        return success_response(
            data={'template': EmailTemplateSerializer(template).data},
            message="Template created.",
            status_code=status.HTTP_201_CREATED
        )


class EmailTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return EmailTemplate.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except EmailTemplate.DoesNotExist:
            return None

    def get(self, request, pk):
        template = self.get_object(request, pk)
        if not template:
            return error_response("Template not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'template': EmailTemplateSerializer(template).data},
            message="Template retrieved."
        )

    def put(self, request, pk):
        template = self.get_object(request, pk)
        if not template:
            return error_response("Template not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = EmailTemplateSerializer(template, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'template': serializer.data},
            message="Template updated."
        )

    def delete(self, request, pk):
        template = self.get_object(request, pk)
        if not template:
            return error_response("Template not found.", status_code=status.HTTP_404_NOT_FOUND)

        template.soft_delete()
        return success_response(
            message="Template deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )
