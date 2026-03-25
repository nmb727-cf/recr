from django.utils import timezone

from apps.communications.models import (
    EmailDeliveryEvent,
    EmailMessage,
    EmailUsageAudit,
)


class EmailAuditService:
    @staticmethod
    def record_usage(*, tenant_id, actor_user_id, action, target_type, target_id='', details=None):
        return EmailUsageAudit.objects.create(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id or ''),
            details_json=details or {},
        )

    @staticmethod
    def record_delivery_event(*, tenant_id, message: EmailMessage, provider_type: str, event_type: str, payload: dict):
        return EmailDeliveryEvent.objects.create(
            tenant_id=tenant_id,
            email_message=message,
            provider_type=provider_type,
            event_type=event_type,
            raw_payload_json=payload,
            occurred_at=timezone.now(),
        )
