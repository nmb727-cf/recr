import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.jobs.views import (
    JobRequisitionListView,
    JobRequisitionDetailView,
    JobPostingListView,
    JDTemplateListView,
    JobPrequalSnapshotView,
)


class InternalJobsSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.candidate = CustomUser.objects.create_user(
            email='jobs-internal-candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )

    def test_candidate_cannot_access_internal_jobs_endpoints(self):
        requisition_id = uuid.uuid4()
        cases = [
            (self.factory.get('/api/v1/jobs/requisitions/'), JobRequisitionListView.as_view(), {}),
            (self.factory.get(f'/api/v1/jobs/requisitions/{requisition_id}/'), JobRequisitionDetailView.as_view(), {'pk': requisition_id}),
            (self.factory.get('/api/v1/jobs/postings/'), JobPostingListView.as_view(), {}),
            (self.factory.get('/api/v1/jobs/templates/'), JDTemplateListView.as_view(), {}),
            (self.factory.get(f'/api/v1/jobs/requisitions/{requisition_id}/prequal-snapshot/'), JobPrequalSnapshotView.as_view(), {'pk': requisition_id}),
        ]
        for request, view, kwargs in cases:
            with self.subTest(view=view.view_class.__name__):
                force_authenticate(request, user=self.candidate)
                response = view(request, **kwargs)
                self.assertEqual(response.status_code, 403)
