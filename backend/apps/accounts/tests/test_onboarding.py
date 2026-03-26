import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.accounts.views import CompleteOnboardingView


class CompleteOnboardingViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = CompleteOnboardingView.as_view()

    def _post(self, user, payload):
        request = self.factory.post('/api/v1/auth/onboarding/complete/', payload, format='json')
        force_authenticate(request, user=user)
        return self.view(request)

    @patch('apps.accounts.views._auto_configure')
    @patch('apps.accounts.views.events.onboarding.completed.send_robust')
    def test_agency_onboarding_succeeds_when_signal_receiver_fails(self, mock_send_robust, mock_auto_configure):
        user = CustomUser.objects.create_user(
            email='agency-owner@example.com',
            password='testpass123',
            role='agency_owner',
            tenant_id=uuid.uuid4(),
            first_name='Agency',
            last_name='Owner',
        )
        mock_send_robust.return_value = [('receiver', RuntimeError('broker down'))]

        response = self._post(user, {
            'hiring_style': 'agency',
            'team_size': '1-5',
            'automation_preference': 'manual',
        })

        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(user.role, 'agency_owner')
        self.assertEqual(user.metadata['onboarding']['user_type'], 'agency')
        mock_auto_configure.assert_called_once()

    @patch('apps.accounts.views._auto_configure')
    @patch('apps.accounts.views.events.onboarding.completed.send_robust')
    def test_company_onboarding_still_succeeds(self, mock_send_robust, mock_auto_configure):
        user = CustomUser.objects.create_user(
            email='tenant-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=uuid.uuid4(),
            first_name='Company',
            last_name='Admin',
        )
        mock_send_robust.return_value = []

        response = self._post(user, {
            'hiring_style': 'internal',
            'team_size': '5-20',
            'automation_preference': 'manual',
        })

        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(user.metadata['onboarding']['user_type'], 'company')
        mock_auto_configure.assert_called_once()

    def test_onboarding_requires_tenant(self):
        user = CustomUser.objects.create_user(
            email='no-tenant@example.com',
            password='testpass123',
            role='agency_owner',
            tenant_id=None,
        )

        response = self._post(user, {
            'hiring_style': 'agency',
            'team_size': '1-5',
            'automation_preference': 'manual',
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['errors']['tenant_id'], 'missing')
