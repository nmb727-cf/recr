import uuid

from celery import shared_task
from django.utils import timezone

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.passport.models import DataWithdrawalRequest, TalentPassport


def _process_due_withdrawal_deletions(now=None):
    now = now or timezone.now()
    due = DataWithdrawalRequest.objects.filter(
        status="anonymized",
        deletion_scheduled_at__isnull=False,
        deletion_scheduled_at__lte=now,
    )
    processed = 0

    for withdrawal in due.iterator():
        user = CustomUser.objects.filter(id=withdrawal.user_id).first()
        passports = list(
            TalentPassport.objects.filter(user_id=withdrawal.user_id, is_deleted=False).values_list("id", flat=True)
        )

        if user:
            tombstone_email = f"withdrawn-{user.id.hex}@deleted.local"
            user.email = tombstone_email
            user.first_name = "Deleted"
            user.last_name = "User"
            user.phone = ""
            user.phone_number = ""
            user.is_active = False
            user.is_deleted = True
            user.deleted_at = now
            user.metadata = {
                **(user.metadata or {}),
                "withdrawal_deleted_at": now.isoformat(),
                "withdrawal_request_id": str(withdrawal.id),
            }
            user.save(update_fields=[
                "email", "first_name", "last_name", "phone", "phone_number",
                "is_active", "is_deleted", "deleted_at", "metadata", "updated_at",
            ])

        candidate_filters = {}
        if user:
            candidate_filters["user_id"] = user.id

        candidate_qs = Candidate.objects.none()
        if candidate_filters:
            candidate_qs = Candidate.objects.filter(is_deleted=False, **candidate_filters)
        if passports:
            candidate_qs = (candidate_qs | Candidate.objects.filter(is_deleted=False, passport_id__in=passports)).distinct()

        for candidate in candidate_qs:
            candidate.first_name = "Deleted"
            candidate.last_name = "Candidate"
            candidate.email = ""
            candidate.phone = ""
            candidate.phone_number = ""
            candidate.resume_url = ""
            candidate.linkedin_url = ""
            candidate.passport_linked = False
            candidate.passport_id = None
            candidate.user_id = None
            candidate.is_deleted = True
            candidate.deleted_at = now
            candidate.metadata = {
                **(candidate.metadata or {}),
                "withdrawal_deleted_at": now.isoformat(),
                "withdrawal_request_id": str(withdrawal.id),
            }
            candidate.save(update_fields=[
                "first_name", "last_name", "email", "phone", "phone_number",
                "resume_url", "linkedin_url", "passport_linked", "passport_id", "user_id",
                "is_deleted", "deleted_at", "metadata", "updated_at",
            ])

        if passports:
            TalentPassport.objects.filter(id__in=passports).update(
                is_active=False,
                is_deleted=True,
                deleted_at=now,
                share_link_token=uuid.uuid4().hex,
                updated_at=now,
            )

        withdrawal.status = "deleted"
        withdrawal.completed_at = now
        withdrawal.metadata = {
            **(withdrawal.metadata or {}),
            "deletion_processed_at": now.isoformat(),
            "tenant_notifications_pending": False,
        }
        withdrawal.save(update_fields=["status", "completed_at", "metadata"])
        processed += 1

    return {"processed": processed}


@shared_task(name="passport.process_due_withdrawal_deletions")
def process_due_withdrawal_deletions_task():
    return _process_due_withdrawal_deletions()

