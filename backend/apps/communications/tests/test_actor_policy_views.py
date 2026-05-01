import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.communications.analytics_views import CommunicationDashboardView
from apps.communications.notification_orchestration_views import NotificationAutomationJobListView


class CommunicationsActorPolicyViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.candidate = CustomUser.objects.create_user(
            email='policy-candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )
        self.recruiter = CustomUser.objects.create_user(
            email='policy-recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )
        self.tenant_admin = CustomUser.objects.create_user(
            email='policy-tenant-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_id,
        )

    def test_candidate_blocked_from_communications_analytics(self):
        request = self.factory.get('/api/v1/communications/communication-analytics/dashboard/')
        force_authenticate(request, user=self.candidate)
        response = CommunicationDashboardView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_recruiter_blocked_from_orchestration_admin_endpoint(self):
        request = self.factory.get('/api/v1/communications/notification-control/jobs/')
        force_authenticate(request, user=self.recruiter)
        response = NotificationAutomationJobListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_tenant_admin_allowed_on_orchestration_admin_endpoint(self):
        request = self.factory.get('/api/v1/communications/notification-control/jobs/')
        force_authenticate(request, user=self.tenant_admin)
        response = NotificationAutomationJobListView.as_view()(request)
        self.assertNotEqual(response.status_code, 403)
