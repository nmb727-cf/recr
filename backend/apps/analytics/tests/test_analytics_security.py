import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.analytics.views import (
    DashboardView,
    PipelineAnalyticsView,
    CandidateAnalyticsView,
    InterviewAnalyticsView,
    IntelligencePipelineView,
    IntelligenceCandidateView,
)


class AnalyticsSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.candidate = CustomUser.objects.create_user(
            email='analytics-candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )
        self.agency_user = CustomUser.objects.create_user(
            email='analytics-agency@example.com',
            password='testpass123',
            role='agency_recruiter',
            tenant_id=self.tenant_id,
        )

    def _assert_forbidden_for_candidate(self, view, path):
        request = self.factory.get(path)
        force_authenticate(request, user=self.candidate)
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_candidate_cannot_access_core_analytics_endpoints(self):
        cases = [
            (DashboardView.as_view(), '/api/v1/analytics/dashboard/'),
            (PipelineAnalyticsView.as_view(), '/api/v1/analytics/pipeline/'),
            (CandidateAnalyticsView.as_view(), '/api/v1/analytics/candidates/'),
            (InterviewAnalyticsView.as_view(), '/api/v1/analytics/interviews/'),
            (IntelligencePipelineView.as_view(), '/api/v1/analytics/intelligence/pipeline/'),
        ]
        for view, path in cases:
            with self.subTest(path=path):
                self._assert_forbidden_for_candidate(view, path)

    def test_agency_user_cannot_access_company_analytics_endpoints(self):
        cases = [
            (DashboardView.as_view(), '/api/v1/analytics/dashboard/', {}),
            (PipelineAnalyticsView.as_view(), '/api/v1/analytics/pipeline/', {}),
            (IntelligencePipelineView.as_view(), '/api/v1/analytics/intelligence/pipeline/', {}),
            (
                IntelligenceCandidateView.as_view(),
                '/api/v1/analytics/intelligence/candidate/00000000-0000-0000-0000-000000000001/',
                {'candidate_id': '00000000-0000-0000-0000-000000000001'},
            ),
        ]
        for view, path, kwargs in cases:
            with self.subTest(path=path):
                request = self.factory.get(path)
                force_authenticate(request, user=self.agency_user)
                response = view(request, **kwargs)
                self.assertEqual(response.status_code, 403)
