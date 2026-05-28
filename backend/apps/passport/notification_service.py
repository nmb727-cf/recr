import logging
from typing import Iterable

from django.utils import timezone

from apps.accounts.models import CustomUser
from apps.communications.notification_service import NotificationService
from apps.communications.models import NotificationSeverity

logger = logging.getLogger(__name__)


def dispatch_withdrawal_notifications(*, withdrawal, actor_user_id):
    """
    Dispatch in-app notifications to tenant operators affected by a candidate withdrawal.
    Idempotency is tracked in withdrawal.metadata['tenant_notifications_sent_at'].
    """
    tenant_ids: Iterable[str] = withdrawal.notified_tenants or []
    if not tenant_ids:
        withdrawal.metadata = {
            **(withdrawal.metadata or {}),
            "tenant_notifications_pending": False,
        }
        withdrawal.save(update_fields=["metadata"])
        return {"sent_tenants": [], "failed_tenants": []}

    sent_map = dict((withdrawal.metadata or {}).get("tenant_notifications_sent_at", {}))
    sent_tenants = []
    failed_tenants = []

    for tenant_id in tenant_ids:
        tenant_key = str(tenant_id)
        if tenant_key in sent_map:
            sent_tenants.append(tenant_key)
            continue
        try:
            recipients = CustomUser.objects.filter(
                tenant_id=tenant_id,
                is_deleted=False,
                is_active=True,
            ).exclude(
                role="candidate",
            ).exclude(
                id=actor_user_id,
            )
            for user in recipients:
                NotificationService.create_notification(
                    user_id=user.id,
                    tenant_id=user.tenant_id,
                    title="Candidate data withdrawn",
                    body="A candidate has requested data withdrawal and profile access has been revoked.",
                    notification_type="passport.withdrawal_notice",
                    severity=NotificationSeverity.HIGH,
                    related_entity_type="data_withdrawal",
                    related_entity_id=withdrawal.id,
                    metadata={
                        "withdrawal_request_id": str(withdrawal.id),
                        "tenant_id": tenant_key,
                    },
                    schedule_fallback=False,
                )
            sent_map[tenant_key] = timezone.now().isoformat()
            sent_tenants.append(tenant_key)
        except Exception:
            logger.exception(
                "Failed tenant withdrawal notification dispatch: withdrawal=%s tenant=%s",
                withdrawal.id,
                tenant_key,
            )
            failed_tenants.append(tenant_key)

    withdrawal.metadata = {
        **(withdrawal.metadata or {}),
        "tenant_notifications_sent_at": sent_map,
        "tenant_notifications_pending": bool(failed_tenants),
    }
    withdrawal.save(update_fields=["metadata"])
    return {"sent_tenants": sent_tenants, "failed_tenants": failed_tenants}
