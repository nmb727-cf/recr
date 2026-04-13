import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.agencies.models import AgencyClientRelationship, AgencyJobAssignment
from apps.agencies.views import AgencyIntelligenceDashboardView, JobAgencyIntelligenceView
from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application


class AgencyIntelligenceViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.agency_one = uuid.uuid4()
        self.agency_two = uuid.uuid4()
        self.job = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Enterprise AE',
            department_id=uuid.uuid4(),
            work_mode='remote',
            job_category='sales',
            status='active',
        )
        self.manager = CustomUser.objects.create_user(
            email='manager@example.com',
            password='testpass123',
            role='hr_manager',
            tenant_id=self.tenant_id,
        )
        self.recruiter = CustomUser.objects.create_user(
            email='recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )
        self.candidate = CustomUser.objects.create_user(
            email='candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )

        AgencyClientRelationship.objects.create(
            tenant_id=self.tenant_id,
            company_tenant_id=self.tenant_id,
            agency_tenant_id=self.agency_one,
            status='active',
            tier='preferred',
            created_by=self.manager.id,
        )
        AgencyClientRelationship.objects.create(
            tenant_id=self.tenant_id,
            company_tenant_id=self.tenant_id,
            agency_tenant_id=self.agency_two,
            status='active',
            tier='standard',
            created_by=self.manager.id,
        )
        AgencyJobAssignment.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
            agency_tenant_id=self.agency_one,
            assigned_by=self.manager.id,
            created_by=self.manager.id,
            submission_count=2,
            status='active',
        )

        Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=uuid.uuid4(),
            requisition_id=self.job.id,
            agency_id=self.agency_one,
            is_agency_submission=True,
            source='agency',
            status='joined',
            match_score=88,
        )
        Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=uuid.uuid4(),
            requisition_id=self.job.id,
            agency_id=self.agency_one,
            is_agency_submission=True,
            source='agency',
            status='shortlisted',
            match_score=76,
        )
        Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=uuid.uuid4(),
            requisition_id=self.job.id,
            agency_id=self.agency_two,
            is_agency_submission=True,
            source='agency',
            status='applied',
            match_score=55,
        )
        Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=uuid.uuid4(),
            requisition_id=self.job.id,
            is_agency_submission=False,
            source='direct',
            status='applied',
            match_score=62,
        )

    def test_dashboard_returns_agency_intelligence_sections(self):
        request = self.factory.get('/api/v1/agencies/intelligence/dashboard/')
        force_authenticate(request, user=self.manager)

        response = AgencyIntelligenceDashboardView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        intelligence = response.data['data']['intelligence']
        self.assertIn('overview', intelligence)
        self.assertIn('performance', intelligence)
        self.assertIn('distribution', intelligence)
        self.assertIn('risks', intelligence)
        self.assertIn('comparison', intelligence)
        self.assertIn('pipeline', intelligence)
        self.assertGreaterEqual(intelligence['overview']['connected_agencies'], 2)

    def test_job_intelligence_returns_assigned_recommended_and_source_sections(self):
        request = self.factory.get(f'/api/v1/agencies/jobs/{self.job.id}/intelligence/')
        force_authenticate(request, user=self.recruiter)

        response = JobAgencyIntelligenceView.as_view()(request, requisition_id=self.job.id)

        self.assertEqual(response.status_code, 200)
        payload = response.data['data']
        self.assertIn('assigned_agencies', payload)
        self.assertIn('recommended_agencies', payload)
        self.assertIn('underperforming_agencies', payload)
        self.assertIn('inactive_agencies', payload)
        self.assertIn('source_intelligence', payload)
        self.assertGreaterEqual(len(payload['assigned_agencies']), 1)
        self.assertGreaterEqual(payload['source_intelligence']['agency_submissions'], 1)

    def test_dashboard_rbac_blocks_candidate(self):
        request = self.factory.get('/api/v1/agencies/intelligence/dashboard/')
        force_authenticate(request, user=self.candidate)

        response = AgencyIntelligenceDashboardView.as_view()(request)

        self.assertEqual(response.status_code, 403)
