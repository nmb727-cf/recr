import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.organisations.models import Organisation
from apps.orchestration_center.models import IntelligenceAuditLog
from apps.tenants.admin_views import (
    MasterAdminTenantFeatureFlagsView,
    MasterAdminTenantLimitsView,
    MasterAdminTenantListView,
    MasterAdminTenantReactivateView,
    MasterAdminTenantSuspendView,
    MasterAdminTenantVerifyView,
)
from apps.tenants.models import Client


class MasterAdminControlPlaneTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.super_admin = CustomUser.objects.create_user(
            email='super-admin@talentos.test',
            password='testpass123',
            role='super_admin',
            is_staff=True,
        )
        self.tenant_admin = CustomUser.objects.create_user(
            email='tenant-admin@talentos.test',
            password='testpass123',
            role='tenant_admin',
            tenant_id=uuid.uuid4(),
        )
        self.recruiter = CustomUser.objects.create_user(
            email='recruiter@talentos.test',
            password='testpass123',
            role='recruiter',
            tenant_id=uuid.uuid4(),
        )

        self.target_tenant = Client.objects.create(
            schema_name='tenant-alpha',
            name='Tenant Alpha',
            slug='tenant-alpha',
            tenant_type='company',
            status='active',
        )
        Organisation.objects.create(
            tenant_id=self.target_tenant.id,
            name='Tenant Alpha Org',
            org_type='company',
            settings={
                'limits': {'user_limit': 10, 'job_limit': 20, 'candidate_limit': 100},
                'feature_flags': {'agency_intelligence': False},
            },
        )

    def test_non_admin_denied_from_master_admin_endpoints(self):
        request = self.factory.get('/api/v1/admin/tenants/')
        force_authenticate(request, user=self.recruiter)
        response = MasterAdminTenantListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_tenant_admin_denied_from_master_admin_endpoints(self):
        request = self.factory.get('/api/v1/admin/tenants/')
        force_authenticate(request, user=self.tenant_admin)
        response = MasterAdminTenantListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    @patch('apps.rbac.utils.get_user_permissions', return_value=frozenset({'master_admin.access'}))
    def test_tenant_admin_with_master_admin_permission_allowed(self, _mock_get_user_permissions):
        request = self.factory.post(
            f'/api/v1/admin/tenants/{self.target_tenant.id}/verify/',
            {},
            format='json',
        )
        force_authenticate(request, user=self.tenant_admin)
        response = MasterAdminTenantVerifyView.as_view()(request, tenant_id=self.target_tenant.id)
        self.assertEqual(response.status_code, 200)

    def test_verify_suspend_reactivate_flow(self):
        verify_request = self.factory.post(
            f'/api/v1/admin/tenants/{self.target_tenant.id}/verify/',
            {},
            format='json',
        )
        force_authenticate(verify_request, user=self.super_admin)
        verify_response = MasterAdminTenantVerifyView.as_view()(verify_request, tenant_id=self.target_tenant.id)
        self.assertEqual(verify_response.status_code, 200)

        org = Organisation.objects.get(tenant_id=self.target_tenant.id, is_deleted=False)
        self.assertEqual((org.metadata or {}).get('verification_state'), 'verified')

        suspend_request = self.factory.post(
            f'/api/v1/admin/tenants/{self.target_tenant.id}/suspend/',
            {'reason': 'security review'},
            format='json',
        )
        force_authenticate(suspend_request, user=self.super_admin)
        suspend_response = MasterAdminTenantSuspendView.as_view()(suspend_request, tenant_id=self.target_tenant.id)
        self.assertEqual(suspend_response.status_code, 200)
        self.target_tenant.refresh_from_db()
        self.assertEqual(self.target_tenant.status, 'suspended')

        reactivate_request = self.factory.post(
            f'/api/v1/admin/tenants/{self.target_tenant.id}/reactivate/',
            {'reason': 'review complete'},
            format='json',
        )
        force_authenticate(reactivate_request, user=self.super_admin)
        reactivate_response = MasterAdminTenantReactivateView.as_view()(reactivate_request, tenant_id=self.target_tenant.id)
        self.assertEqual(reactivate_response.status_code, 200)
        self.target_tenant.refresh_from_db()
        self.assertEqual(self.target_tenant.status, 'active')

    def test_feature_flag_update_works(self):
        request = self.factory.put(
            f'/api/v1/admin/tenants/{self.target_tenant.id}/feature-flags/',
            {'feature_flags': {'agency_intelligence': True, 'interview_ai': True}},
            format='json',
        )
        force_authenticate(request, user=self.super_admin)
        response = MasterAdminTenantFeatureFlagsView.as_view()(request, tenant_id=self.target_tenant.id)
        self.assertEqual(response.status_code, 200)

        org = Organisation.objects.get(tenant_id=self.target_tenant.id, is_deleted=False)
        self.assertEqual(org.settings.get('feature_flags', {}).get('agency_intelligence'), True)
        self.assertEqual(org.settings.get('feature_flags', {}).get('interview_ai'), True)

    def test_limit_update_works(self):
        request = self.factory.put(
            f'/api/v1/admin/tenants/{self.target_tenant.id}/limits/',
            {'user_limit': 25, 'job_limit': 200},
            format='json',
        )
        force_authenticate(request, user=self.super_admin)
        response = MasterAdminTenantLimitsView.as_view()(request, tenant_id=self.target_tenant.id)
        self.assertEqual(response.status_code, 200)

        org = Organisation.objects.get(tenant_id=self.target_tenant.id, is_deleted=False)
        limits = org.settings.get('limits', {})
        self.assertEqual(limits.get('user_limit'), 25)
        self.assertEqual(limits.get('job_limit'), 200)
        self.assertEqual(limits.get('candidate_limit'), 100)

    def test_audit_entry_created_for_admin_actions(self):
        request = self.factory.post(
            f'/api/v1/admin/tenants/{self.target_tenant.id}/suspend/',
            {'reason': 'audit check'},
            format='json',
        )
        force_authenticate(request, user=self.super_admin)
        response = MasterAdminTenantSuspendView.as_view()(request, tenant_id=self.target_tenant.id)
        self.assertEqual(response.status_code, 200)

        audit_exists = IntelligenceAuditLog.objects.filter(
            action_type='master_admin.tenant_suspended',
            target_type='tenant',
            target_id=self.target_tenant.id,
        ).exists()
        self.assertTrue(audit_exists)
