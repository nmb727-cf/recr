import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.interviews.views import (
    CandidateInterviewListView,
    CandidateInterviewResultsView,
    CandidateInterviewStartView,
)


class CandidateInterviewEndpointSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.recruiter = CustomUser.objects.create_user(
            email='interview-recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )

    def test_non_candidate_user_blocked_from_candidate_interview_views(self):
        interview_id = uuid.uuid4()
        cases = [
            (self.factory.get('/api/v1/candidate/interviews/'), CandidateInterviewListView.as_view(), {}),
            (self.factory.get('/api/v1/candidate/interviews/results/?interview_id=x'), CandidateInterviewResultsView.as_view(), {}),
            (
                self.factory.post(f'/api/v1/candidate/interviews/{interview_id}/start/', {}, format='json'),
                CandidateInterviewStartView.as_view(),
                {'pk': interview_id},
            ),
        ]
        for request, view, kwargs in cases:
            with self.subTest(view=view.view_class.__name__):
                force_authenticate(request, user=self.recruiter)
                response = view(request, **kwargs)
                self.assertEqual(response.status_code, 403)
