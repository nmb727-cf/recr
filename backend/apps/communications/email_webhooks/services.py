from django.utils import timezone

from apps.communications.email_audit.services import EmailAuditService
from apps.communications.models import EmailMessage, EmailMessageStatus


STATUS_BY_EVENT = {
    'queued': EmailMessageStatus.QUEUED,
    'accepted': EmailMessageStatus.SENT,
    'delivered': EmailMessageStatus.DELIVERED,
    'opened': EmailMessageStatus.OPENED,
    'clicked': EmailMessageStatus.CLICKED,
    'bounced': EmailMessageStatus.BOUNCED,
    'complained': EmailMessageStatus.FAILED,
    'failed': EmailMessageStatus.FAILED,
}


class EmailWebhookProcessor:
    @staticmethod
    def process_event(*, provider: str, payload: dict):
        provider_message_id = payload.get('provider_message_id') or payload.get('message_id')
        event_type = payload.get('event_type') or payload.get('event') or 'unknown'

        if not provider_message_id:
            return None

        message = EmailMessage.objects.filter(provider_message_id=provider_message_id).first()
        if not message:
            return None

        EmailAuditService.record_delivery_event(
            tenant_id=message.tenant_id,
            message=message,
            provider_type=provider,
            event_type=event_type,
            payload=payload,
        )

        status = STATUS_BY_EVENT.get(event_type)
        if status:
            message.status = status
            if event_type == 'delivered':
                message.delivered_at = timezone.now()
            if event_type in {'failed', 'bounced', 'complained'}:
                message.failed_at = timezone.now()
                message.failure_reason = payload.get('reason', event_type)
            message.save(update_fields=['status', 'delivered_at', 'failed_at', 'failure_reason', 'updated_at'])

        return message
