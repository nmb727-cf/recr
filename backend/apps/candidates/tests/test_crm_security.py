import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.candidates.crm_views import CRMPipelineView, CRMRemindersView


class CRMSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.candidate_user = CustomUser.objects.create_user(
            email='crm-candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )

    def test_candidate_cannot_access_internal_crm_views(self):
        cases = [
            (CRMPipelineView.as_view(), '/api/v1/candidates/crm/pipeline/'),
            (CRMRemindersView.as_view(), '/api/v1/candidates/crm/reminders/'),
        ]
        for view, path in cases:
            with self.subTest(path=path):
                request = self.factory.get(path)
                force_authenticate(request, user=self.candidate_user)
                response = view(request)
                self.assertEqual(response.status_code, 403)
