import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.jobs.views import (
    CandidateApplicationListView,
    CandidateApplicationDetailView,
    RecommendedJobsView,
    JobApplyView,
)


class CandidateEndpointSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.recruiter = CustomUser.objects.create_user(
            email='recruiter-no-candidate-route@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )

    def test_non_candidate_user_cannot_access_candidate_endpoints(self):
        app_id = uuid.uuid4()
        cases = [
            (CandidateApplicationListView.as_view(), '/api/v1/candidate/applications/', {}),
            (CandidateApplicationDetailView.as_view(), f'/api/v1/candidate/applications/{app_id}/', {'pk': app_id}),
            (RecommendedJobsView.as_view(), '/api/v1/candidate/recommended-jobs/', {}),
        ]
        for view, path, kwargs in cases:
            with self.subTest(path=path):
                request = self.factory.get(path)
                force_authenticate(request, user=self.recruiter)
                response = view(request, **kwargs)
                self.assertEqual(response.status_code, 403)

    def test_non_candidate_user_cannot_apply_to_job(self):
        posting_id = uuid.uuid4()
        request = self.factory.post(
            f'/api/v1/jobs/{posting_id}/apply/',
            {'cover_note': 'test'},
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        response = JobApplyView.as_view()(request, pk=posting_id)
        self.assertEqual(response.status_code, 403)
