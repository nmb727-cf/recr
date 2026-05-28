from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.passport.models import DataWithdrawalRequest, TalentPassport
from apps.passport.tasks import _process_due_withdrawal_deletions
from apps.tenants.models import Client


class PassportWithdrawalDeletionTaskTests(TestCase):
    def setUp(self):
        self.tenant = Client.objects.create(
            schema_name="withdrawal_task_tenant",
            name="Withdrawal Task Tenant",
            slug="withdrawal-task-tenant",
            tenant_type="company",
            status="active",
        )

    def test_process_due_deletes_due_withdrawal_records(self):
        user = CustomUser.objects.create_user(
            email="due-withdrawal@example.com",
            password="testpass123",
            role="candidate",
            tenant_id=self.tenant.id,
            first_name="Due",
            last_name="User",
        )
        candidate = Candidate.objects.create(
            first_name="Due",
            last_name="Candidate",
            email="due-withdrawal@example.com",
            tenant_id=self.tenant.id,
            source="self",
            source_type="direct",
            user_id=user.id,
        )
        passport = TalentPassport.objects.create(
            user_id=user.id,
            candidate_id=candidate.id,
            is_active=False,
        )
        candidate.passport_id = passport.id
        candidate.passport_linked = True
        candidate.save(update_fields=["passport_id", "passport_linked", "updated_at"])

        withdrawal = DataWithdrawalRequest.objects.create(
            candidate_id=candidate.id,
            user_id=user.id,
            status="anonymized",
            anonymized_at=timezone.now() - timedelta(days=30),
            deletion_scheduled_at=timezone.now() - timedelta(minutes=1),
        )

        result = _process_due_withdrawal_deletions()
        self.assertEqual(result["processed"], 1)

        user.refresh_from_db()
        candidate.refresh_from_db()
        passport.refresh_from_db()
        withdrawal.refresh_from_db()

        self.assertEqual(withdrawal.status, "deleted")
        self.assertIsNotNone(withdrawal.completed_at)
        self.assertTrue(user.is_deleted)
        self.assertFalse(user.is_active)
        self.assertTrue(candidate.is_deleted)
        self.assertFalse(candidate.passport_linked)
        self.assertIsNone(candidate.user_id)
        self.assertIsNone(candidate.passport_id)
        self.assertTrue(passport.is_deleted)
        self.assertFalse(passport.is_active)

    def test_process_due_skips_future_scheduled_withdrawals(self):
        user = CustomUser.objects.create_user(
            email="future-withdrawal@example.com",
            password="testpass123",
            role="candidate",
            tenant_id=self.tenant.id,
        )
        withdrawal = DataWithdrawalRequest.objects.create(
            candidate_id=user.id,
            user_id=user.id,
            status="anonymized",
            anonymized_at=timezone.now(),
            deletion_scheduled_at=timezone.now() + timedelta(days=1),
        )

        result = _process_due_withdrawal_deletions()
        self.assertEqual(result["processed"], 0)
        withdrawal.refresh_from_db()
        self.assertEqual(withdrawal.status, "anonymized")
