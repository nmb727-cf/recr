import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.candidates.views import (
    CandidateListView,
    CandidateDatabaseView,
    CandidateSavedViewsView,
    CandidateWorkflowPolicyView,
)


class CandidatesSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.candidate_user = CustomUser.objects.create_user(
            email='candidate-security@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )
        self.candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            user_id=self.candidate_user.id,
            first_name='Candidate',
            last_name='Security',
            email=self.candidate_user.email,
        )

    def test_candidate_cannot_access_internal_candidate_operations(self):
        cases = [
            (CandidateListView.as_view(), '/api/v1/candidates/'),
            (CandidateDatabaseView.as_view(), '/api/v1/candidates/database/'),
            (CandidateSavedViewsView.as_view(), '/api/v1/candidates/database/saved-views/'),
            (CandidateWorkflowPolicyView.as_view(), '/api/v1/candidates/workflow-policy/'),
        ]
        for view, path in cases:
            with self.subTest(path=path):
                request = self.factory.get(path)
                force_authenticate(request, user=self.candidate_user)
                response = view(request)
                self.assertEqual(response.status_code, 403)
