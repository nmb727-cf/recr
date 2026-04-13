import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.interviews.models import Interview, InterviewDecision, InterviewFeedback, InterviewPanelist
from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application
from apps.analytics.views import InterviewIntelligenceAnalyticsView


class InterviewAnalyticsEngineTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.user = CustomUser.objects.create_user(
            email='analytics-interview@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_id,
        )
        self.panel_user = CustomUser.objects.create_user(
            email='analytics-panel@example.com',
            password='testpass123',
            role='interviewer',
            tenant_id=self.tenant_id,
        )

        self.job = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Analytics Job',
            status='active',
        )
        self.candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            first_name='Ana',
            last_name='Lytics',
            email='ana@example.com',
            source='company',
        )
        self.app = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            requisition_id=self.job.id,
            status='offer',
            source='internal',
        )
        self.interview = Interview.objects.create(
            tenant_id=self.tenant_id,
            application_id=self.app.id,
            candidate_id=self.candidate.id,
            requisition_id=self.job.id,
            interview_type='technical_interview',
            status='completed',
            scheduled_at=timezone.now() - timedelta(days=2),
            completed_at=timezone.now() - timedelta(days=1),
            duration_minutes=60,
            created_by=self.user.id,
        )
        InterviewPanelist.objects.create(
            tenant_id=self.tenant_id,
            interview_id=self.interview.id,
            interviewer_id=self.panel_user.id,
            role='panelist',
        )
        InterviewFeedback.objects.create(
            tenant_id=self.tenant_id,
            interview_id=self.interview.id,
            panelist_id=self.panel_user.id,
            score=85,
            recommendation='next_round',
        )
        InterviewDecision.objects.create(
            tenant_id=self.tenant_id,
            interview_id=self.interview.id,
            decision='next_round',
            decision_source='interviewer_feedback',
            decision_mode='manual',
            notes='Strong round',
            decided_by=self.user.id,
        )

    def test_dashboard_loads(self):
        request = self.factory.get('/api/v1/analytics/interviews/intelligence/')
        force_authenticate(request, user=self.user)
        response = InterviewIntelligenceAnalyticsView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertIn('funnel', response.data['data'])

    def test_filters_work(self):
        request = self.factory.get('/api/v1/analytics/interviews/intelligence/?interview_type=technical_interview')
        force_authenticate(request, user=self.user)
        response = InterviewIntelligenceAnalyticsView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        type_rows = response.data['data']['interview_type_analytics']
        self.assertTrue(any(r['interview_type'] == 'technical_interview' for r in type_rows))

    def test_no_backend_500(self):
        request = self.factory.get('/api/v1/analytics/interviews/intelligence/?start_date=invalid-date')
        force_authenticate(request, user=self.user)
        response = InterviewIntelligenceAnalyticsView.as_view()(request)
        self.assertNotEqual(response.status_code, 500)
