import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate, CandidateProfile
from apps.interviews.models import (
    Interview,
    InterviewFeedback,
    InterviewQuestion,
    InterviewScorecardTemplate,
)
from apps.interviews.views import (
    InterviewKitView,
    InterviewPanelDecisionView,
    InterviewScorecardTemplateListView,
    InterviewStructuredFeedbackView,
)
from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application


class InterviewScorecardEngineTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()

        self.user1 = CustomUser.objects.create_user(
            email='interviewer1@example.com',
            password='testpass123',
            role='interviewer',
            tenant_id=self.tenant_id,
        )
        self.user2 = CustomUser.objects.create_user(
            email='interviewer2@example.com',
            password='testpass123',
            role='interviewer',
            tenant_id=self.tenant_id,
        )

        # Keep interview fixtures minimal and consistent with existing architecture.
        self.candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            first_name='Isha',
            last_name='Patel',
            email='isha@example.com',
            source='company',
        )
        CandidateProfile.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            cv_url='https://cdn.example.com/resume/isha.pdf',
        )
        self.job = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Senior Backend Engineer',
            status='active',
        )
        self.application = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            requisition_id=self.job.id,
            status='interview',
            source='direct',
        )
        self.interview = Interview.objects.create(
            tenant_id=self.tenant_id,
            application_id=self.application.id,
            candidate_id=self.candidate.id,
            requisition_id=self.job.id,
            interview_type='technical',
            status='scheduled',
        )

        self.permission_patch = patch(
            'apps.rbac.permissions.user_has_all_permissions',
            return_value=True,
        )
        self.permission_patch.start()
        self.addCleanup(self.permission_patch.stop)

    def _post(self, view, path, user, payload):
        request = self.factory.post(path, payload, format='json')
        force_authenticate(request, user=user)
        return view(request, pk=self.interview.id) if '<id>' in path else view(request)

    def _get(self, view, path, user):
        request = self.factory.get(path)
        force_authenticate(request, user=user)
        return view(request, pk=self.interview.id)

    def test_scorecard_template_create_works(self):
        payload = {
            'name': 'Technical Screen Scorecard',
            'description': 'Default technical screen evaluation rubric',
            'interview_type': 'technical',
            'attributes': [
                {
                    'attribute_name': 'Problem Solving',
                    'weight': '40.00',
                    'rating_type': 'scale_1_5',
                    'required': True,
                    'order_index': 1,
                },
                {
                    'attribute_name': 'Communication',
                    'weight': '60.00',
                    'rating_type': 'yes_no',
                    'required': True,
                    'order_index': 2,
                },
            ],
        }

        request = self.factory.post('/api/v1/interviews/scorecards/templates/', payload, format='json')
        force_authenticate(request, user=self.user1)
        response = InterviewScorecardTemplateListView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        scorecard_id = response.data['data']['scorecard']['id']
        scorecard = InterviewScorecardTemplate.objects.get(id=scorecard_id)
        self.assertEqual(scorecard.attributes.count(), 2)

    def test_interview_kit_loads_with_candidate_job_resume_questions_and_scorecard(self):
        scorecard = InterviewScorecardTemplate.objects.create(
            tenant_id=self.tenant_id,
            name='Technical Round Kit',
            interview_type='technical',
            created_by=self.user1.id,
        )
        scorecard.attributes.create(
            tenant_id=self.tenant_id,
            attribute_name='System Design',
            weight='100.00',
            rating_type='scale_1_5',
            required=True,
            order_index=1,
        )
        InterviewQuestion.objects.create(
            tenant_id=self.tenant_id,
            interview_id=self.interview.id,
            question_text='Design a rate limiter.',
            question_type='text',
            order_index=1,
        )
        self.interview.scorecard_template_id = scorecard.id
        self.interview.save(update_fields=['scorecard_template_id'])

        request = self.factory.get(f'/api/v1/interviews/{self.interview.id}/kit/')
        force_authenticate(request, user=self.user1)
        response = InterviewKitView.as_view()(request, pk=self.interview.id)

        self.assertEqual(response.status_code, 200)
        data = response.data['data']
        self.assertEqual(data['candidate']['full_name'], 'Isha Patel')
        self.assertEqual(data['job']['title'], 'Senior Backend Engineer')
        self.assertTrue(data['resume_url'])
        self.assertEqual(len(data['questions']), 1)
        self.assertEqual(data['scorecard']['name'], 'Technical Round Kit')

    def test_feedback_submit_works_and_exposes_panel_decision(self):
        payload = {
            'notes': 'Strong problem decomposition and communication.',
            'recommendation': 'hire',
            'scorecard_ratings': {
                'Problem Solving': 4,
                'Communication': 5,
            },
        }

        request = self.factory.post(
            f'/api/v1/interviews/{self.interview.id}/structured-feedback/',
            payload,
            format='json',
        )
        force_authenticate(request, user=self.user1)
        response = InterviewStructuredFeedbackView.as_view()(request, pk=self.interview.id)

        self.assertEqual(response.status_code, 200)
        feedback = InterviewFeedback.objects.get(interview_id=self.interview.id, panelist_id=self.user1.id)
        self.assertEqual(feedback.recommendation, 'hire')
        self.assertEqual(feedback.scorecard_ratings['Problem Solving'], 4)
        self.assertEqual(response.data['data']['panel_decision']['total_feedback'], 1)

    def test_multi_interviewer_combined_decision_works(self):
        request1 = self.factory.post(
            f'/api/v1/interviews/{self.interview.id}/structured-feedback/',
            {
                'score': 4,
                'notes': 'Good fundamentals',
                'recommendation': 'hire',
            },
            format='json',
        )
        force_authenticate(request1, user=self.user1)
        response1 = InterviewStructuredFeedbackView.as_view()(request1, pk=self.interview.id)
        self.assertEqual(response1.status_code, 200)

        request2 = self.factory.post(
            f'/api/v1/interviews/{self.interview.id}/structured-feedback/',
            {
                'score': 2,
                'notes': 'Not enough depth',
                'recommendation': 'reject',
            },
            format='json',
        )
        force_authenticate(request2, user=self.user2)
        response2 = InterviewStructuredFeedbackView.as_view()(request2, pk=self.interview.id)
        self.assertEqual(response2.status_code, 200)

        panel_request = self.factory.get(f'/api/v1/interviews/{self.interview.id}/panel-decision/')
        force_authenticate(panel_request, user=self.user1)
        panel_response = InterviewPanelDecisionView.as_view()(panel_request, pk=self.interview.id)

        self.assertEqual(panel_response.status_code, 200)
        payload = panel_response.data['data']['panel_decision']
        self.assertEqual(payload['total_feedback'], 2)
        self.assertEqual(payload['recommendation_counts']['hire'], 1)
        self.assertEqual(payload['recommendation_counts']['reject'], 1)
        self.assertEqual(float(payload['average_score']), 3.0)
        self.assertEqual(payload['combined_recommendation'], 'hire')
