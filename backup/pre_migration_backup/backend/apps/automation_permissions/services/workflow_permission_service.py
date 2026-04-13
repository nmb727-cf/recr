"""
WorkflowPermissionService
─────────────────────────
Central gate for all automation RBAC decisions.

Usage:
    from apps.automation_permissions.services.workflow_permission_service import (
        WorkflowPermissionService,
    )

    result = WorkflowPermissionService.can_user_access_workflow(user, workflow, 'activate')
    if result['allowed']:
        ...
    elif result['requires_approval']:
        # trigger governance approval
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.db.models import Q

from apps.automation_permissions.models import (
    AuditDecision,
    PermissionLevel,
    WorkflowAccessAudit,
    WorkflowPermissionPolicy,
    WorkflowPermissionRule,
    WorkflowRestrictedAction,
)

if TYPE_CHECKING:
    from apps.accounts.models import CustomUser
    from apps.orchestration_center.models.workflow import Workflow

logger = logging.getLogger(__name__)

# ─── Default role matrix ──────────────────────────────────────────────────────
# Fallback when no policy rule exists for the (role, resource, action) triple.

_DEFAULT_MATRIX: dict[str, dict[str, PermissionLevel]] = {
    'tenant_admin': {
        '__all__': PermissionLevel.ALLOW,
    },
    'super_admin': {
        '__all__': PermissionLevel.ALLOW,
    },
    'hr_manager': {
        'workflow.view':           PermissionLevel.ALLOW,
        'workflow.create':         PermissionLevel.ALLOW,
        'workflow.edit':           PermissionLevel.ALLOW,
        'workflow.activate':       PermissionLevel.ALLOW,
        'workflow.pause':          PermissionLevel.ALLOW,
        'workflow.archive':        PermissionLevel.ALLOW,
        'workflow.duplicate':      PermissionLevel.ALLOW,
        'workflow.import_template':PermissionLevel.ALLOW,
        'workflow.dry_run':        PermissionLevel.ALLOW,
        'workflow.view_logs':      PermissionLevel.ALLOW,
        'workflow.view_analytics': PermissionLevel.ALLOW,
        'workflow.emergency_stop': PermissionLevel.REQUIRE_APPROVAL,
        'workflow.rollback':       PermissionLevel.REQUIRE_APPROVAL,
        'workflow_execution.view': PermissionLevel.ALLOW,
        'workflow_template.view':  PermissionLevel.ALLOW,
        'workflow_analytics.view_analytics': PermissionLevel.ALLOW,
        'automation_center.view':  PermissionLevel.ALLOW,
    },
    'recruiter': {
        'workflow.view':           PermissionLevel.ALLOW,
        'workflow_execution.view': PermissionLevel.ALLOW,
        'workflow_template.view':  PermissionLevel.ALLOW,
        'automation_center.view':  PermissionLevel.ALLOW,
    },
    'hiring_manager': {
        'workflow.view':           PermissionLevel.ALLOW,
        'workflow_execution.view': PermissionLevel.ALLOW,
        'automation_center.view':  PermissionLevel.ALLOW,
    },
    'interviewer': {},
    'viewer': {
        'workflow.view':           PermissionLevel.ALLOW,
        'workflow_execution.view': PermissionLevel.ALLOW,
        'automation_center.view':  PermissionLevel.ALLOW,
    },
}

# ─── Module-scoped visibility (recruiter sees only candidate-related workflows)
_MODULE_SCOPE_MAP: dict[str, list[str]] = {
    'recruiter': ['candidates', 'jobs', 'pipeline'],
    'hiring_manager': ['jobs', 'interviews', 'candidates'],
    'interviewer': ['interviews'],
}


class WorkflowPermissionService:

    # ─── Core check ──────────────────────────────────────────────────────────

    @staticmethod
    def can_user_access_workflow(
        user: 'CustomUser',
        workflow: 'Workflow | None',
        action: str,
        *,
        resource_type: str = 'workflow',
        audit: bool = True,
    ) -> dict:
        """
        Returns:
            {
                'allowed': bool,
                'requires_approval': bool,
                'decision': str,       # 'allowed' | 'denied' | 'approval_required'
                'reason': str,
            }
        """
        tenant_id  = getattr(user, 'tenant_id', None)
        role       = getattr(user, 'role', '')
        workflow_id = getattr(workflow, 'id', None) if workflow else None

        level = WorkflowPermissionService._resolve_permission_level(
            tenant_id=tenant_id,
            role=role,
            resource_type=resource_type,
            action=action,
        )

        # Additional check: restricted action registry.
        # Roles that may request approval even when the base matrix returns DENY.
        _APPROVAL_CAPABLE = {'tenant_admin', 'super_admin', 'hr_manager'}

        restricted = WorkflowPermissionService._get_restricted_action(tenant_id, action)
        if restricted:
            if restricted.requires_admin and role not in ('tenant_admin', 'super_admin'):
                # Only admins may use admin-only actions
                level = PermissionLevel.DENY
            elif restricted.requires_approval:
                # Capable roles get routed to approval flow; others are denied
                level = (
                    PermissionLevel.REQUIRE_APPROVAL
                    if role in _APPROVAL_CAPABLE
                    else PermissionLevel.DENY
                )

        # Module scope check for limited roles
        if level != PermissionLevel.DENY and workflow is not None:
            if not WorkflowPermissionService._passes_module_scope(user, workflow):
                level = PermissionLevel.DENY

        # Build result
        if level == PermissionLevel.ALLOW:
            result = {
                'allowed': True,
                'requires_approval': False,
                'decision': AuditDecision.ALLOWED,
                'reason': 'Permission granted',
            }
        elif level == PermissionLevel.REQUIRE_APPROVAL:
            result = {
                'allowed': False,
                'requires_approval': True,
                'decision': AuditDecision.APPROVAL_REQUIRED,
                'reason': f'Action "{action}" requires approval',
            }
        else:
            result = {
                'allowed': False,
                'requires_approval': False,
                'decision': AuditDecision.DENIED,
                'reason': f'Role "{role}" does not have permission for "{resource_type}.{action}"',
            }

        if audit:
            WorkflowPermissionService._log_audit(
                tenant_id=tenant_id,
                user_id=user.id,
                workflow_id=workflow_id,
                action=action,
                decision=result['decision'],
                reason=result['reason'],
            )

        return result

    # ─── Trigger / action checks ──────────────────────────────────────────────

    @staticmethod
    def can_user_use_trigger(user: 'CustomUser', trigger_event: str) -> dict:
        """
        Critical trigger types (bulk ops, emergency) require elevated role.
        """
        critical_triggers = {
            'bulk_status_change', 'emergency_event', 'mass_communication',
            'cross_module_trigger', 'bulk_rejection', 'offer_automation',
        }
        role = getattr(user, 'role', '')
        is_critical = trigger_event in critical_triggers
        if is_critical and role not in ('tenant_admin', 'super_admin', 'hr_manager'):
            return {
                'allowed': False,
                'requires_approval': True,
                'decision': AuditDecision.APPROVAL_REQUIRED,
                'reason': f'Trigger "{trigger_event}" requires manager-level role',
            }
        return {
            'allowed': True,
            'requires_approval': False,
            'decision': AuditDecision.ALLOWED,
            'reason': 'Trigger access granted',
        }

    @staticmethod
    def can_user_use_action(user: 'CustomUser', action_type: str) -> dict:
        return WorkflowPermissionService.can_user_access_workflow(
            user, None, action_type, audit=False
        )

    # ─── Approval check ───────────────────────────────────────────────────────

    @staticmethod
    def requires_approval(user: 'CustomUser', workflow: 'Workflow | None', action: str) -> bool:
        result = WorkflowPermissionService.can_user_access_workflow(
            user, workflow, action, audit=False
        )
        return result['requires_approval']

    # ─── Visibility helpers ───────────────────────────────────────────────────

    @staticmethod
    def get_visible_workflows(user: 'CustomUser'):
        """
        Return a filtered queryset of workflows the user may see.
        Imports here to avoid circular imports.
        """
        from apps.orchestration_center.models.workflow import Workflow

        role = getattr(user, 'role', '')
        tid  = getattr(user, 'tenant_id', None)
        qs   = Workflow.objects.filter(tenant_id=tid, is_deleted=False)

        if role in ('tenant_admin', 'super_admin'):
            return qs

        # hr_manager sees all
        if role == 'hr_manager':
            return qs

        # Scoped roles: filter by module
        allowed_modules = _MODULE_SCOPE_MAP.get(role, [])
        if not allowed_modules:
            return qs.none()

        return qs.filter(
            Q(tags__overlap=allowed_modules)
            | Q(module_scope__in=allowed_modules)
        )

    @staticmethod
    def get_visible_executions(user: 'CustomUser'):
        """
        Return filtered WorkflowExecution queryset for the given user.
        """
        from apps.orchestration_center.models.workflow import WorkflowExecution

        role = getattr(user, 'role', '')
        tid  = getattr(user, 'tenant_id', None)
        qs   = WorkflowExecution.objects.filter(tenant_id=tid)

        if role in ('tenant_admin', 'super_admin', 'hr_manager'):
            return qs

        visible_workflows = WorkflowPermissionService.get_visible_workflows(user)
        return qs.filter(workflow__in=visible_workflows)

    # ─── Internals ───────────────────────────────────────────────────────────

    @staticmethod
    def _resolve_permission_level(
        tenant_id, role: str, resource_type: str, action: str
    ) -> PermissionLevel:
        """
        Check DB policy rules first; fall back to hardcoded default matrix.
        """
        # Try active DB policy for this tenant
        policy = (
            WorkflowPermissionPolicy.objects
            .filter(tenant_id=tenant_id, is_active=True, is_deleted=False)
            .order_by('-created_at')
            .first()
        )
        if policy:
            rule = (
                WorkflowPermissionRule.objects
                .filter(
                    policy=policy,
                    role_code=role,
                    resource_type=resource_type,
                    action_type=action,
                )
                .first()
            )
            if rule:
                return rule.permission_level

        # Fall back to default matrix
        role_map = _DEFAULT_MATRIX.get(role, {})
        if '__all__' in role_map:
            return role_map['__all__']
        key = f'{resource_type}.{action}'
        return role_map.get(key, PermissionLevel.DENY)

    @staticmethod
    def _get_restricted_action(tenant_id, action_key: str):
        return (
            WorkflowRestrictedAction.objects
            .filter(tenant_id=tenant_id, action_key=action_key, is_deleted=False)
            .first()
        )

    @staticmethod
    def _passes_module_scope(user: 'CustomUser', workflow: 'Workflow') -> bool:
        role = getattr(user, 'role', '')
        allowed_modules = _MODULE_SCOPE_MAP.get(role)
        if allowed_modules is None:
            return True  # no restriction for this role
        workflow_module = getattr(workflow, 'module_scope', None) or ''
        tags = list(getattr(workflow, 'tags', None) or [])
        return (
            workflow_module in allowed_modules
            or any(t in allowed_modules for t in tags)
        )

    @staticmethod
    def _log_audit(
        tenant_id, user_id, workflow_id, action: str, decision: str, reason: str,
        metadata: dict | None = None,
    ) -> None:
        try:
            WorkflowAccessAudit.objects.create(
                tenant_id=tenant_id,
                user_id=user_id,
                workflow_id=workflow_id,
                action_attempted=action,
                decision=decision,
                reason=reason,
                metadata=metadata or {},
            )
        except Exception:
            logger.exception('Failed to write workflow access audit log')

    # ─── Role permission matrix helper ────────────────────────────────────────

    @staticmethod
    def get_role_matrix(tenant_id) -> dict:
        """
        Returns the full matrix of roles × (resource.action) → level
        for the UI role matrix view.
        """
        from apps.automation_permissions.models import ActionType, ResourceType

        roles = [
            'tenant_admin', 'hr_manager', 'recruiter',
            'hiring_manager', 'interviewer', 'viewer',
        ]
        resources = [r.value for r in ResourceType]
        actions   = [a.value for a in ActionType]

        matrix: dict[str, dict[str, str]] = {}
        for role in roles:
            matrix[role] = {}
            for resource in resources:
                for action in actions:
                    level = WorkflowPermissionService._resolve_permission_level(
                        tenant_id, role, resource, action
                    )
                    matrix[role][f'{resource}.{action}'] = level

        return matrix
