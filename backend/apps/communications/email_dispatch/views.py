from django.db import DatabaseError, ProgrammingError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.communications.email_dispatch.dispatch import EmailDispatchService
from apps.communications.email_dispatch.serializers import EmailMessageSerializer, EmailSendSerializer
from apps.communications.email_dispatch.types import EmailSendRequest
from apps.communications.feature_readiness import email_not_ready_response, get_email_feature_status
from apps.communications.email_templates.services import EmailTemplateService
from apps.communications.models import EmailMessage, EmailTemplateDefinition
from apps.communications.permissions import can_send_email
from apps.core.responses import error_response, success_response


class EmailSendView(APIView):
    permission_classes = [IsAuthenticated, can_send_email]

    def post(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_message': None})
        serializer = EmailSendSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Validation failed', serializer.errors)

        send_request = serializer.to_request(
            tenant_id=request.user.tenant_id,
            actor_user_id=request.user.id,
            trigger_source='manual',
        )

        try:
            if send_request.schedule_at:
                EmailDispatchService.queue_send(send_request)
                return success_response(message='Email scheduled.', status_code=status.HTTP_202_ACCEPTED)
            message = EmailDispatchService.send_now(send_request)
            return success_response(data={'email_message': EmailMessageSerializer(message).data}, status_code=status.HTTP_201_CREATED)
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)


class EmailSendTestView(APIView):
    permission_classes = [IsAuthenticated, can_send_email]

    def post(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_message': None})
        serializer = EmailSendSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Validation failed', serializer.errors)

        send_request = serializer.to_request(
            tenant_id=request.user.tenant_id,
            actor_user_id=request.user.id,
            trigger_source='manual_test',
        )
        send_request.message_purpose = 'platform_notification'
        send_request.allow_fallback = True

        try:
            message = EmailDispatchService.send_now(send_request)
            return success_response(data={'email_message': EmailMessageSerializer(message).data}, status_code=status.HTTP_201_CREATED)
        except Exception as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)


class EmailRenderPreviewView(APIView):
    permission_classes = [IsAuthenticated, can_send_email]

    def post(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'preview': {'subject': '', 'body_html': '', 'body_text': ''}})
        template_id = request.data.get('template_id')
        quick_reply_template_id = request.data.get('quick_reply_template_id')
        variables = request.data.get('variables', {})

        payload = {'subject': '', 'body_html': '', 'body_text': ''}

        try:
            if template_id:
                template = get_object_or_404(EmailTemplateDefinition, id=template_id)
                payload = EmailTemplateService.render_template(template, variables)

            if quick_reply_template_id:
                send_request = EmailSendRequest(
                    tenant_id=str(request.user.tenant_id),
                    actor_user_id=str(request.user.id),
                    email_type='business',
                    message_purpose='platform_notification',
                    recipients=['preview@example.com'],
                    quick_reply_template_id=str(quick_reply_template_id),
                    variables=variables,
                )
                _, body_html, body_text = EmailDispatchService._render_content(send_request)
                payload.update({'body_html': body_html, 'body_text': body_text})
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'preview': {'subject': '', 'body_html': '', 'body_text': ''}})

        return success_response(data={'preview': payload})


class EmailMessageListView(APIView):
    permission_classes = [IsAuthenticated, can_send_email]

    def get(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_messages': []})
        try:
            qs = EmailMessage.objects.filter(tenant_id=request.user.tenant_id).order_by('-created_at')
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_messages': []})
        related_object_type = request.query_params.get('related_object_type')
        related_object_id = request.query_params.get('related_object_id')
        trigger_source = request.query_params.get('trigger_source')
        if related_object_type:
            qs = qs.filter(related_object_type=related_object_type)
        if related_object_id:
            qs = qs.filter(related_object_id=related_object_id)
        if trigger_source:
            qs = qs.filter(trigger_source=trigger_source)
        return success_response(data={'email_messages': EmailMessageSerializer(qs[:200], many=True).data}, meta={'total': qs.count()})


class EmailMessageDetailView(APIView):
    permission_classes = [IsAuthenticated, can_send_email]

    def get(self, request, pk):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_message': None})
        try:
            message = get_object_or_404(EmailMessage, id=pk, tenant_id=request.user.tenant_id)
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_message': None})
        return success_response(data={'email_message': EmailMessageSerializer(message).data})
