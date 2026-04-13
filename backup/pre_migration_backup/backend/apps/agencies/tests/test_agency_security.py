import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.agencies.models import AgencyClientRelationship, AgencyJobAssignment
from apps.agencies.views import (
    AgencyPerformanceListView,
    AgencyJobAssignRecruiterView,
    AgencyRelationshipReactivateView,
)


class AgencySecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.company_tenant = uuid.uuid4()
        self.other_company_tenant = uuid.uuid4()
        self.agency_tenant = uuid.uuid4()
        self.other_agency_tenant = uuid.uuid4()

        self.company_admin = CustomUser.objects.create_user(
            email='company-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.company_tenant,
        )
        self.other_company_admin = CustomUser.objects.create_user(
            email='other-company-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.other_company_tenant,
        )

        self.agency_user = CustomUser.objects.create_user(
            email='agency-user@example.com',
            password='testpass123',
            role='agency_recruiter',
            tenant_id=self.agency_tenant,
        )
        self.outside_agency_user = CustomUser.objects.create_user(
            email='outside-agency-user@example.com',
            password='testpass123',
            role='agency_recruiter',
            tenant_id=self.other_agency_tenant,
        )

        self.relationship = AgencyClientRelationship.objects.create(
            tenant_id=self.company_tenant,
            company_tenant_id=self.company_tenant,
            agency_tenant_id=self.agency_tenant,
            status='suspended',
            tier='standard',
            created_by=self.company_admin.id,
        )

        # Unrelated relationship for a different company
        AgencyClientRelationship.objects.create(
            tenant_id=self.other_company_tenant,
            company_tenant_id=self.other_company_tenant,
            agency_tenant_id=self.other_agency_tenant,
            status='active',
            tier='standard',
            created_by=self.other_company_admin.id,
        )

        self.assignment = AgencyJobAssignment.objects.create(
            tenant_id=self.company_tenant,
            requisition_id=uuid.uuid4(),
            agency_tenant_id=self.agency_tenant,
            status='active',
            created_by=self.company_admin.id,
        )

    def test_company_cannot_access_other_agency_performance(self):
        request = self.factory.get('/api/v1/agencies/performance/?agency_id={}'.format(self.other_agency_tenant))
        force_authenticate(request, user=self.company_admin)

        response = AgencyPerformanceListView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        performance = response.data['data']['performance']
        returned_agencies = {row.get('agency_tenant_id') for row in performance}
        self.assertIn(str(self.agency_tenant), returned_agencies)
        self.assertNotIn(str(self.other_agency_tenant), returned_agencies)

    def test_cannot_assign_recruiter_outside_agency(self):
        request = self.factory.post(
            f'/api/v1/agencies/agency-jobs/{self.assignment.id}/assign-recruiter/',
            {'recruiter_id': str(self.outside_agency_user.id)},
            format='json',
        )
        force_authenticate(request, user=self.company_admin)

        response = AgencyJobAssignRecruiterView.as_view()(request, pk=self.assignment.id)
        self.assertEqual(response.status_code, 403)

    def test_cannot_reactivate_unauthorized_relationship(self):
        request = self.factory.post(
            f'/api/v1/agencies/company-agency/{self.relationship.id}/reactivate/',
            {},
            format='json',
        )
        force_authenticate(request, user=self.other_company_admin)

        response = AgencyRelationshipReactivateView.as_view()(request, pk=self.relationship.id)
        self.assertEqual(response.status_code, 404)
