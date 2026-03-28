from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.interviews.models import Interview
from apps.interviews.views import (
    CandidateInterviewListView,
    CandidateInterviewRuntimeView,
    CandidateInterviewStartView,
    CandidateCompleteInterviewView,
)


class InterviewSecurityEngineTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.candidate = CustomUser.objects.create_user(
            email='candidate-security@example.com',
            password='testpass123',
            role='candidate',
            tenant_id='00000000-0000-0000-0000-000000000001',
        )
        self.interview = Interview.objects.create(
            tenant_id=self.candidate.tenant_id,
            application_id='00000000-0000-0000-0000-000000000201',
            candidate_id=self.candidate.id,
            requisition_id='00000000-0000-0000-0000-000000000202',
            interview_type='ai_screening',
            status='scheduled',
            title='Security Runtime',
            scheduled_at=timezone.now() + timedelta(minutes=5),
        )
        self.runtime = CandidateInterviewListView()._ensure_runtime_shell(self.interview)
        self.token = self.runtime['token']

    def test_token_validation_works(self):
        req = self.factory.get(f'/api/v1/candidate/interviews/{self.interview.id}/runtime/?access_token=wrong&session_id=s1')
        force_authenticate(req, user=self.candidate)
        res = CandidateInterviewRuntimeView.as_view()(req, pk=self.interview.id)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data.get('errors', {}).get('code'), 'token_invalid')

    def test_expiry_works(self):
        md = self.interview.metadata or {}
        runtime = md.get('candidate_runtime_access') or {}
        runtime['token_expires_at'] = (timezone.now() - timedelta(minutes=1)).isoformat()
        md['candidate_runtime_access'] = runtime
        self.interview.metadata = md
        self.interview.save(update_fields=['metadata', 'updated_at'])

        req = self.factory.get(f'/api/v1/candidate/interviews/{self.interview.id}/runtime/?access_token={self.token}&session_id=s1')
        force_authenticate(req, user=self.candidate)
        res = CandidateInterviewRuntimeView.as_view()(req, pk=self.interview.id)
        self.assertEqual(res.status_code, 410)
        self.assertEqual(res.data.get('errors', {}).get('code'), 'token_expired')

    def test_attempt_tracking_works(self):
        start_req = self.factory.post(
            f'/api/v1/candidate/interviews/{self.interview.id}/start/',
            {'access_token': self.token, 'session_id': 'sess-1'},
            format='json',
        )
        force_authenticate(start_req, user=self.candidate)
        start_res = CandidateInterviewStartView.as_view()(start_req, pk=self.interview.id)
        self.assertEqual(start_res.status_code, 200)

        complete_req = self.factory.post(f'/api/v1/candidate/interviews/{self.interview.id}/complete/', {}, format='json')
        force_authenticate(complete_req, user=self.candidate)
        complete_res = CandidateCompleteInterviewView.as_view()(complete_req, pk=self.interview.id)
        self.assertEqual(complete_res.status_code, 200)

        self.interview.refresh_from_db()
        rt = (self.interview.metadata or {}).get('candidate_runtime_access') or {}
        self.assertEqual(rt.get('attempt_status'), 'completed')
        self.assertGreaterEqual(int(rt.get('attempt_duration_seconds') or 0), 0)

    def test_session_lock_works(self):
        start_req = self.factory.post(
            f'/api/v1/candidate/interviews/{self.interview.id}/start/',
            {'access_token': self.token, 'session_id': 'sess-1'},
            format='json',
        )
        force_authenticate(start_req, user=self.candidate)
        start_res = CandidateInterviewStartView.as_view()(start_req, pk=self.interview.id)
        self.assertEqual(start_res.status_code, 200)

        lock_req = self.factory.get(
            f'/api/v1/candidate/interviews/{self.interview.id}/runtime/?access_token={self.token}&session_id=sess-2'
        )
        force_authenticate(lock_req, user=self.candidate)
        lock_res = CandidateInterviewRuntimeView.as_view()(lock_req, pk=self.interview.id)
        self.assertEqual(lock_res.status_code, 409)
        self.assertEqual(lock_res.data.get('errors', {}).get('code'), 'session_locked')
