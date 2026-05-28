import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.passport.candidate_sync_views import MyCandidateView
from apps.passport.models import PassportRevocation, TalentPassport
from apps.passport.views import PassportImportView, PublicPassportView
from apps.tenants.models import Client


class PassportSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_a = Client.objects.create(
            schema_name="passport_sec_a",
            name="Passport Sec A",
            slug="passport-sec-a",
            tenant_type="company",
            status="active",
        )
        self.tenant_b = Client.objects.create(
            schema_name="passport_sec_b",
            name="Passport Sec B",
            slug="passport-sec-b",
            tenant_type="company",
            status="active",
        )

    def test_my_candidate_endpoint_requires_candidate_role(self):
        recruiter = CustomUser.objects.create_user(
            email="recruiter-passport@example.com",
            password="testpass123",
            role="recruiter",
            tenant_id=self.tenant_a.id,
        )
        request = self.factory.get("/api/v1/passport/my-candidate/")
        force_authenticate(request, user=recruiter)
        response = MyCandidateView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_passport_import_blocked_when_revoked_for_tenant(self):
        importer = CustomUser.objects.create_user(
            email="importer-passport@example.com",
            password="testpass123",
            role="recruiter",
            tenant_id=self.tenant_a.id,
        )
        owner_id = uuid.uuid4()
        passport = TalentPassport.objects.create(
            user_id=owner_id,
            share_link_token="revoked-token-123",
            is_active=True,
            is_deleted=False,
            current_title="Engineer",
        )
        PassportRevocation.objects.create(
            passport_id=passport.id,
            revoked_from_tenant_id=self.tenant_a.id,
            revoked_by=importer.id,
            reason="policy",
        )

        request = self.factory.post(
            "/api/v1/passport/import/",
            {"passport_token": "revoked-token-123"},
            format="json",
        )
        force_authenticate(request, user=importer)
        response = PassportImportView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_public_passport_hides_metadata(self):
        passport = TalentPassport.objects.create(
            user_id=uuid.uuid4(),
            share_link_token="public-token-123",
            is_active=True,
            is_deleted=False,
            headline="Visible",
            metadata={"internal_notes": "should not be public"},
        )
        request = self.factory.get(f"/api/v1/passport/public/{passport.share_link_token}/")
        response = PublicPassportView.as_view()(request, token=passport.share_link_token)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("metadata", response.data["data"]["passport"])

    def test_my_candidate_lookup_respects_tenant_boundary(self):
        candidate_user = CustomUser.objects.create_user(
            email="candidate-boundary@example.com",
            password="testpass123",
            role="candidate",
            tenant_id=self.tenant_a.id,
            phone="+919999999999",
        )
        Candidate.objects.create(
            first_name="Cross",
            last_name="Tenant",
            email="candidate-boundary@example.com",
            tenant_id=self.tenant_b.id,
            source="company",
            source_type="direct",
        )
        request = self.factory.get("/api/v1/passport/my-candidate/")
        force_authenticate(request, user=candidate_user)
        response = MyCandidateView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["no_candidate"])
