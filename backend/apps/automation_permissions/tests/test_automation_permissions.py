"""
Automation Permission Layer — test suite

Covers the 5 acceptance tests from the spec plus additional edge cases.
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.automation_permissions.models import (
    AuditDecision,
    WorkflowPermissionPolicy,
    WorkflowRestrictedAction,
)
from apps.automation_permissions.services.workflow_permission_service import (
    WorkflowPermissionService,
)
from apps.automation_permissions.views import (
    AuditLogListView,
    PermissionCheckView,
    PolicyListView,
    RoleMatrixView,
    RestrictedActionListView,
)

TENANT_ID = '00000000-0000-0000-0000-000000000001'


def _user(role: str, tenant_id=TENANT_ID) -> CustomUser:
    email = f'{role}-{tenant_id[:4]}@example.com'
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return CustomUser.objects.create_user(
            email=email,
            password='testpass123',
            role=role,
            tenant_id=tenant_id,
        )


def _mock_workflow(module_scope='candidates'):
    wf = MagicMock()
    wf.id          = '00000000-0000-0000-0000-000000000099'
    wf.tenant_id   = TENANT_ID
    wf.module_scope = module_scope
    wf.tags        = []
    wf.is_deleted  = False
    return wf


class PermissionServiceTests(TestCase):
    """Unit tests for WorkflowPermissionService."""

    # ── Test 1 ────────────────────────────────────────────────────────────────
    def test_recruiter_cannot_activate_workflow(self):
        """Recruiter tries to activate workflow → denied."""
        recruiter = _user('recruiter')
        workflow  = _mock_workflow()
        result    = WorkflowPermissionService.can_user_access_workflow(
            recruiter, workflow, 'activate'
        )
        self.assertFalse(result['allowed'])
        self.assertFalse(result['requires_approval'])
        self.assertEqual(result['decision'], AuditDecision.DENIED)

    # ── Test 2 ────────────────────────────────────────────────────────────────
    def test_hr_manager_can_create_standard_workflow(self):
        """HR manager creates standard workflow → allowed."""
        hr_manager = _user('hr_manager')
        result     = WorkflowPermissionService.can_user_access_workflow(
            hr_manager, None, 'create'
        )
        self.assertTrue(result['allowed'])
        self.assertEqual(result['decision'], AuditDecision.ALLOWED)

    # ── Test 3 ────────────────────────────────────────────────────────────────
    def test_hr_manager_bulk_rejection_requires_approval(self):
        """HR manager uses critical bulk rejection action → approval required."""
        hr_manager = _user('hr_manager')
        # Seed the restricted action for this tenant
        WorkflowRestrictedAction.objects.create(
            tenant_id=TENANT_ID,
            action_key='bulk_reject_candidate',
            description='Bulk reject candidates',
            severity='critical',
            requires_approval=True,
            requires_admin=False,
        )
        result = WorkflowPermissionService.can_user_access_workflow(
            hr_manager, _mock_workflow(), 'bulk_reject_candidate'
        )
        self.assertFalse(result['allowed'])
        self.assertTrue(result['requires_approval'])
        self.assertEqual(result['decision'], AuditDecision.APPROVAL_REQUIRED)

    # ── Test 4 ────────────────────────────────────────────────────────────────
    def test_tenant_admin_emergency_stop_allowed_and_audited(self):
        """Tenant admin uses emergency stop → allowed and audited."""
        from apps.automation_permissions.models import WorkflowAccessAudit

        admin    = _user('tenant_admin')
        workflow = _mock_workflow()
        result   = WorkflowPermissionService.can_user_access_workflow(
            admin, workflow, 'emergency_stop'
        )
        self.assertTrue(result['allowed'])
        self.assertEqual(result['decision'], AuditDecision.ALLOWED)

        # Verify audit row was written
        audit_qs = WorkflowAccessAudit.objects.filter(
            tenant_id=TENANT_ID,
            action_attempted='emergency_stop',
            decision=AuditDecision.ALLOWED,
        )
        self.assertTrue(audit_qs.exists())

    # ── Test 5 ────────────────────────────────────────────────────────────────
    def test_recruiter_denied_execution_outside_module_scope(self):
        """Recruiter views execution from outside allowed module scope → denied."""
        recruiter = _user('recruiter')
        # 'offers' is outside recruiter's allowed scope
        workflow = _mock_workflow(module_scope='offers')
        result   = WorkflowPermissionService.can_user_access_workflow(
            recruiter, workflow, 'view', resource_type='workflow_execution'
        )
        self.assertFalse(result['allowed'])
        self.assertEqual(result['decision'], AuditDecision.DENIED)

    # ── Additional: trigger permission ────────────────────────────────────────
    def test_recruiter_blocked_from_critical_trigger(self):
        recruiter = _user('recruiter')
        result    = WorkflowPermissionService.can_user_use_trigger(recruiter, 'bulk_rejection')
        self.assertFalse(result['allowed'])

    def test_admin_allowed_on_critical_trigger(self):
        admin  = _user('tenant_admin')
        result = WorkflowPermissionService.can_user_use_trigger(admin, 'bulk_rejection')
        self.assertTrue(result['allowed'])

    # ── Additional: role matrix non-empty ─────────────────────────────────────
    def test_role_matrix_returns_all_roles(self):
        matrix = WorkflowPermissionService.get_role_matrix(TENANT_ID)
        for role in ('tenant_admin', 'hr_manager', 'recruiter', 'hiring_manager', 'interviewer', 'viewer'):
            self.assertIn(role, matrix)


class PolicyAPITests(TestCase):
    """API-level tests for policy endpoints."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin   = _user('tenant_admin')
        self.manager = _user('hr_manager')
        self.viewer  = _user('viewer')

    def test_admin_can_list_policies(self):
        request = self.factory.get('/api/v1/workflow-permissions/policies/')
        force_authenticate(request, user=self.admin)
        response = PolicyListView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_admin_can_create_policy(self):
        request = self.factory.post(
            '/api/v1/workflow-permissions/policies/',
            {
                'name': 'Enterprise Policy',
                'description': 'Full enterprise RBAC',
                'is_active': True,
                'rules': [
                    {
                        'role_code': 'recruiter',
                        'module_scope': 'candidates',
                        'resource_type': 'workflow',
                        'action_type': 'view',
                        'permission_level': 'allow',
                        'conditions': {},
                    }
                ],
            },
            format='json',
        )
        force_authenticate(request, user=self.admin)
        response = PolicyListView.as_view()(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            WorkflowPermissionPolicy.objects.filter(
                tenant_id=self.admin.tenant_id, is_deleted=False
            ).count(),
            1,
        )

    def test_viewer_cannot_create_policy(self):
        request = self.factory.post(
            '/api/v1/workflow-permissions/policies/',
            {'name': 'Should Fail'},
            format='json',
        )
        force_authenticate(request, user=self.viewer)
        response = PolicyListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_permission_check_endpoint(self):
        request = self.factory.post(
            '/api/v1/workflow-permissions/check/',
            {'action': 'activate'},
            format='json',
        )
        force_authenticate(request, user=self.manager)
        response = PermissionCheckView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_role_matrix_endpoint(self):
        request = self.factory.get('/api/v1/workflow-permissions/matrix/')
        force_authenticate(request, user=self.admin)
        response = RoleMatrixView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_audit_log_endpoint(self):
        request = self.factory.get('/api/v1/workflow-permissions/audit/')
        force_authenticate(request, user=self.admin)
        response = AuditLogListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
