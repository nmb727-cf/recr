import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.agencies.models import AgencyClientRelationship, AgencyJobAssignment
from apps.agencies.views import (
    AgencyJobAssignmentListView,
    AgencyRelationshipDetailView,
    AgencyRelationshipSuspendView,
)
from apps.candidates.models import Candidate
from apps.candidates.views import _get_visible_candidate
from apps.analytics.views import DashboardView
from apps.pipeline.models import Application


class TenantSafetyHardeningTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.company_tenant = uuid.uuid4()
        self.other_tenant = uuid.uuid4()
        self.agency_tenant = uuid.uuid4()

        self.company_admin = CustomUser.objects.create_user(
            email='tenant-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.company_tenant,
        )
        self.other_admin = CustomUser.objects.create_user(
            email='other-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.other_tenant,
        )
        self.super_admin = CustomUser.objects.create_user(
            email='super-admin@example.com',
            password='testpass123',
            role='super_admin',
            tenant_id=self.other_tenant,
            is_staff=True,
        )

        self.relationship = AgencyClientRelationship.objects.create(
            tenant_id=self.company_tenant,
            company_tenant_id=self.company_tenant,
            agency_tenant_id=self.agency_tenant,
            status='active',
            created_by=self.company_admin.id,
        )
        self.assignment = AgencyJobAssignment.objects.create(
            tenant_id=self.company_tenant,
            requisition_id=uuid.uuid4(),
            agency_tenant_id=self.agency_tenant,
            status='active',
            created_by=self.company_admin.id,
        )

    def test_query_param_tenant_scope_widening_is_rejected(self):
        request = self.factory.get(
            f'/api/v1/agencies/assignments/?tenant_id={self.other_tenant}'
        )
        force_authenticate(request, user=self.company_admin)

        response = AgencyJobAssignmentListView.as_view()(request)
        self.assertEqual(response.status_code, 400)

    def test_cannot_read_or_mutate_other_tenant_relationship(self):
        request_get = self.factory.get(f'/api/v1/agencies/relationships/{self.relationship.id}/')
        force_authenticate(request_get, user=self.other_admin)
        response_get = AgencyRelationshipDetailView.as_view()(request_get, pk=self.relationship.id)
        self.assertEqual(response_get.status_code, 404)

        request_suspend = self.factory.post(
            f'/api/v1/agencies/relationships/{self.relationship.id}/suspend/',
            {'reason': 'unauthorized attempt'},
            format='json',
        )
        force_authenticate(request_suspend, user=self.other_admin)
        response_suspend = AgencyRelationshipSuspendView.as_view()(request_suspend, pk=self.relationship.id)
        self.assertEqual(response_suspend.status_code, 404)

    def test_admin_override_allowed_for_scoped_relationship_detail(self):
        request = self.factory.get(f'/api/v1/agencies/relationships/{self.relationship.id}/')
        force_authenticate(request, user=self.super_admin)

        response = AgencyRelationshipDetailView.as_view()(request, pk=self.relationship.id)
        self.assertEqual(response.status_code, 200)

    def test_global_candidate_visibility_is_association_bound(self):
        global_candidate = Candidate.objects.create(
            tenant_id=self.other_tenant,
            first_name='Global',
            last_name='Visible',
            email='global.visible@example.com',
        )
        hidden_other_tenant_candidate = Candidate.objects.create(
            tenant_id=self.other_tenant,
            first_name='Other',
            last_name='Tenant',
            email='other.tenant@example.com',
        )
        Application.objects.create(
            tenant_id=self.company_tenant,
            candidate_id=global_candidate.id,
            requisition_id=uuid.uuid4(),
            status='applied',
        )

        request = self.factory.get('/api/v1/candidates/')
        request.user = self.company_admin

        visible_candidate = _get_visible_candidate(request, global_candidate.id)
        hidden_candidate = _get_visible_candidate(request, hidden_other_tenant_candidate.id)

        self.assertIsNotNone(visible_candidate)
        self.assertEqual(visible_candidate.id, global_candidate.id)
        self.assertIsNone(hidden_candidate)

    def test_candidate_scope_cannot_be_widened_by_query_param(self):
        request = self.factory.get(f'/api/v1/analytics/dashboard/?tenant_id={self.other_tenant}')
        force_authenticate(request, user=self.company_admin)

        response = DashboardView.as_view()(request)
        self.assertEqual(response.status_code, 400)
