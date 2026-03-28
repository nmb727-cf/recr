import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.interviews.models import Interview, InterviewDecision, InterviewDecisionHistory, InterviewFeedback, InterviewPanelist
from apps.interviews.views import InterviewDecisionEvaluateView, InterviewDecisionHistoryView, InterviewDecisionView
from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application


class InterviewDecisionEngineTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()

        self.recruiter = CustomUser.objects.create_user(
            email='decision-recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )
        self.hiring_manager = CustomUser.objects.create_user(
            email='decision-hm@example.com',
            password='testpass123',
            role='hiring_manager',
            tenant_id=self.tenant_id,
        )
        self.panel1 = CustomUser.objects.create_user(
            email='decision-panel1@example.com',
            password='testpass123',
            role='interviewer',
            tenant_id=self.tenant_id,
        )
        self.panel2 = CustomUser.objects.create_user(
            email='decision-panel2@example.com',
            password='testpass123',
            role='interviewer',
            tenant_id=self.tenant_id,
        )

        self.candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            first_name='Decision',
            last_name='Candidate',
            email='decision-candidate@example.com',
            source='company',
        )
        self.job = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Decision Engineer',
            status='active',
        )
        self.application = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            requisition_id=self.job.id,
            status='interview',
            source='internal',
        )
        self.interview = Interview.objects.create(
            tenant_id=self.tenant_id,
            application_id=self.application.id,
            candidate_id=self.candidate.id,
            requisition_id=self.job.id,
            interview_type='technical_interview',
            status='completed',
            duration_minutes=60,
            scheduled_at=timezone.now() - timedelta(days=1),
            completed_at=timezone.now(),
            created_by=self.recruiter.id,
        )

        self.permission_patch = patch('apps.rbac.permissions.user_has_all_permissions', return_value=True)
        self.permission_patch.start()
        self.addCleanup(self.permission_patch.stop)

    def test_decision_create_works(self):
        request = self.factory.post(
            f'/api/v1/interviews/{self.interview.id}/decision/',
            {
                'decision': 'next_round',
                'decision_source': 'scorecard',
                'decision_mode': 'manual',
                'notes': 'Strong scorecard and feedback alignment',
            },
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        response = InterviewDecisionView.as_view()(request, pk=self.interview.id)
        self.assertEqual(response.status_code, 200)

        decision = InterviewDecision.objects.get(interview_id=self.interview.id)
        self.assertEqual(decision.decision, 'next_round')
        self.assertEqual(decision.decision_source, 'scorecard')

    def test_override_works_and_history_created(self):
        create = self.factory.post(
            f'/api/v1/interviews/{self.interview.id}/decision/',
            {'decision': 'next_round', 'decision_source': 'automation_rules', 'decision_mode': 'auto'},
            format='json',
        )
        force_authenticate(create, user=self.recruiter)
        first = InterviewDecisionView.as_view()(create, pk=self.interview.id)
        self.assertEqual(first.status_code, 200)

        override = self.factory.post(
            f'/api/v1/interviews/{self.interview.id}/decision/',
            {
                'decision': 'hold',
                'decision_source': 'manual',
                'decision_mode': 'manual',
                'is_override': True,
                'override_reason': 'Hiring manager requested additional calibration',
                'notes': 'Override after manager review',
            },
            format='json',
        )
        force_authenticate(override, user=self.hiring_manager)
        second = InterviewDecisionView.as_view()(override, pk=self.interview.id)
        self.assertEqual(second.status_code, 200)

        obj = InterviewDecision.objects.get(interview_id=self.interview.id)
        self.assertEqual(obj.decision, 'hold')
        self.assertTrue(obj.is_override)
        self.assertEqual(obj.previous_decision, 'next_round')

        history_count = InterviewDecisionHistory.objects.filter(interview_id=self.interview.id).count()
        self.assertGreaterEqual(history_count, 2)

    def test_history_endpoint_works(self):
        for choice in ['next_round', 'manual_review']:
            req = self.factory.post(
                f'/api/v1/interviews/{self.interview.id}/decision/',
                {'decision': choice, 'decision_source': 'manual', 'decision_mode': 'manual'},
                format='json',
            )
            force_authenticate(req, user=self.recruiter)
            InterviewDecisionView.as_view()(req, pk=self.interview.id)

        history_req = self.factory.get(f'/api/v1/interviews/{self.interview.id}/decision/history/')
        force_authenticate(history_req, user=self.recruiter)
        history_res = InterviewDecisionHistoryView.as_view()(history_req, pk=self.interview.id)
        self.assertEqual(history_res.status_code, 200)
        self.assertGreaterEqual(history_res.data['meta']['total'], 2)

    def test_multi_interviewer_evaluation_works(self):
        InterviewPanelist.objects.create(
            tenant_id=self.tenant_id,
            interview_id=self.interview.id,
            interviewer_id=self.panel1.id,
            role='lead',
        )
        InterviewPanelist.objects.create(
            tenant_id=self.tenant_id,
            interview_id=self.interview.id,
            interviewer_id=self.panel2.id,
            role='panelist',
        )
        InterviewFeedback.objects.create(
            tenant_id=self.tenant_id,
            interview_id=self.interview.id,
            panelist_id=self.panel1.id,
            score=82,
            recommendation='next_round',
        )
        InterviewFeedback.objects.create(
            tenant_id=self.tenant_id,
            interview_id=self.interview.id,
            panelist_id=self.panel2.id,
            score=78,
            recommendation='hire',
        )

        evaluate_req = self.factory.post(
            f'/api/v1/interviews/{self.interview.id}/decision/evaluate/',
            {
                'persist': True,
                'thresholds': {'next_round_min': 80, 'reject_max': 50},
                'source_inputs': {'score': 81},
                'notes': 'Auto conditional evaluation',
            },
            format='json',
        )
        force_authenticate(evaluate_req, user=self.recruiter)
        evaluate_res = InterviewDecisionEvaluateView.as_view()(evaluate_req, pk=self.interview.id)
        self.assertEqual(evaluate_res.status_code, 200)
        self.assertIn(evaluate_res.data['data']['evaluation']['decision'], {'next_round', 'hire'})

    def test_no_backend_500_on_invalid_interview(self):
        bad_id = uuid.uuid4()
        req = self.factory.post(
            f'/api/v1/interviews/{bad_id}/decision/evaluate/',
            {'persist': False},
            format='json',
        )
        force_authenticate(req, user=self.recruiter)
        res = InterviewDecisionEvaluateView.as_view()(req, pk=bad_id)
        self.assertEqual(res.status_code, 404)
