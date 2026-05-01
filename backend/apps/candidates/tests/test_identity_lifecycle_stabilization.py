import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.accounts.models import CustomUser
from apps.accounts.views import RegisterCandidateView
from apps.candidates.identity_service import resolve_candidate_identity
from apps.candidates.models import Candidate, CandidateTenantRight
from apps.jobs.views import _get_or_create_candidate_for_user
from apps.tenants.models import Client


class IdentityLifecycleStabilizationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.public_tenant = Client.objects.create(
            schema_name='public',
            name='Public',
            slug='public',
            tenant_type='candidate_pool',
            status='active',
        )
        self.company_tenant = Client.objects.create(
            schema_name='company_a',
            name='Company A',
            slug='company-a',
            tenant_type='company',
            status='active',
        )
        self.agency_tenant = Client.objects.create(
            schema_name='agency_a',
            name='Agency A',
            slug='agency-a',
            tenant_type='agency',
            status='active',
        )
        self.company_user = CustomUser.objects.create_user(
            email='company-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.company_tenant.id,
        )
        self.agency_user = CustomUser.objects.create_user(
            email='agency-admin@example.com',
            password='testpass123',
            role='agency_admin',
            tenant_id=self.agency_tenant.id,
        )

    def test_1_candidate_self_signup_creates_and_links_stable_identity(self):
        request = self.factory.post('/api/v1/auth/register/candidate/', {
            'first_name': 'Asha',
            'last_name': 'Menon',
            'email': 'asha+signup@example.com',
            'password': 'StrongPass123',
            'password_confirm': 'StrongPass123',
        }, format='json')
        response = RegisterCandidateView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(email='asha+signup@example.com')
        candidate = Candidate.objects.filter(user_id=user.id, is_deleted=False).first()
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.email.lower(), user.email.lower())

    def test_2_company_add_reuses_existing_candidate_identity(self):
        existing = Candidate.objects.create(
            first_name='Riya',
            last_name='Shah',
            email='riya@example.com',
            phone='+919111111111',
            source='self',
            source_type='direct',
        )
        result = resolve_candidate_identity(
            email='riya@example.com',
            phone='+919111111111',
            tenant_id=self.company_tenant.id,
            create_if_missing=True,
            allow_cross_tenant=True,
            actor_user_id=self.company_user.id,
            ensure_tenant_association_flag=True,
            ensure_visibility=True,
            source='candidate_manual_add',
        )

        self.assertFalse(result.created)
        self.assertEqual(result.candidate.id, existing.id)

    def test_3_agency_add_reuses_existing_candidate_identity(self):
        existing = Candidate.objects.create(
            first_name='Rahul',
            last_name='Iyer',
            email='rahul@example.com',
            phone='+919222222222',
            source='company',
            source_type='direct',
            tenant_id=self.company_tenant.id,
            owner_tenant_id=self.company_tenant.id,
        )
        result = resolve_candidate_identity(
            email='rahul@example.com',
            phone='+919222222222',
            tenant_id=self.agency_tenant.id,
            create_if_missing=True,
            allow_cross_tenant=True,
            actor_user_id=self.agency_user.id,
            ensure_tenant_association_flag=True,
            ensure_visibility=True,
            source='agency_submission',
        )

        self.assertFalse(result.created)
        self.assertEqual(result.candidate.id, existing.id)

    def test_4_invite_link_flow_does_not_duplicate_candidate(self):
        first = resolve_candidate_identity(
            email='invite@example.com',
            phone='+919333333333',
            tenant_id=self.company_tenant.id,
            create_if_missing=True,
            allow_cross_tenant=True,
            actor_user_id=self.company_user.id,
            ensure_tenant_association_flag=True,
            ensure_visibility=True,
            source='invite_apply',
        )
        second = resolve_candidate_identity(
            email='invite@example.com',
            phone='+919333333333',
            tenant_id=self.company_tenant.id,
            create_if_missing=True,
            allow_cross_tenant=True,
            actor_user_id=self.company_user.id,
            ensure_tenant_association_flag=True,
            ensure_visibility=True,
            source='invite_apply',
        )

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.candidate.id, second.candidate.id)
        self.assertEqual(Candidate.objects.filter(email__iexact='invite@example.com', is_deleted=False).count(), 1)

    def test_5_job_application_resolution_uses_canonical_candidate(self):
        user = CustomUser.objects.create_user(
            email='apply-user@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.public_tenant.id,
            first_name='Apply',
            last_name='User',
        )
        existing = Candidate.objects.create(
            first_name='Apply',
            last_name='User',
            email='apply-user@example.com',
            phone='',
            source='company',
            source_type='direct',
            account_status='none',
        )

        resolved = _get_or_create_candidate_for_user(user)
        existing.refresh_from_db()

        self.assertEqual(resolved.id, existing.id)
        self.assertEqual(str(existing.user_id), str(user.id))

    def test_6_tenant_associations_are_explicit_and_correct(self):
        candidate = Candidate.objects.create(
            first_name='Priya',
            last_name='Nair',
            email='priya@example.com',
            phone='+919444444444',
            source='self',
            source_type='direct',
        )
        resolve_candidate_identity(
            email='priya@example.com',
            phone='+919444444444',
            tenant_id=self.company_tenant.id,
            create_if_missing=True,
            allow_cross_tenant=True,
            actor_user_id=self.company_user.id,
            ensure_tenant_association_flag=True,
            ensure_visibility=True,
            source='candidate_manual_add',
        )
        resolve_candidate_identity(
            email='priya@example.com',
            phone='+919444444444',
            tenant_id=self.agency_tenant.id,
            create_if_missing=True,
            allow_cross_tenant=True,
            actor_user_id=self.agency_user.id,
            ensure_tenant_association_flag=True,
            ensure_visibility=True,
            source='agency_submission',
        )

        rights = CandidateTenantRight.objects.filter(candidate_id=candidate.id, relationship_type='shared', is_deleted=False)
        target_tenants = {str(r.target_tenant_id) for r in rights}
        self.assertIn(str(uuid.UUID(int=int(self.company_tenant.id))), target_tenants)
        self.assertIn(str(uuid.UUID(int=int(self.agency_tenant.id))), target_tenants)

    def test_7_conservative_resolution_does_not_overmerge_without_identity_keys(self):
        existing = Candidate.objects.create(
            first_name='Same',
            last_name='Name',
            email='same-name@example.com',
            phone='+919555555555',
            source='self',
            source_type='direct',
        )
        result = resolve_candidate_identity(
            email='',
            phone='',
            tenant_id=self.company_tenant.id,
            create_if_missing=True,
            allow_cross_tenant=True,
            actor_user_id=self.company_user.id,
            ensure_tenant_association_flag=True,
            ensure_visibility=True,
            source='candidate_manual_add',
            candidate_defaults={
                'first_name': 'Same',
                'last_name': 'Name',
                'email': '',
                'phone': '',
                'tenant_id': self.company_tenant.id,
                'owner_tenant_id': self.company_tenant.id,
                'created_by': self.company_user.id,
            },
        )

        self.assertTrue(result.created)
        self.assertNotEqual(result.candidate.id, existing.id)
