from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.interviews.models import InterviewType
from apps.interviews.views import (
    InterviewTypeConfigView,
    InterviewTypeDetailView,
    InterviewTypeListView,
)


class InterviewTypesEngineTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = CustomUser.objects.create_user(
            email='types-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id='00000000-0000-0000-0000-000000000001',
        )
        self.permission_patch = patch('apps.rbac.permissions.user_has_all_permissions', return_value=True)
        self.permission_patch.start()
        self.addCleanup(self.permission_patch.stop)

    def test_type_registry_loads_and_has_40_plus_entries(self):
        request = self.factory.get('/api/v1/interviews/types/')
        force_authenticate(request, user=self.user)
        response = InterviewTypeListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['meta']['total'], 40)
        self.assertGreaterEqual(InterviewType.objects.filter(is_deleted=False).count(), 40)

    def test_enable_disable_works(self):
        itype = InterviewType.objects.filter(is_deleted=False).first()
        self.assertIsNotNone(itype)

        disable_request = self.factory.put(
            f'/api/v1/interviews/types/{itype.id}/',
            {'is_active': False},
            format='json',
        )
        force_authenticate(disable_request, user=self.user)
        disable_response = InterviewTypeDetailView.as_view()(disable_request, pk=itype.id)
        self.assertEqual(disable_response.status_code, 200)

        itype.refresh_from_db()
        self.assertFalse(itype.is_active)

    def test_type_configuration_page_loads_and_updates(self):
        itype = InterviewType.objects.filter(is_deleted=False).first()
        self.assertIsNotNone(itype)

        get_request = self.factory.get(f'/api/v1/interviews/types/{itype.id}/config/')
        force_authenticate(get_request, user=self.user)
        get_response = InterviewTypeConfigView.as_view()(get_request, pk=itype.id)
        self.assertEqual(get_response.status_code, 200)
        self.assertIn('configuration', get_response.data['data'])

        update_request = self.factory.put(
            f'/api/v1/interviews/types/{itype.id}/config/',
            {
                'execution_mode': 'manual',
                'configurable': True,
                'is_active': True,
                'template': True,
                'scorecard': True,
                'scheduling': True,
                'automation': False,
                'prequalification': True,
            },
            format='json',
        )
        force_authenticate(update_request, user=self.user)
        update_response = InterviewTypeConfigView.as_view()(update_request, pk=itype.id)
        self.assertEqual(update_response.status_code, 200)

        itype.refresh_from_db()
        self.assertEqual(itype.execution_mode, 'manual')
        self.assertTrue(itype.type_configuration.get('prequalification'))
        self.assertFalse(itype.type_configuration.get('automation'))
