import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.interviews.models import InterviewIntegrationProvider, Interview
from apps.interviews.views import (
    InterviewPackageListView,
    InterviewListView,
    InterviewTypeListView,
    InterviewIntegrationProviderDetailView,
    InterviewStartView,
    InterviewTemplateListView,
    InterviewFlowListView,
)


class InternalInterviewsSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.candidate = CustomUser.objects.create_user(
            email='interviews-internal-candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )
        self.recruiter = CustomUser.objects.create_user(
            email='interviews-internal-recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )
        self.tenant_admin = CustomUser.objects.create_user(
            email='interviews-internal-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_id,
        )

    def test_candidate_cannot_access_internal_interview_ops_endpoints(self):
        cases = [
            (self.factory.get('/api/v1/interviews/packages/'), InterviewPackageListView.as_view(), {}),
            (self.factory.get('/api/v1/interviews/'), InterviewListView.as_view(), {}),
            (self.factory.get('/api/v1/interviews/types/'), InterviewTypeListView.as_view(), {}),
        ]
        for request, view, kwargs in cases:
            with self.subTest(view=view.view_class.__name__):
                force_authenticate(request, user=self.candidate)
                response = view(request, **kwargs)
                self.assertEqual(response.status_code, 403)

    def test_only_admin_can_modify_integration_provider(self):
        provider = InterviewIntegrationProvider.objects.create(
            name='Test Provider',
            code='test_provider_security',
            provider_type='calendar',
            tenant_configurable=True,
            is_active=True,
        )

        recruiter_request = self.factory.put(
            f'/api/v1/interviews/providers/{provider.id}/',
            {'name': 'Recruiter Update Attempt'},
            format='json',
        )
        force_authenticate(recruiter_request, user=self.recruiter)
        recruiter_response = InterviewIntegrationProviderDetailView.as_view()(recruiter_request, pk=provider.id)
        self.assertEqual(recruiter_response.status_code, 403)

        admin_request = self.factory.put(
            f'/api/v1/interviews/providers/{provider.id}/',
            {'name': 'Admin Updated Provider'},
            format='json',
        )
        force_authenticate(admin_request, user=self.tenant_admin)
        admin_response = InterviewIntegrationProviderDetailView.as_view()(admin_request, pk=provider.id)
        self.assertEqual(admin_response.status_code, 200)

    def test_recruiter_without_interview_permissions_is_denied_on_write_paths(self):
        create_request = self.factory.post(
            '/api/v1/interviews/',
            {
                'application_id': str(uuid.uuid4()),
                'candidate_id': str(uuid.uuid4()),
                'interview_type': 'ai_screening',
            },
            format='json',
        )
        force_authenticate(create_request, user=self.recruiter)
        with patch('apps.rbac.permissions.user_has_all_permissions', return_value=False):
            create_response = InterviewListView.as_view()(create_request)
        self.assertEqual(create_response.status_code, 403)

        interview = Interview.objects.create(
            tenant_id=self.tenant_id,
            application_id=uuid.uuid4(),
            candidate_id=uuid.uuid4(),
            requisition_id=uuid.uuid4(),
            interview_type='ai_screening',
            status='scheduled',
            created_by=self.tenant_admin.id,
        )
        start_request = self.factory.post(f'/api/v1/interviews/{interview.id}/start/', {}, format='json')
        force_authenticate(start_request, user=self.recruiter)
        with patch('apps.rbac.permissions.user_has_all_permissions', return_value=False):
            start_response = InterviewStartView.as_view()(start_request, pk=interview.id)
        self.assertEqual(start_response.status_code, 403)

    def test_recruiter_without_template_permission_cannot_create_template(self):
        request = self.factory.post(
            '/api/v1/interviews/templates/',
            {'name': 'Template Permission Test', 'interview_type': 'ai_screening'},
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        with patch('apps.rbac.permissions.user_has_all_permissions', return_value=False):
            response = InterviewTemplateListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_recruiter_without_interview_create_permission_cannot_create_flow(self):
        request = self.factory.post(
            '/api/v1/interviews/flows/',
            {'name': 'Flow Permission Test', 'steps': []},
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        with patch('apps.rbac.permissions.user_has_all_permissions', return_value=False):
            response = InterviewFlowListView.as_view()(request)
        self.assertEqual(response.status_code, 403)
