import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.analytics.intelligence_substrate import IntelligenceAggregator, IntelligenceEventTriggers
from apps.analytics.views import IntelligenceCandidateView, IntelligenceJobView, IntelligencePipelineView
from apps.candidates.models import Candidate
from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application


class IntelligenceSubstrateTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.other_tenant_id = uuid.uuid4()

        self.user = CustomUser.objects.create_user(
            email='intel-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_id,
        )
        self.other_user = CustomUser.objects.create_user(
            email='intel-admin-other@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.other_tenant_id,
        )

        self.job = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Platform Engineer',
            status='active',
            headcount=2,
            is_deleted=False,
            recruiter_id=self.user.id,
            job_ref_id=f"SYS-CJ-INTEL-{uuid.uuid4().hex[:8]}",
        )
        self.candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            first_name='Nina',
            last_name='Signals',
            email='nina.signals@example.com',
            candidate_ref_id=f"SYS-CC-INTEL-{uuid.uuid4().hex[:8]}",
            is_actively_looking=True,
            fit_score=83,
            source='company',
            source_type='direct',
        )
        self.app = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            requisition_id=self.job.id,
            status='screening',
            created_by=self.user.id,
            match_score=81,
        )

    def test_1_intelligence_computed_after_event(self):
        first = IntelligenceAggregator.build_job_intelligence(
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
        )
        first_computed = first['computed_at']

        IntelligenceEventTriggers.handle_domain_event(
            event_name='application.stage_changed',
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
            candidate_id=self.candidate.id,
        )

        second = IntelligenceAggregator.build_job_intelligence(
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
        )
        self.assertNotEqual(first_computed, second['computed_at'])

    def test_2_cache_invalidation_works(self):
        first = IntelligenceAggregator.build_pipeline_intelligence(
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
        )
        second = IntelligenceAggregator.build_pipeline_intelligence(
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
        )
        self.assertEqual(first['computed_at'], second['computed_at'])

        IntelligenceEventTriggers.handle_domain_event(
            event_name='application.created',
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
            candidate_id=self.candidate.id,
        )
        third = IntelligenceAggregator.build_pipeline_intelligence(
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
        )
        self.assertNotEqual(second['computed_at'], third['computed_at'])

    def test_3_tenant_isolation_enforced(self):
        other_job = JobRequisition.objects.create(
            tenant_id=self.other_tenant_id,
            title='Other Tenant Job',
            status='active',
            is_deleted=False,
            job_ref_id=f"SYS-CJ-INTEL-{uuid.uuid4().hex[:8]}",
        )
        JobRequisition.objects.create(
            tenant_id=self.other_tenant_id,
            title='Other Tenant Job 2',
            status='active',
            is_deleted=False,
            job_ref_id=f"SYS-CJ-INTEL-{uuid.uuid4().hex[:8]}",
        )
        other_candidate = Candidate.objects.create(
            tenant_id=self.other_tenant_id,
            first_name='Other',
            last_name='Candidate',
            email='other.candidate@example.com',
            candidate_ref_id=f"SYS-CC-INTEL-{uuid.uuid4().hex[:8]}",
            source='company',
            source_type='direct',
        )
        Application.objects.create(
            tenant_id=self.other_tenant_id,
            candidate_id=other_candidate.id,
            requisition_id=other_job.id,
            status='applied',
        )

        t1 = IntelligenceAggregator.build_global_intelligence(tenant_id=self.tenant_id, force_refresh=True)
        t2 = IntelligenceAggregator.build_global_intelligence(tenant_id=self.other_tenant_id, force_refresh=True)
        self.assertNotEqual(t1['signals']['system']['active_jobs'], t2['signals']['system']['active_jobs'])

    def test_4_job_intelligence_returns_expected_signals(self):
        request = self.factory.get(f'/api/v1/analytics/intelligence/jobs/{self.job.id}/')
        force_authenticate(request, user=self.user)
        response = IntelligenceJobView.as_view()(request, job_id=self.job.id)

        self.assertEqual(response.status_code, 200)
        signals = response.data['data']['intelligence']['signals']
        self.assertIn('application_rate', signals)
        self.assertIn('stage_bottlenecks', signals)

    def test_5_candidate_intelligence_returns_expected_signals(self):
        request = self.factory.get(f'/api/v1/analytics/intelligence/candidates/{self.candidate.id}/')
        force_authenticate(request, user=self.user)
        response = IntelligenceCandidateView.as_view()(request, candidate_id=self.candidate.id)

        self.assertEqual(response.status_code, 200)
        signals = response.data['data']['intelligence']['signals']
        self.assertIn('engagement_signals', signals)
        self.assertIn('skill_match_signals', signals)

    def test_6_pipeline_intelligence_works(self):
        request = self.factory.get(f'/api/v1/analytics/intelligence/pipeline/?requisition_id={self.job.id}')
        force_authenticate(request, user=self.user)
        response = IntelligencePipelineView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        signals = response.data['data']['intelligence']['signals']
        self.assertIn('drop_rate', signals)
        self.assertIn('conversion_rate', signals)
