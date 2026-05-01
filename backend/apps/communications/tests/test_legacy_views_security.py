import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.communications.models import EmailTemplate
from apps.communications.views import (
    EmailAccountViewSet,
    EmailTemplateListView,
    EmailTemplateDetailView,
)


class LegacyCommunicationsViewSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.candidate = CustomUser.objects.create_user(
            email='comms-candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )
        self.recruiter = CustomUser.objects.create_user(
            email='comms-recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )

    def test_candidate_cannot_access_legacy_communication_admin_views(self):
        template_id = uuid.uuid4()
        cases = [
            (self.factory.get('/api/v1/communications/communication/email-accounts/'), EmailAccountViewSet.as_view({'get': 'list'}), {}),
            (self.factory.get('/api/v1/communications/communication/templates/'), EmailTemplateListView.as_view(), {}),
            (self.factory.get(f'/api/v1/communications/communication/templates/{template_id}/'), EmailTemplateDetailView.as_view(), {'pk': template_id}),
        ]
        for request, view, kwargs in cases:
            with self.subTest(view=str(view)):
                force_authenticate(request, user=self.candidate)
                response = view(request, **kwargs)
                self.assertEqual(response.status_code, 403)

    def test_recruiter_can_access_legacy_template_list(self):
        request = self.factory.get('/api/v1/communications/communication/templates/')
        force_authenticate(request, user=self.recruiter)
        with patch('apps.rbac.permissions.user_has_all_permissions', return_value=True):
            response = EmailTemplateListView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_recruiter_without_template_permissions_is_denied(self):
        request = self.factory.get('/api/v1/communications/communication/templates/')
        force_authenticate(request, user=self.recruiter)
        with patch('apps.rbac.permissions.user_has_all_permissions', return_value=False):
            response = EmailTemplateListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_recruiter_without_manage_permission_cannot_update_template(self):
        template = EmailTemplate.objects.create(
            tenant_id=self.tenant_id,
            name='Legacy Template',
            subject='Subject',
            body_html='<p>Body</p>',
            body_text='Body',
            created_by=self.recruiter.id,
        )
        request = self.factory.put(
            f'/api/v1/communications/communication/templates/{template.id}/',
            {'name': 'Updated'},
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        with patch('apps.rbac.permissions.user_has_all_permissions', return_value=False):
            response = EmailTemplateDetailView.as_view()(request, pk=template.id)
        self.assertEqual(response.status_code, 403)
