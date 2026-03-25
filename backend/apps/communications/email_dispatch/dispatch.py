import logging

from django.utils import timezone

from apps.communications.email_accounts.providers import get_provider
from apps.communications.email_audit.services import EmailAuditService
from apps.communications.email_dispatch.routing import EmailRoutingService
from apps.communications.email_dispatch.types import EmailSendRequest
from apps.communications.email_templates.services import EmailTemplateService
from apps.communications.models import (
    EmailAttachment,
    EmailMessage,
    EmailMessageStatus,
    EmailSendingAccount,
    EmailTemplateDefinition,
    QuickReplyTemplate,
)

logger = logging.getLogger(__name__)


class EmailDispatchService:
    @staticmethod
    def _render_content(request: EmailSendRequest) -> tuple[str, str, str]:
        subject = request.subject or ''
        body_html = request.body_html or ''
        body_text = request.body_text or ''

        if request.template_id:
            template = EmailTemplateDefinition.objects.filter(id=request.template_id).first()
            if template:
                rendered = EmailTemplateService.render_template(template, request.variables)
                subject = rendered['subject'] or subject
                body_html = rendered['body_html'] or body_html
                body_text = rendered['body_text'] or body_text

        if request.quick_reply_template_id:
            quick = QuickReplyTemplate.objects.filter(id=request.quick_reply_template_id).first()
            if quick:
                rendered = EmailTemplateService.render_quick_reply(quick, request.variables)
                if rendered['subject']:
                    subject = rendered['subject']
                body_html = rendered['body_html'] or body_html
                body_text = rendered['body_text'] or body_text

        return subject, body_html, body_text

    @staticmethod
    def _apply_signature(body_html: str, body_text: str, account: EmailSendingAccount | None):
        if not account:
            return body_html, body_text
        if account.signature_html:
            body_html = f'{body_html}<br><br>{account.signature_html}' if body_html else account.signature_html
        if account.signature_text:
            body_text = f'{body_text}\n\n{account.signature_text}' if body_text else account.signature_text
        return body_html, body_text

    @classmethod
    def create_message_record(cls, request: EmailSendRequest, route, subject: str, body_html: str, body_text: str) -> EmailMessage:
        message = EmailMessage.objects.create(
            tenant_id=request.tenant_id,
            related_object_type=request.related_object_type,
            related_object_id=request.related_object_id,
            workflow_context_type=request.workflow_context_type,
            workflow_context_id=request.workflow_context_id,
            sender_account_id=route.account_id,
            actual_route_used=route.route_used,
            from_email=route.from_email,
            from_name=route.from_name,
            reply_to_email=route.reply_to_email,
            to_emails=request.recipients,
            cc_emails=request.cc_emails,
            bcc_emails=request.bcc_emails,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            template_id=request.template_id,
            quick_reply_template_id=request.quick_reply_template_id,
            message_purpose=request.message_purpose,
            status=EmailMessageStatus.QUEUED,
            triggered_by_user_id=request.actor_user_id,
            triggered_by_event_id=request.triggered_by_event_id,
            trigger_source=request.trigger_source,
            metadata_json=request.metadata,
        )
        for attachment in request.attachments:
            EmailAttachment.objects.create(
                email_message=message,
                file_id=attachment.get('file_id', ''),
                storage_path=attachment.get('storage_path', ''),
                filename=attachment.get('filename', 'attachment'),
                mime_type=attachment.get('mime_type', ''),
                size_bytes=int(attachment.get('size_bytes') or 0),
            )

        EmailAuditService.record_usage(
            tenant_id=request.tenant_id,
            actor_user_id=request.actor_user_id,
            action='email.queued',
            target_type='email_message',
            target_id=message.id,
            details={
                'message_purpose': request.message_purpose,
                'route': route.route_used,
                'provider': route.provider_key,
                'recipients': request.recipients,
                'trigger_source': request.trigger_source,
            },
        )
        return message

    @classmethod
    def send_now(cls, request: EmailSendRequest) -> EmailMessage:
        route = EmailRoutingService.resolve_route(request)
        subject, body_html, body_text = cls._render_content(request)

        account = EmailSendingAccount.objects.filter(id=route.account_id).first() if route.account_id else None
        body_html, body_text = cls._apply_signature(body_html, body_text, account)

        message = cls.create_message_record(request, route, subject, body_html, body_text)
        message.status = EmailMessageStatus.SENDING
        message.save(update_fields=['status', 'updated_at'])

        provider = get_provider(route.provider_key)
        send_result = provider.send_email(
            account=account,
            from_email=route.from_email,
            from_name=route.from_name,
            reply_to=route.reply_to_email,
            recipients=request.recipients,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            attachments=request.attachments,
        )

        if send_result.ok:
            message.status = EmailMessageStatus.SENT
            message.provider_message_id = send_result.provider_message_id
            message.provider_thread_id = send_result.provider_thread_id
            message.sent_at = timezone.now()
            message.failure_reason = ''
            message.save(update_fields=['status', 'provider_message_id', 'provider_thread_id', 'sent_at', 'failure_reason', 'updated_at'])
            EmailAuditService.record_delivery_event(
                tenant_id=request.tenant_id,
                message=message,
                provider_type=route.provider_key,
                event_type='sent',
                payload=send_result.raw,
            )
            return message

        message.status = EmailMessageStatus.FAILED
        message.failed_at = timezone.now()
        message.failure_reason = send_result.error[:1000]
        message.save(update_fields=['status', 'failed_at', 'failure_reason', 'updated_at'])
        EmailAuditService.record_delivery_event(
            tenant_id=request.tenant_id,
            message=message,
            provider_type=route.provider_key,
            event_type='failed',
            payload={'error': send_result.error, **send_result.raw},
        )
        return message

    @classmethod
    def queue_send(cls, request: EmailSendRequest):
        from apps.communications.email_dispatch.tasks import send_email_task
        payload = request.__dict__.copy()
        payload['schedule_at'] = request.schedule_at.isoformat() if request.schedule_at else None
        send_email_task.delay(payload)
