from apps.communications.email_dispatch.dispatch import EmailDispatchService
from apps.communications.email_dispatch.types import EmailSendRequest


class EmailRoutingService:
    """
    Backward-compatible facade.
    Existing code calls EmailRoutingService.send_email(...).
    Internally we now route via the new Communication Engine email architecture.
    """

    @staticmethod
    def send_email(
        subject,
        body_text,
        body_html,
        recipient_list,
        user_id=None,
        tenant_id=None,
        email_type='user',
        attachments=None,
        message_purpose='platform_notification',
    ):
        safe_tenant_id = str(tenant_id) if tenant_id else '00000000-0000-0000-0000-000000000000'
        request = EmailSendRequest(
            tenant_id=safe_tenant_id,
            actor_user_id=str(user_id) if user_id else None,
            email_type='system' if email_type == 'system' else 'business',
            message_purpose=message_purpose,
            recipients=recipient_list,
            subject=subject,
            body_text=body_text or '',
            body_html=body_html or '',
            attachments=attachments or [],
            allow_fallback=True,
            trigger_source='legacy_api',
        )
        message = EmailDispatchService.send_now(request)
        return message.status in {'sent', 'delivered', 'opened', 'clicked'}
