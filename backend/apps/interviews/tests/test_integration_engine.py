from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.interviews.models import (
    Interview,
    InterviewIntegrationProvider,
    InterviewTenantProviderConnection,
    InterviewExecutionMapping,
)
from apps.interviews.views import (
    InterviewIntegrationProviderListView,
    InterviewIntegrationProviderDetailView,
    InterviewTenantProviderConnectionListView,
    InterviewExecutionMappingListView,
    InterviewManualSchedulingView,
    InterviewStructuredFeedbackView,
    InterviewDecisionView,
)


class InterviewIntegrationEngineTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = CustomUser.objects.create_user(
            email='integration-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id='00000000-0000-0000-0000-000000000001',
        )
        self.permission_patch = patch('apps.rbac.permissions.user_has_all_permissions', return_value=True)
        self.permission_patch.start()
        self.addCleanup(self.permission_patch.stop)

    def test_provider_registry_loads(self):
        request = self.factory.get('/api/v1/interviews/integrations/providers/')
        force_authenticate(request, user=self.user)
        response = InterviewIntegrationProviderListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['meta']['total'], 7)

    def test_enable_disable_works(self):
        request = self.factory.get('/api/v1/interviews/integrations/providers/')
        force_authenticate(request, user=self.user)
        InterviewIntegrationProviderListView.as_view()(request)
        provider = InterviewIntegrationProvider.objects.filter(is_deleted=False).first()
        self.assertIsNotNone(provider)
        put_req = self.factory.put(
            f'/api/v1/interviews/integrations/providers/{provider.id}/',
            {'is_active': False},
            format='json',
        )
        force_authenticate(put_req, user=self.user)
        response = InterviewIntegrationProviderDetailView.as_view()(put_req, pk=provider.id)
        self.assertEqual(response.status_code, 200)
        provider.refresh_from_db()
        self.assertFalse(provider.is_active)

    def test_tenant_config_saves(self):
        request = self.factory.get('/api/v1/interviews/integrations/providers/')
        force_authenticate(request, user=self.user)
        InterviewIntegrationProviderListView.as_view()(request)
        provider = InterviewIntegrationProvider.objects.filter(code='zoom').first()
        self.assertIsNotNone(provider)
        post_req = self.factory.post(
            '/api/v1/interviews/integrations/connections/',
            {
                'provider_id': str(provider.id),
                'auth_data': {'token': 'x'},
                'config_data': {'account_email': 'ops@example.com'},
                'is_enabled': True,
            },
            format='json',
        )
        force_authenticate(post_req, user=self.user)
        response = InterviewTenantProviderConnectionListView.as_view()(post_req)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(InterviewTenantProviderConnection.objects.filter(tenant_id=self.user.tenant_id, provider=provider).exists())

    def test_execution_mode_mapping_works(self):
        map_req = self.factory.post(
            '/api/v1/interviews/integrations/mappings/',
            {
                'interview_type': 'technical_interview',
                'stage_code': '',
                'execution_mode': 'third_party',
                'provider_code': 'zoom',
                'is_active': True,
            },
            format='json',
        )
        force_authenticate(map_req, user=self.user)
        map_res = InterviewExecutionMappingListView.as_view()(map_req)
        self.assertEqual(map_res.status_code, 201)
        self.assertTrue(InterviewExecutionMapping.objects.filter(tenant_id=self.user.tenant_id, interview_type='technical_interview').exists())

        sched_req = self.factory.post(
            '/api/v1/interviews/scheduling/manual/',
            {
                'application_id': '00000000-0000-0000-0000-000000000111',
                'candidate_id': '00000000-0000-0000-0000-000000000222',
                'requisition_id': '00000000-0000-0000-0000-000000000333',
                'interview_type': 'technical_interview',
                'scheduled_at': '2026-04-01T10:00:00Z',
                'duration_minutes': 60,
            },
            format='json',
        )
        force_authenticate(sched_req, user=self.user)
        sched_res = InterviewManualSchedulingView.as_view()(sched_req)
        self.assertEqual(sched_res.status_code, 201)
        interview_id = sched_res.data['data']['interview']['id']
        interview = Interview.objects.get(id=interview_id)
        self.assertEqual(interview.execution_mode, 'third_party')
        self.assertEqual(interview.execution_provider_code, 'zoom')

    def test_external_manual_interview_can_be_tracked(self):
        create_req = self.factory.post(
            '/api/v1/interviews/scheduling/manual/',
            {
                'application_id': '00000000-0000-0000-0000-000000000511',
                'candidate_id': '00000000-0000-0000-0000-000000000522',
                'requisition_id': '00000000-0000-0000-0000-000000000533',
                'interview_type': 'behavioral',
                'scheduled_at': '2026-04-01T12:00:00Z',
                'execution_mode': 'external_manual',
                'external_interview_link': 'https://external.tool/interview/abc',
            },
            format='json',
        )
        force_authenticate(create_req, user=self.user)
        create_res = InterviewManualSchedulingView.as_view()(create_req)
        self.assertEqual(create_res.status_code, 201)
        interview_id = create_res.data['data']['interview']['id']

        feedback_req = self.factory.post(
            f'/api/v1/interviews/{interview_id}/structured-feedback/',
            {
                'score': 78,
                'notes': 'External interview completed',
                'recommendation': 'next_round',
            },
            format='json',
        )
        force_authenticate(feedback_req, user=self.user)
        feedback_res = InterviewStructuredFeedbackView.as_view()(feedback_req, pk=interview_id)
        self.assertEqual(feedback_res.status_code, 200)

        decision_req = self.factory.post(
            f'/api/v1/interviews/{interview_id}/decision/',
            {'decision': 'next_round', 'notes': 'Proceed'},
            format='json',
        )
        force_authenticate(decision_req, user=self.user)
        decision_res = InterviewDecisionView.as_view()(decision_req, pk=interview_id)
        self.assertEqual(decision_res.status_code, 200)

