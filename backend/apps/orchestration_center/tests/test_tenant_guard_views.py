import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.orchestration_center.api.views import (
    GovernanceApproveView,
    GovernanceRejectView,
    LibraryTemplateActivateView,
    LibraryTemplateCloneView,
    WorkflowApprovalDecideView,
    WorkflowRollbackView,
    WorkflowSafetyRuleView,
)
from apps.orchestration_center.models import (
    AIGovernanceApproval,
    AutomationLibraryTemplate,
    Workflow,
    WorkflowApproval,
    WorkflowExecution,
    WorkflowSafetyRule,
    WorkflowVersion,
)


class TenantGuardViewsTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.UUID("00000000-0000-0000-0000-00000000a101")
        self.other_tenant_id = uuid.UUID("00000000-0000-0000-0000-00000000b202")
        self.user = get_user_model().objects.create_user(
            email="tenant-guard-admin@example.com",
            password="password",
            tenant_id=self.tenant_id,
            role="super_admin",
            is_staff=True,
        )

    def _call(self, view_cls, method, path, *, data=None, **kwargs):
        request = getattr(self.factory, method.lower())(path, data=data or {}, format="json")
        force_authenticate(request, user=self.user)
        response = view_cls.as_view()(request, **kwargs)
        response.render()
        return response

    def _make_workflow_bundle(self):
        workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name="Tenant Guard Workflow",
            trigger_event="candidate_applied",
            is_active=True,
        )
        version = WorkflowVersion.objects.create(
            tenant_id=self.tenant_id,
            workflow=workflow,
            version_number=1,
            config_snapshot={"nodes": [], "edges": []},
            is_active=True,
        )
        return workflow, version

    def test_workflow_approval_decide_rejects_cross_tenant_request(self):
        workflow, version = self._make_workflow_bundle()
        approval = WorkflowApproval.objects.create(
            tenant_id=self.tenant_id,
            workflow=workflow,
            version=version,
            requested_by=self.user.id,
            status="pending",
        )
        response = self._call(
            WorkflowApprovalDecideView,
            "post",
            f"/api/v1/intelligence/workflows/approvals/{approval.id}/decide/",
            data={"status": "approved", "tenant_id": str(self.other_tenant_id)},
            pk=approval.id,
        )
        self.assertEqual(response.status_code, 404)

    def test_workflow_safety_rule_get_scoped_by_effective_tenant(self):
        workflow, _ = self._make_workflow_bundle()
        WorkflowSafetyRule.objects.create(
            tenant_id=self.tenant_id,
            workflow=workflow,
            max_executions_per_hour=50,
        )

        denied = self._call(
            WorkflowSafetyRuleView,
            "get",
            f"/api/v1/intelligence/workflows/{workflow.id}/safety-rule/?tenant_id={self.other_tenant_id}",
            workflow_id=workflow.id,
        )
        self.assertEqual(denied.status_code, 404)

        allowed = self._call(
            WorkflowSafetyRuleView,
            "get",
            f"/api/v1/intelligence/workflows/{workflow.id}/safety-rule/?tenant_id={self.tenant_id}",
            workflow_id=workflow.id,
        )
        self.assertEqual(allowed.status_code, 200)

    def test_workflow_rollback_rejects_cross_tenant_execution(self):
        workflow, version = self._make_workflow_bundle()
        execution = WorkflowExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow=workflow,
            version=version,
            entity_type="candidate",
            entity_id="candidate-1",
            status="running",
        )
        response = self._call(
            WorkflowRollbackView,
            "post",
            f"/api/v1/intelligence/workflows/executions/{execution.id}/rollback/",
            data={"tenant_id": str(self.other_tenant_id)},
            execution_id=execution.id,
        )
        self.assertEqual(response.status_code, 404)

    def test_governance_approve_reject_paths_enforce_tenant(self):
        approval = AIGovernanceApproval.objects.create(
            tenant_id=self.other_tenant_id,
            request_type="policy_change",
            requested_by=self.user.id,
            approval_status="pending",
        )

        approve_response = self._call(
            GovernanceApproveView,
            "post",
            "/api/v1/intelligence/governance/approve/",
            data={"approval_id": str(approval.id)},
        )
        self.assertEqual(approve_response.status_code, 404)

        reject_response = self._call(
            GovernanceRejectView,
            "post",
            "/api/v1/intelligence/governance/reject/",
            data={"approval_id": str(approval.id)},
        )
        self.assertEqual(reject_response.status_code, 404)

    def test_governance_approve_success_in_tenant(self):
        approval = AIGovernanceApproval.objects.create(
            tenant_id=self.tenant_id,
            request_type="policy_change",
            requested_by=self.user.id,
            approval_status="pending",
        )
        response = self._call(
            GovernanceApproveView,
            "post",
            "/api/v1/intelligence/governance/approve/",
            data={"approval_id": str(approval.id), "reason": "looks good"},
        )
        self.assertEqual(response.status_code, 200)
        approval.refresh_from_db()
        self.assertEqual(approval.approval_status, "approved")

    def test_library_template_clone_activate_require_system_template(self):
        template = AutomationLibraryTemplate.objects.create(
            tenant_id=self.tenant_id,
            template_name="Tenant Local Template",
            template_type="workflow",
            category="ops",
            config_payload={"steps": []},
            is_system_template=False,
        )

        clone_response = self._call(
            LibraryTemplateCloneView,
            "post",
            f"/api/v1/intelligence/library/templates/{template.id}/clone/",
            pk=template.id,
        )
        self.assertEqual(clone_response.status_code, 404)

        activate_response = self._call(
            LibraryTemplateActivateView,
            "post",
            f"/api/v1/intelligence/library/templates/{template.id}/activate/",
            pk=template.id,
        )
        self.assertEqual(activate_response.status_code, 404)
