import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.communications.email_templates.views import (
    EmailTemplateDuplicateView,
    EmailTemplatePreviewView,
)
from apps.communications.models import EmailTemplateDefinition, EmailTemplateScope


class EmailTemplateScopeSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_a = uuid.uuid4()
        self.tenant_b = uuid.uuid4()
        self.admin_a = CustomUser.objects.create_user(
            email='email-template-admin-a@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_a,
        )
        self.admin_b = CustomUser.objects.create_user(
            email='email-template-admin-b@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_b,
        )
        self.permission_patch = patch('apps.rbac.permissions.user_has_all_permissions', return_value=True)
        self.permission_patch.start()
        self.addCleanup(self.permission_patch.stop)

        self.tenant_b_template = EmailTemplateDefinition.objects.create(
            tenant_id=self.tenant_b,
            template_scope=EmailTemplateScope.TENANT_CUSTOM,
            template_type='business',
            name='Tenant B Private Template',
            slug='tenant-b-private-template',
            subject_template='Hello {{name}}',
            body_html='<p>Hello {{name}}</p>',
            body_text='Hello {{name}}',
            is_active=True,
        )
        self.system_template = EmailTemplateDefinition.objects.create(
            tenant_id=None,
            template_scope=EmailTemplateScope.SYSTEM_DEFAULT,
            template_type='system',
            name='System Default Template',
            slug='system-default-template',
            subject_template='System {{name}}',
            body_html='<p>System {{name}}</p>',
            body_text='System {{name}}',
            is_active=True,
            is_system_locked=True,
        )

    def test_cross_tenant_template_preview_is_blocked(self):
        request = self.factory.post(
            f'/api/v1/communications/templates/{self.tenant_b_template.id}/preview/',
            {'variables': {'name': 'User'}},
            format='json',
        )
        force_authenticate(request, user=self.admin_a)
        response = EmailTemplatePreviewView.as_view()(request, pk=self.tenant_b_template.id)
        self.assertEqual(response.status_code, 404)

    def test_cross_tenant_template_duplicate_is_blocked(self):
        request = self.factory.post(
            f'/api/v1/communications/templates/{self.tenant_b_template.id}/duplicate/',
            {},
            format='json',
        )
        force_authenticate(request, user=self.admin_a)
        response = EmailTemplateDuplicateView.as_view()(request, pk=self.tenant_b_template.id)
        self.assertEqual(response.status_code, 404)

    def test_system_template_preview_and_duplicate_allowed(self):
        preview_request = self.factory.post(
            f'/api/v1/communications/templates/{self.system_template.id}/preview/',
            {'variables': {'name': 'User'}},
            format='json',
        )
        force_authenticate(preview_request, user=self.admin_a)
        preview_response = EmailTemplatePreviewView.as_view()(preview_request, pk=self.system_template.id)
        self.assertEqual(preview_response.status_code, 200)

        duplicate_request = self.factory.post(
            f'/api/v1/communications/templates/{self.system_template.id}/duplicate/',
            {},
            format='json',
        )
        force_authenticate(duplicate_request, user=self.admin_a)
        duplicate_response = EmailTemplateDuplicateView.as_view()(duplicate_request, pk=self.system_template.id)
        self.assertEqual(duplicate_response.status_code, 201)
