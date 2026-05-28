import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.communications.models import Notification
from apps.passport.notification_service import dispatch_withdrawal_notifications
from apps.passport.models import DataWithdrawalRequest, PassportAccessLog, TalentPassport
from apps.passport.withdrawal_views import DataWithdrawalView
from apps.tenants.models import Client


class PassportWithdrawalTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_a = Client.objects.create(
            schema_name="withdrawal_a",
            name="Withdrawal A",
            slug="withdrawal-a",
            tenant_type="company",
            status="active",
        )
        self.tenant_b = Client.objects.create(
            schema_name="withdrawal_b",
            name="Withdrawal B",
            slug="withdrawal-b",
            tenant_type="company",
            status="active",
        )

    def test_withdrawal_anonymizes_linked_candidate_and_tracks_tenants(self):
        user = CustomUser.objects.create_user(
            email="withdraw@example.com",
            password="testpass123",
            role="candidate",
            tenant_id=self.tenant_a.id,
            first_name="Real",
            last_name="Name",
            phone="+911111111111",
        )
        candidate = Candidate.objects.create(
            first_name="Real",
            last_name="Name",
            email="withdraw@example.com",
            phone="+911111111111",
            tenant_id=self.tenant_a.id,
            source="self",
            source_type="direct",
            user_id=user.id,
            passport_linked=True,
        )
        passport = TalentPassport.objects.create(
            user_id=user.id,
            candidate_id=candidate.id,
            is_active=True,
            headline="h",
            summary="s",
        )
        candidate.passport_id = passport.id
        candidate.save(update_fields=["passport_id", "updated_at"])

        PassportAccessLog.objects.create(
            passport_id=passport.id,
            access_type="view",
            accessed_by_tenant_id=self.tenant_b.id,
        )
        tenant_b_admin = CustomUser.objects.create_user(
            email="tenant-b-admin@example.com",
            password="testpass123",
            role="tenant_admin",
            tenant_id=self.tenant_b.id,
        )
        tenant_a_admin = CustomUser.objects.create_user(
            email="tenant-a-admin@example.com",
            password="testpass123",
            role="tenant_admin",
            tenant_id=self.tenant_a.id,
        )

        request = self.factory.post("/api/v1/passport/withdraw-data/", {"reason": "privacy"}, format="json")
        force_authenticate(request, user=user)
        response = DataWithdrawalView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        candidate.refresh_from_db()
        passport.refresh_from_db()
        user.refresh_from_db()
        withdrawal = DataWithdrawalRequest.objects.get(user_id=user.id)
        expected_tenant_from_access_log = str(
            PassportAccessLog.objects.filter(passport_id=passport.id)
            .values_list("accessed_by_tenant_id", flat=True)
            .first()
        )
        expected_candidate_tenant = str(candidate.tenant_id)

        self.assertFalse(passport.is_active)
        self.assertEqual(user.first_name, "Withdrawn")
        self.assertEqual(candidate.first_name, "Withdrawn")
        self.assertFalse(candidate.passport_linked)
        self.assertIsNone(candidate.passport_id)
        self.assertIsNone(candidate.user_id)
        self.assertIn(expected_tenant_from_access_log, withdrawal.notified_tenants)
        self.assertIn(expected_candidate_tenant, withdrawal.notified_tenants)
        self.assertEqual(
            Notification.objects.filter(
                user_id=tenant_b_admin.id,
                notification_type="passport.withdrawal_notice",
            ).count(),
            1,
        )
        self.assertEqual(
            Notification.objects.filter(
                user_id=tenant_a_admin.id,
                notification_type="passport.withdrawal_notice",
            ).count(),
            1,
        )
        self.assertEqual(
            Notification.objects.filter(
                user_id=user.id,
                notification_type="passport.withdrawal_notice",
            ).count(),
            0,
        )
        self.assertFalse(withdrawal.metadata.get("tenant_notifications_pending", True))

    def test_withdrawal_does_not_touch_unowned_passport_candidate(self):
        user = CustomUser.objects.create_user(
            email="withdraw2@example.com",
            password="testpass123",
            role="candidate",
            tenant_id=self.tenant_a.id,
        )
        other_user_id = uuid.uuid4()
        candidate = Candidate.objects.create(
            first_name="Other",
            last_name="Person",
            email="other@example.com",
            tenant_id=self.tenant_a.id,
            source="company",
            source_type="direct",
            user_id=other_user_id,
        )
        passport = TalentPassport.objects.create(
            user_id=user.id,
            candidate_id=candidate.id,
            is_active=True,
        )
        candidate.passport_id = passport.id
        candidate.passport_linked = True
        candidate.save(update_fields=["passport_id", "passport_linked", "updated_at"])

        request = self.factory.post("/api/v1/passport/withdraw-data/", {}, format="json")
        force_authenticate(request, user=user)
        response = DataWithdrawalView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        candidate.refresh_from_db()
        self.assertEqual(candidate.first_name, "Other")
        self.assertTrue(candidate.passport_linked)
        self.assertEqual(candidate.user_id, other_user_id)

    def test_withdrawal_notification_dispatch_is_idempotent(self):
        admin = CustomUser.objects.create_user(
            email="idempotent-admin@example.com",
            password="testpass123",
            role="tenant_admin",
            tenant_id=self.tenant_b.id,
        )
        withdrawal = DataWithdrawalRequest.objects.create(
            candidate_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            status="anonymized",
            notified_tenants=[str(self.tenant_b.id)],
            metadata={
                "tenant_notifications_sent_at": {
                    str(self.tenant_b.id): "2026-05-05T00:00:00+00:00",
                },
            },
        )
        result = dispatch_withdrawal_notifications(
            withdrawal=withdrawal,
            actor_user_id=uuid.uuid4(),
        )
        self.assertIn(str(self.tenant_b.id), result["sent_tenants"])
        self.assertEqual(
            Notification.objects.filter(
                user_id=admin.id,
                notification_type="passport.withdrawal_notice",
            ).count(),
            0,
        )
