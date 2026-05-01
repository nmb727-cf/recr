import uuid
from django.db import models
from shared.models import BaseModel

# ─── Choices ──────────────────────────────────────────────────────────────────

class SandboxRunStatus(models.TextChoices):
    QUEUED    = 'queued',    'Queued'
    RUNNING   = 'running',   'Running'
    COMPLETED = 'completed', 'Completed'
    FAILED    = 'failed',    'Failed'
    CANCELLED = 'cancelled', 'Cancelled'


class SandboxStepStatus(models.TextChoices):
    SUCCESS   = 'success',   'Success'
    FAILED    = 'failed',    'Failed'
    SKIPPED   = 'skipped',   'Skipped'
    SIMULATED = 'simulated', 'Simulated'
    WARNING   = 'warning',   'Warning'


class ArtifactType(models.TextChoices):
    NOTIFICATION     = 'simulated_notification',     'Simulated Notification'
    TASK             = 'simulated_task',             'Simulated Task'
    SLA              = 'simulated_sla',              'Simulated SLA'
    STAGE_CHANGE     = 'simulated_stage_change',     'Simulated Stage Change'
    ESCALATION       = 'simulated_escalation',       'Simulated Escalation'
    OFFER            = 'simulated_offer',            'Simulated Offer'
    DEPENDENCY_TRACE = 'simulated_dependency_trace', 'Simulated Dependency Trace'


class SandboxApprovalStatus(models.TextChoices):
    PENDING  = 'pending',  'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


# ─── Model 1: WorkflowSandboxRun ─────────────────────────────────────────────

class WorkflowSandboxRun(BaseModel):
    """
    Represents a specific simulation execution of a workflow.
    """
    workflow_id      = models.UUIDField(db_index=True)
    version_id       = models.UUIDField(null=True, blank=True)
    run_name         = models.CharField(max_length=255)
    trigger_event    = models.CharField(max_length=128)
    input_context    = models.JSONField(default=dict, blank=True)
    expected_outcome = models.JSONField(default=dict, blank=True)
    actual_outcome   = models.JSONField(default=dict, blank=True)
    status           = models.CharField(
        max_length=20, choices=SandboxRunStatus.choices, default=SandboxRunStatus.QUEUED, db_index=True
    )
    started_at       = models.DateTimeField(null=True, blank=True)
    completed_at     = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Workflow Sandbox Run'
        ordering     = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'workflow_id']),
        ]

    def __str__(self):
        return f'{self.run_name} ({self.status})'


# ─── Model 2: WorkflowSandboxStepLog ──────────────────────────────────────────

class WorkflowSandboxStepLog(models.Model):
    """
    Trace of an individual node execution within a sandbox run.
    """
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sandbox_run      = models.ForeignKey(
        WorkflowSandboxRun,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    node_id          = models.UUIDField(db_index=True)
    step_order       = models.PositiveIntegerField()
    action_type      = models.CharField(max_length=64)
    simulated_input  = models.JSONField(default=dict, blank=True)
    simulated_output = models.JSONField(default=dict, blank=True)
    status           = models.CharField(max_length=20, choices=SandboxStepStatus.choices)
    duration_ms      = models.IntegerField(default=0)
    warning_message  = models.TextField(blank=True)
    error_message    = models.TextField(blank=True)
    executed_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Workflow Sandbox Step Log'
        ordering     = ['sandbox_run', 'step_order']


# ─── Model 3: WorkflowSandboxScenario ─────────────────────────────────────────

class WorkflowSandboxScenario(BaseModel):
    """
    Predefined test cases for specific modules and triggers.
    """
    name              = models.CharField(max_length=255)
    description       = models.TextField(blank=True)
    module_scope      = models.CharField(max_length=64, db_index=True)
    trigger_event     = models.CharField(max_length=128, db_index=True)
    scenario_payload  = models.JSONField(default=dict)
    expected_path     = models.JSONField(default=list, blank=True) # List of node IDs
    expected_actions  = models.JSONField(default=list, blank=True) # List of action types
    is_system_scenario = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = 'Workflow Sandbox Scenario'
        ordering     = ['-is_system_scenario', 'name']


# ─── Model 4: WorkflowSandboxArtifact ─────────────────────────────────────────

class WorkflowSandboxArtifact(BaseModel):
    """
    Simulated outputs generated during a sandbox run.
    """
    sandbox_run      = models.ForeignKey(
        WorkflowSandboxRun,
        on_delete=models.CASCADE,
        related_name='artifacts'
    )
    artifact_type    = models.CharField(max_length=50, choices=ArtifactType.choices)
    artifact_name    = models.CharField(max_length=255)
    artifact_payload = models.JSONField(default=dict)

    class Meta:
        verbose_name = 'Workflow Sandbox Artifact'
        ordering     = ['-created_at']


# ─── Model 5: WorkflowSandboxApproval ─────────────────────────────────────────

class WorkflowSandboxApproval(BaseModel):
    """
    Manual sign-off after a successful sandbox run.
    """
    workflow_id      = models.UUIDField(db_index=True)
    sandbox_run      = models.ForeignKey(
        WorkflowSandboxRun,
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    approval_status  = models.CharField(
        max_length=20, choices=SandboxApprovalStatus.choices, default=SandboxApprovalStatus.PENDING, db_index=True
    )
    reviewed_by      = models.UUIDField(null=True, blank=True)
    review_notes     = models.TextField(blank=True)
    approved_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Workflow Sandbox Approval'
        ordering     = ['-created_at']
