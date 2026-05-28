from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch

from apps.accounts.models import CustomUser
from apps.agencies.models import AgencyClientRelationship
from apps.candidates.models import Candidate
from apps.candidates.views import CandidateListView
from apps.jobs.models import JobPosting, JobRequisition
from apps.jobs.views import JobRequisitionListView, JobSearchView, JobPublicDetailView
from apps.organisations.views import GlobalSearchView
from apps.tenants.models import Client


class SearchReliabilityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission_patch = patch('apps.rbac.permissions.user_has_all_permissions', return_value=True)
        self.permission_patch.start()
        self.addCleanup(self.permission_patch.stop)
        self.tenant_a = Client.objects.create(
            schema_name='company_search_a',
            name='Company Search A',
            slug='company-search-a',
            tenant_type='company',
            status='active',
        )
        self.tenant_b = Client.objects.create(
            schema_name='company_search_b',
            name='Company Search B',
            slug='company-search-b',
            tenant_type='company',
            status='active',
        )
        self.user_a = CustomUser.objects.create_user(
            email='search-admin-a@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_a.id,
        )

    def _authed_request(self, method: str, path: str):
        request = getattr(self.factory, method)(path)
        force_authenticate(request, user=self.user_a)
        return request

    def test_1_candidate_search_returns_only_allowed_tenant_visible_records(self):
        visible = Candidate.objects.create(
            first_name='Alex',
            last_name='Visible',
            email='alex.visible@example.com',
            tenant_id=self.tenant_a.id,
            source='company',
            source_type='direct',
        )
        Candidate.objects.create(
            first_name='Alex',
            last_name='Hidden',
            email='alex.hidden@example.com',
            tenant_id=self.tenant_b.id,
            source='company',
            source_type='direct',
        )

        request = self._authed_request('get', '/api/v1/candidates/?search=alex')
        response = CandidateListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        ids = {row['id'] for row in response.data['data']['candidates']}
        self.assertIn(str(visible.id), ids)
        self.assertEqual(len(ids), 1)

    def test_2_job_search_returns_correct_matches_for_tenant(self):
        match = JobRequisition.objects.create(
            tenant_id=self.tenant_a.id,
            title='Python Backend Engineer',
            status='active',
            is_deleted=False,
        )
        JobRequisition.objects.create(
            tenant_id=self.tenant_a.id,
            title='Sales Manager',
            status='active',
            is_deleted=False,
        )
        JobRequisition.objects.create(
            tenant_id=self.tenant_b.id,
            title='Python Data Engineer',
            status='active',
            is_deleted=False,
        )

        request = self._authed_request('get', '/api/v1/jobs/requisitions/?search=python')
        response = JobRequisitionListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        ids = {row['id'] for row in response.data['data']['requisitions']}
        self.assertEqual(ids, {str(match.id)})

    def test_3_public_job_search_only_returns_public_active_postings(self):
        req_active = JobRequisition.objects.create(
            tenant_id=self.tenant_a.id,
            title='Frontend Engineer',
            status='active',
            is_deleted=False,
        )
        req_draft = JobRequisition.objects.create(
            tenant_id=self.tenant_a.id,
            title='Draft Role',
            status='draft',
            is_deleted=False,
        )
        good = JobPosting.objects.create(
            tenant_id=self.tenant_a.id,
            requisition_id=req_active.id,
            title='Frontend Engineer',
            description_html='React and TypeScript role',
            is_active=True,
            is_deleted=False,
        )
        JobPosting.objects.create(
            tenant_id=self.tenant_a.id,
            requisition_id=req_draft.id,
            title='Draft Public Posting',
            description_html='Should not be public',
            is_active=True,
            is_deleted=False,
        )
        JobPosting.objects.create(
            tenant_id=self.tenant_a.id,
            requisition_id=req_active.id,
            title='Inactive Posting',
            description_html='Should not show',
            is_active=False,
            is_deleted=False,
        )

        request = self.factory.get('/api/v1/jobs/search/?search=engineer')
        response = JobSearchView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        jobs = response.data['data']['jobs']
        ids = {row['id'] for row in jobs}
        self.assertEqual(ids, {str(good.id)})
        self.assertNotIn('tenant_id', jobs[0])
        self.assertNotIn('requisition_id', jobs[0])
        self.assertNotIn('metadata', jobs[0])
        self.assertNotIn('custom_application_form', jobs[0])
        self.assertNotIn('views_count', jobs[0])

    def test_3b_public_job_detail_hides_internal_requisition_fields(self):
        req = JobRequisition.objects.create(
            tenant_id=self.tenant_a.id,
            title='Security Engineer',
            status='active',
            is_deleted=False,
            salary_visible=False,
            budget_code='INTERNAL-BUDGET-1',
            recruiter_id=self.user_a.id,
        )
        posting = JobPosting.objects.create(
            tenant_id=self.tenant_a.id,
            requisition_id=req.id,
            title='Security Engineer Posting',
            description_html='Role description',
            is_active=True,
            is_deleted=False,
        )
        request = self.factory.get(f'/api/v1/jobs/public/{posting.id}/')
        response = JobPublicDetailView.as_view()(request, pk=posting.id)
        self.assertEqual(response.status_code, 200)
        posting_data = response.data['data']['posting']
        requisition_data = response.data['data']['requisition']
        self.assertNotIn('tenant_id', posting_data)
        self.assertNotIn('requisition_id', posting_data)
        self.assertNotIn('metadata', posting_data)
        self.assertIsNone(requisition_data['salary_min'])
        self.assertIsNone(requisition_data['salary_max'])
        self.assertNotIn('budget_code', requisition_data)
        self.assertNotIn('recruiter_id', requisition_data)

    def test_4_scope_widening_query_param_is_rejected(self):
        request = self._authed_request('get', '/api/v1/candidates/?tenant_id=11111111-1111-1111-1111-111111111111')
        response = CandidateListView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Scope widening', response.data['message'])

    def test_5_typo_tolerance_baseline_matches_relaxed_query(self):
        candidate = Candidate.objects.create(
            first_name='Nina',
            last_name='Developer',
            email='nina.dev@example.com',
            tenant_id=self.tenant_a.id,
            source='company',
            source_type='direct',
        )

        request = self._authed_request('get', '/api/v1/candidates/?search=develper')
        response = CandidateListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        ids = {row['id'] for row in response.data['data']['candidates']}
        self.assertIn(str(candidate.id), ids)
        self.assertIn(response.data['meta']['search_mode'], {'strict', 'relaxed'})

    def test_6_global_search_returns_expected_sections(self):
        Candidate.objects.create(
            first_name='Priya',
            last_name='Platform',
            email='priya.platform@example.com',
            current_title='Platform Engineer',
            tenant_id=self.tenant_a.id,
            source='company',
            source_type='direct',
        )
        JobRequisition.objects.create(
            tenant_id=self.tenant_a.id,
            title='Platform Architect',
            status='active',
            is_deleted=False,
        )
        AgencyClientRelationship.objects.create(
            tenant_id=self.tenant_a.id,
            company_tenant_id=self.tenant_a.id,
            agency_tenant_id=self.tenant_b.id,
            contact_person_name='Platform Partners',
            contact_email='partners@example.com',
            status='active',
            invited_by='company',
        )

        request = self._authed_request('get', '/api/v1/organisations/search/?q=platform')
        response = GlobalSearchView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['data']['candidates']), 1)
        self.assertGreaterEqual(len(response.data['data']['jobs']), 1)
        self.assertGreaterEqual(len(response.data['data']['agencies']), 1)

    def test_7_search_pagination_and_filters_are_stable(self):
        Candidate.objects.create(
            first_name='Alexa',
            last_name='One',
            email='alexa.one@example.com',
            tenant_id=self.tenant_a.id,
            source='company',
            source_type='direct',
        )
        second = Candidate.objects.create(
            first_name='Alexb',
            last_name='Two',
            email='alexb.two@example.com',
            tenant_id=self.tenant_a.id,
            source='company',
            source_type='direct',
        )

        request = self._authed_request(
            'get',
            '/api/v1/candidates/?search=alex&sort_by=first_name&sort_dir=asc&limit=1&offset=1',
        )
        response = CandidateListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        rows = response.data['data']['candidates']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['id'], str(second.id))
        self.assertEqual(response.data['meta']['limit'], 1)
        self.assertEqual(response.data['meta']['offset'], 1)
