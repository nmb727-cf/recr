from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.communications.models import MessageThread, Message, Notification, EmailTemplate
from apps.communications.serializers import (
    MessageThreadSerializer, MessageSerializer,
    NotificationSerializer, EmailTemplateSerializer,
)
from apps.core.responses import success_response, error_response


class MessageThreadListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        threads = MessageThread.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        ).order_by('-last_message_at')
        return success_response(
            data={'threads': MessageThreadSerializer(threads, many=True).data},
            message="Threads retrieved.",
            meta={'total': threads.count()}
        )

    def post(self, request):
        subject = request.data.get('subject', '')
        recipient_id = request.data.get('recipient_id')
        message_text = request.data.get('message', '')
        related_entity_type = request.data.get('related_entity_type', '')
        related_entity_id = request.data.get('related_entity_id')

        if not message_text:
            return error_response("message is required.")

        thread = MessageThread.objects.create(
            tenant_id=request.user.tenant_id,
            subject=subject,
            created_by=request.user.id,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            participant_ids=[str(request.user.id), str(recipient_id)] if recipient_id else [str(request.user.id)],
            last_message_at=timezone.now(),
        )

        message = Message.objects.create(
            tenant_id=request.user.tenant_id,
            thread_id=thread.id,
            sender_id=request.user.id,
            sender_tenant_id=request.user.tenant_id,
            content=message_text,
        )

        return success_response(
            data={
                'thread': MessageThreadSerializer(thread).data,
                'message': MessageSerializer(message).data,
            },
            message="Thread created.",
            status_code=status.HTTP_201_CREATED
        )


class MessageThreadDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            thread = MessageThread.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except MessageThread.DoesNotExist:
            return error_response("Thread not found.", status_code=status.HTTP_404_NOT_FOUND)

        messages = Message.objects.filter(thread_id=pk).order_by('sent_at')
        return success_response(
            data={
                'thread': MessageThreadSerializer(thread).data,
                'messages': MessageSerializer(messages, many=True).data,
            },
            message="Thread retrieved."
        )


class MessageReplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            thread = MessageThread.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except MessageThread.DoesNotExist:
            return error_response("Thread not found.", status_code=status.HTTP_404_NOT_FOUND)

        content = request.data.get('message', '')
        if not content:
            return error_response("message is required.")

        message = Message.objects.create(
            tenant_id=request.user.tenant_id,
            thread_id=thread.id,
            sender_id=request.user.id,
            sender_tenant_id=request.user.tenant_id,
            content=content,
            attachments=request.data.get('attachments', []),
        )

        thread.last_message_at = timezone.now()
        thread.save(update_fields=['last_message_at'])

        return success_response(
            data={'message': MessageSerializer(message).data},
            message="Reply sent.",
            status_code=status.HTTP_201_CREATED
        )


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(user_id=request.user.id)

        is_read = request.query_params.get('is_read')
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == 'true')

        return success_response(
            data={'notifications': NotificationSerializer(qs, many=True).data},
            message="Notifications retrieved.",
            meta={'total': qs.count(), 'unread': qs.filter(is_read=False).count()}
        )


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(
                id=pk,
                user_id=request.user.id
            )
        except Notification.DoesNotExist:
            return error_response("Notification not found.", status_code=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])

        return success_response(
            data={'notification': NotificationSerializer(notification).data},
            message="Notification marked as read."
        )


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(
            user_id=request.user.id,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

        return success_response(message="All notifications marked as read.")


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
