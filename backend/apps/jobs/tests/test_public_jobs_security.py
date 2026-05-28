import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.jobs.models import JobPosting, JobRequisition
from apps.jobs.views import JobPublicDetailView, JobSearchView


class PublicJobsSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()

    def test_public_job_search_redacts_internal_posting_fields(self):
        req = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Public Frontend Engineer',
            status='active',
            is_deleted=False,
        )
        posting = JobPosting.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=req.id,
            title='Frontend Engineer',
            description_html='React role',
            is_active=True,
            is_deleted=False,
            metadata={'internal_note': 'do not expose'},
        )

        request = self.factory.get('/api/v1/jobs/search/?search=frontend')
        response = JobSearchView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        jobs = response.data['data']['jobs']
        self.assertEqual({row['id'] for row in jobs}, {str(posting.id)})
        public_post = jobs[0]
        self.assertNotIn('tenant_id', public_post)
        self.assertNotIn('requisition_id', public_post)
        self.assertNotIn('metadata', public_post)
        self.assertNotIn('custom_application_form', public_post)
        self.assertNotIn('views_count', public_post)

    def test_public_job_detail_redacts_internal_requisition_fields(self):
        req = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Security Engineer',
            status='active',
            is_deleted=False,
            salary_visible=False,
            salary_min='100000.00',
            salary_max='200000.00',
            budget_code='INTERNAL-ONLY',
            recruiter_id=uuid.uuid4(),
        )
        posting = JobPosting.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=req.id,
            title='Security Engineer Posting',
            description_html='Security role',
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
