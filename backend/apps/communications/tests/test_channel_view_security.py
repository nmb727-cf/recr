import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.communications import channel_views


class ChannelViewSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.candidate = CustomUser.objects.create_user(
            email='channel-candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )
        self.recruiter = CustomUser.objects.create_user(
            email='channel-recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )

    def _assert_forbidden(self, user, view, path, kwargs=None):
        request = self.factory.get(path)
        force_authenticate(request, user=user)
        response = view(request, **(kwargs or {}))
        self.assertEqual(response.status_code, 403)

    def test_candidate_blocked_from_channel_admin_views(self):
        delivery_id = uuid.uuid4()
        config_id = uuid.uuid4()
        self._assert_forbidden(
            self.candidate,
            channel_views.CommunicationDeliveryListView.as_view(),
            '/api/v1/communications/deliveries/',
        )
        self._assert_forbidden(
            self.candidate,
            channel_views.CommunicationDeliveryDetailView.as_view(),
            f'/api/v1/communications/deliveries/{delivery_id}/',
            {'delivery_id': delivery_id},
        )
        self._assert_forbidden(
            self.candidate,
            channel_views.ChannelHealthView.as_view(),
            '/api/v1/communications/channel-health/',
        )
        self._assert_forbidden(
            self.candidate,
            channel_views.TenantChannelConfigListView.as_view(),
            '/api/v1/communications/channel-configs/',
        )
        self._assert_forbidden(
            self.candidate,
            channel_views.TenantChannelConfigDetailView.as_view(),
            f'/api/v1/communications/channel-configs/{config_id}/',
            {'config_id': config_id},
        )

    def test_recruiter_blocked_from_channel_admin_views(self):
        self._assert_forbidden(
            self.recruiter,
            channel_views.CommunicationDeliveryListView.as_view(),
            '/api/v1/communications/deliveries/',
        )
        self._assert_forbidden(
            self.recruiter,
            channel_views.ChannelStatsView.as_view(),
            '/api/v1/communications/channel-stats/',
        )
