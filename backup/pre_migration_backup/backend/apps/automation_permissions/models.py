import uuid
from django.db import models
from shared.models import BaseModel


# ─── Choice constants ─────────────────────────────────────────────────────────

class ResourceType(models.TextChoices):
    WORKFLOW            = 'workflow',            'Workflow'
    WORKFLOW_TEMPLATE   = 'workflow_template',   'Workflow Template'
    WORKFLOW_EXECUTION  = 'workflow_execution',  'Workflow Execution'
    WORKFLOW_GOVERNANCE = 'workflow_governance', 'Workflow Governance'
    WORKFLOW_ANALYTICS  = 'workflow_analytics',  'Workflow Analytics'
    AUTOMATION_CENTER   = 'automation_center',   'Automation Center'


class ActionType(models.TextChoices):
    VIEW           = 'view',           'View'
    CREATE         = 'create',         'Create'
    EDIT           = 'edit',           'Edit'
    DELETE         = 'delete',         'Delete'
    ACTIVATE       = 'activate',       'Activate'
    PAUSE          = 'pause',          'Pause'
    ARCHIVE        = 'archive',        'Archive'
    DUPLICATE      = 'duplicate',      'Duplicate'
    IMPORT_TEMPLATE= 'import_template','Import Template'
    EMERGENCY_STOP = 'emergency_stop', 'Emergency Stop'
    ROLLBACK       = 'rollback',       'Rollback'
    APPROVE        = 'approve',        'Approve'
    DRY_RUN        = 'dry_run',        'Dry Run'
    VIEW_LOGS      = 'view_logs',      'View Logs'
    VIEW_ANALYTICS = 'view_analytics', 'View Analytics'


class PermissionLevel(models.TextChoices):
    ALLOW            = 'allow',            'Allow'
    DENY             = 'deny',             'Deny'
    REQUIRE_APPROVAL = 'require_approval', 'Require Approval'


class Severity(models.TextChoices):
    LOW      = 'low',      'Low'
    MEDIUM   = 'medium',   'Medium'
    HIGH     = 'high',     'High'
    CRITICAL = 'critical', 'Critical'


class AuditDecision(models.TextChoices):
    ALLOWED          = 'allowed',          'Allowed'
    DENIED           = 'denied',           'Denied'
    APPROVAL_REQUIRED= 'approval_required','Approval Required'


# ─── Model 1: WorkflowPermissionPolicy ───────────────────────────────────────

class WorkflowPermissionPolicy(BaseModel):
    """
    Top-level policy container. One active policy per tenant governs
    all automation RBAC decisions.
    """
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name        = 'Workflow Permission Policy'
        verbose_name_plural = 'Workflow Permission Policies'
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'is_active']),
        ]

    def __str__(self):
        return self.name


# ─── Model 2: WorkflowPermissionRule ─────────────────────────────────────────

class WorkflowPermissionRule(models.Model):
    """
    Individual rule inside a policy: role × resource × action → permission level.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy       = models.ForeignKey(
        WorkflowPermissionPolicy,
        on_delete=models.CASCADE,
        related_name='rules',
    )
    role_code        = models.CharField(max_length=100)          # e.g. hr_manager
    module_scope     = models.CharField(max_length=100, blank=True)  # e.g. candidates
    resource_type    = models.CharField(max_length=50, choices=ResourceType.choices)
    action_type      = models.CharField(max_length=50, choices=ActionType.choices)
    permission_level = models.CharField(
        max_length=30,
        choices=PermissionLevel.choices,
        default=PermissionLevel.DENY,
    )
    conditions  = models.JSONField(default=dict, blank=True)     # optional JSON conditions
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Workflow Permission Rule'
        ordering     = ['role_code', 'resource_type', 'action_type']
        indexes = [
            models.Index(fields=['policy', 'role_code']),
            models.Index(fields=['role_code', 'resource_type', 'action_type']),
        ]

    def __str__(self):
        return f'{self.role_code} | {self.resource_type}.{self.action_type} → {self.permission_level}'


# ─── Model 3: WorkflowRestrictedAction ───────────────────────────────────────

class WorkflowRestrictedAction(BaseModel):
    """
    Registry of actions that require elevated control — approval, admin-only, or both.
    """
    action_key        = models.CharField(max_length=100, unique=True)
    description       = models.TextField(blank=True)
    severity          = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    requires_approval = models.BooleanField(default=True)
    requires_admin    = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Workflow Restricted Action'
        ordering     = ['-severity', 'action_key']
        indexes = [
            models.Index(fields=['tenant_id', 'severity']),
        ]

    def __str__(self):
        return f'{self.action_key} ({self.severity})'


# ─── Model 4: WorkflowAccessAudit ────────────────────────────────────────────

class WorkflowAccessAudit(models.Model):
    """
    Immutable audit trail of every permission decision for sensitive actions.
    """
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id        = models.UUIDField(db_index=True)
    user_id          = models.UUIDField(db_index=True)
    workflow_id      = models.UUIDField(null=True, blank=True, db_index=True)
    action_attempted = models.CharField(max_length=100)
    decision         = models.CharField(max_length=30, choices=AuditDecision.choices)
    reason           = models.TextField(blank=True)
    metadata         = models.JSONField(default=dict, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Workflow Access Audit'
        ordering     = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'created_at']),
            models.Index(fields=['tenant_id', 'user_id']),
            models.Index(fields=['tenant_id', 'decision']),
        ]

    def __str__(self):
        return f'{self.action_attempted} → {self.decision} ({self.created_at:%Y-%m-%d %H:%M})'
