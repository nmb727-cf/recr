from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.interviews.models import Interview, InterviewQuestion
from apps.interviews.views import (
    CandidateInterviewListView,
    CandidateInterviewInstructionsView,
    CandidateInterviewRuntimeView,
    CandidateInterviewStartView,
    CandidateSubmitAnswerView,
    CandidateCompleteInterviewView,
    CandidateInterviewStatusView,
)


class CandidateRuntimeEngineTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = CustomUser.objects.create_user(
            email='candidate-runtime@example.com',
            password='testpass123',
            role='candidate',
            tenant_id='00000000-0000-0000-0000-000000000001',
        )
        # Interview.candidate_id must be Candidate.id (not User.id).
        self.candidate_record = Candidate.objects.create(
            tenant_id=self.user.tenant_id,
            user_id=self.user.id,
            email=self.user.email,
            first_name='Runtime',
            last_name='Candidate',
            source='self',
        )
        self.interview = Interview.objects.create(
            tenant_id=self.user.tenant_id,
            application_id='00000000-0000-0000-0000-000000000101',
            candidate_id=self.candidate_record.id,
            requisition_id='00000000-0000-0000-0000-000000000102',
            interview_type='ai_screening',
            status='scheduled',
            title='AI Screening Runtime',
        )
        # Keep self.candidate pointing to the user for force_authenticate
        self.candidate = self.user
        self.question = InterviewQuestion.objects.create(
            tenant_id=self.candidate.tenant_id,
            interview_id=self.interview.id,
            question_text='Tell us about yourself.',
            question_type='text',
            order_index=0,
        )
        self.runtime_token = CandidateInterviewListView()._ensure_runtime_shell(self.interview).get('token')

    def test_candidate_dashboard_loads(self):
        req = self.factory.get('/api/v1/candidate/interviews/')
        force_authenticate(req, user=self.candidate)
        res = CandidateInterviewListView.as_view()(req)
        self.assertEqual(res.status_code, 200)
        self.assertIn('upcoming_interviews', res.data['data'])

    def test_interview_opens(self):
        req = self.factory.get(f'/api/v1/candidate/interviews/{self.interview.id}/runtime/?access_token={self.runtime_token}&session_id=s1')
        force_authenticate(req, user=self.candidate)
        res = CandidateInterviewRuntimeView.as_view()(req, pk=self.interview.id)
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.data['data']['questions']), 1)

    def test_join_works_and_status_updates(self):
        ins_req = self.factory.get(f'/api/v1/candidate/interviews/{self.interview.id}/instructions/')
        force_authenticate(ins_req, user=self.candidate)
        ins_res = CandidateInterviewInstructionsView.as_view()(ins_req, pk=self.interview.id)
        self.assertEqual(ins_res.status_code, 200)

        start_req = self.factory.post(
            f'/api/v1/candidate/interviews/{self.interview.id}/start/',
            {'access_token': self.runtime_token, 'session_id': 's1'},
            format='json',
        )
        force_authenticate(start_req, user=self.candidate)
        start_res = CandidateInterviewStartView.as_view()(start_req, pk=self.interview.id)
        self.assertEqual(start_res.status_code, 200)

        ans_req = self.factory.post(
            f'/api/v1/candidate/interviews/{self.interview.id}/submit-answer/',
            {'question_id': str(self.question.id), 'answer_text': 'Answer'},
            format='json',
        )
        force_authenticate(ans_req, user=self.candidate)
        ans_res = CandidateSubmitAnswerView.as_view()(ans_req, pk=self.interview.id)
        self.assertEqual(ans_res.status_code, 200)

        comp_req = self.factory.post(f'/api/v1/candidate/interviews/{self.interview.id}/complete/', {}, format='json')
        force_authenticate(comp_req, user=self.candidate)
        comp_res = CandidateCompleteInterviewView.as_view()(comp_req, pk=self.interview.id)
        self.assertEqual(comp_res.status_code, 200)

        status_req = self.factory.get(f'/api/v1/candidate/interviews/{self.interview.id}/status/')
        force_authenticate(status_req, user=self.candidate)
        status_res = CandidateInterviewStatusView.as_view()(status_req, pk=self.interview.id)
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.data['data']['status'], 'completed')

    def test_no_backend_500(self):
        req = self.factory.get('/api/v1/candidate/interviews/00000000-0000-0000-0000-000000000999/runtime/')
        force_authenticate(req, user=self.candidate)
        res = CandidateInterviewRuntimeView.as_view()(req, pk='00000000-0000-0000-0000-000000000999')
        self.assertEqual(res.status_code, 404)
