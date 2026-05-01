import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.pipeline.views import (
    ApplicationListView,
    ApplicationDetailView,
    PipelineView,
    DeadlineListView,
    OverdueDeadlineView,
)


class PipelineSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.candidate = CustomUser.objects.create_user(
            email='pipeline-candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )

    def _assert_candidate_forbidden(self, response):
        self.assertEqual(response.status_code, 403)

    def test_candidate_cannot_access_pipeline_endpoints(self):
        req_id = uuid.uuid4()
        app_id = uuid.uuid4()
        cases = [
            (self.factory.get('/api/v1/pipeline/applications/'), ApplicationListView.as_view(), {}),
            (self.factory.get(f'/api/v1/pipeline/applications/{app_id}/'), ApplicationDetailView.as_view(), {'pk': app_id}),
            (self.factory.get(f'/api/v1/pipeline/{req_id}/'), PipelineView.as_view(), {'requisition_id': req_id}),
            (self.factory.get('/api/v1/pipeline/deadlines/'), DeadlineListView.as_view(), {}),
            (self.factory.get('/api/v1/pipeline/deadlines/overdue/'), OverdueDeadlineView.as_view(), {}),
        ]
        for request, view, kwargs in cases:
            with self.subTest(view=view.view_class.__name__):
                force_authenticate(request, user=self.candidate)
                response = view(request, **kwargs)
                self._assert_candidate_forbidden(response)
