import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.agencies.models import AgencyClientRelationship, AgencyJobAssignment
from apps.agencies.views import (
    AgencyPerformanceListView,
    AgencyJobAssignRecruiterView,
    AgencyRelationshipReactivateView,
    AgencyRelationshipListView,
    TenantLookupView,
    AvailableAgencyListView,
    AgencyMyJobsView,
    AgencyMySubmissionsView,
    AgencyMyClientsView,
    AgencySubmitCandidateView,
    GuestPortalCreateView,
    EmailTrackingCreateView,
    OfflineClientCreateView,
    GuestPortalResendInviteView,
)
from apps.organisations.models import Organisation


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
        self.candidate_user = CustomUser.objects.create_user(
            email='candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=uuid.uuid4(),
        )

        Organisation.objects.create(
            tenant_id=self.company_tenant,
            name='Company One',
            org_type='company',
            created_by=self.company_admin.id,
        )
        Organisation.objects.create(
            tenant_id=self.agency_tenant,
            name='Agency One',
            org_type='agency',
            created_by=self.agency_user.id,
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

    def test_candidate_cannot_use_lookup_or_available_discovery_endpoints(self):
        lookup = self.factory.get('/api/v1/agencies/lookup/?q=agency-user@example.com')
        force_authenticate(lookup, user=self.candidate_user)
        lookup_response = TenantLookupView.as_view()(lookup)
        self.assertEqual(lookup_response.status_code, 403)

        available = self.factory.get('/api/v1/agencies/available/')
        force_authenticate(available, user=self.candidate_user)
        available_response = AvailableAgencyListView.as_view()(available)
        self.assertEqual(available_response.status_code, 403)

    def test_company_user_can_access_available_discovery_endpoint(self):
        request = self.factory.get('/api/v1/agencies/available/')
        force_authenticate(request, user=self.company_admin)
        response = AvailableAgencyListView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_company_lookup_only_resolves_agency_entities(self):
        company_lookup = self.factory.get('/api/v1/agencies/lookup/?q=other-company-admin@example.com')
        force_authenticate(company_lookup, user=self.company_admin)
        company_lookup_response = TenantLookupView.as_view()(company_lookup)
        self.assertEqual(company_lookup_response.status_code, 200)
        self.assertFalse(company_lookup_response.data['data']['found'])

        agency_lookup = self.factory.get('/api/v1/agencies/lookup/?q=agency-user@example.com')
        force_authenticate(agency_lookup, user=self.company_admin)
        agency_lookup_response = TenantLookupView.as_view()(agency_lookup)
        self.assertEqual(agency_lookup_response.status_code, 200)
        self.assertTrue(agency_lookup_response.data['data']['found'])
        self.assertEqual(agency_lookup_response.data['data']['tenant_type'], 'agency')

    def test_candidate_cannot_access_agency_operational_endpoints(self):
        req_jobs = self.factory.get('/api/v1/agencies/my-jobs/')
        force_authenticate(req_jobs, user=self.candidate_user)
        self.assertEqual(AgencyMyJobsView.as_view()(req_jobs).status_code, 403)

        req_submissions = self.factory.get('/api/v1/agencies/my-submissions/')
        force_authenticate(req_submissions, user=self.candidate_user)
        self.assertEqual(AgencyMySubmissionsView.as_view()(req_submissions).status_code, 403)

        req_clients = self.factory.get('/api/v1/agencies/my-clients/')
        force_authenticate(req_clients, user=self.candidate_user)
        self.assertEqual(AgencyMyClientsView.as_view()(req_clients).status_code, 403)

        req_submit = self.factory.post('/api/v1/agencies/submit-candidate/', {}, format='json')
        force_authenticate(req_submit, user=self.candidate_user)
        self.assertEqual(AgencySubmitCandidateView.as_view()(req_submit).status_code, 403)

    def test_candidate_cannot_manage_guest_portals_or_offline_tracking(self):
        req_portal = self.factory.post(
            '/api/v1/agencies/guest-portals/',
            {'portal_type': 'agency_guest', 'name': 'Demo', 'contact_email': 'demo@example.com'},
            format='json',
        )
        force_authenticate(req_portal, user=self.candidate_user)
        self.assertEqual(GuestPortalCreateView.as_view()(req_portal).status_code, 403)

        req_email_tracking = self.factory.post(
            '/api/v1/agencies/email-tracking/',
            {'client_name': 'Demo', 'contact_email': 'demo@example.com'},
            format='json',
        )
        force_authenticate(req_email_tracking, user=self.candidate_user)
        self.assertEqual(EmailTrackingCreateView.as_view()(req_email_tracking).status_code, 403)

        req_offline = self.factory.post(
            '/api/v1/agencies/offline-clients/',
            {'client_name': 'Demo'},
            format='json',
        )
        force_authenticate(req_offline, user=self.candidate_user)
        self.assertEqual(OfflineClientCreateView.as_view()(req_offline).status_code, 403)

        random_pk = uuid.uuid4()
        req_resend = self.factory.post('/api/v1/agencies/guest-portals/{}/resend/'.format(random_pk), {}, format='json')
        force_authenticate(req_resend, user=self.candidate_user)
        self.assertEqual(GuestPortalResendInviteView.as_view()(req_resend, pk=random_pk).status_code, 403)

    def test_portal_type_alignment_is_enforced_for_company_and_agency(self):
        company_bad = self.factory.post(
            '/api/v1/agencies/guest-portals/',
            {'portal_type': 'client_guest', 'name': 'Wrong', 'contact_email': 'wrong@example.com'},
            format='json',
        )
        force_authenticate(company_bad, user=self.company_admin)
        self.assertEqual(GuestPortalCreateView.as_view()(company_bad).status_code, 403)

        agency_bad = self.factory.post(
            '/api/v1/agencies/guest-portals/',
            {'portal_type': 'agency_guest', 'name': 'Wrong', 'contact_email': 'wrong@example.com'},
            format='json',
        )
        force_authenticate(agency_bad, user=self.agency_user)
        self.assertEqual(GuestPortalCreateView.as_view()(agency_bad).status_code, 403)

    def test_recruiter_without_relationship_manage_permission_is_denied(self):
        request = self.factory.post(
            '/api/v1/agencies/company-agency/',
            {
                'agency_tenant_id': str(self.agency_tenant),
                'company_tenant_id': str(self.company_tenant),
                'invited_via': 'agency-user@example.com',
            },
            format='json',
        )
        recruiter = CustomUser.objects.create_user(
            email='company-recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.company_tenant,
        )
        force_authenticate(request, user=recruiter)
        with patch('apps.rbac.utils.user_has_permission', return_value=False):
            response = AgencyRelationshipListView.as_view()(request)
        self.assertEqual(response.status_code, 403)
