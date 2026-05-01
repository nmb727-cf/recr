import uuid
from django.db import models
from shared.models import BaseModel


# ─── Choices ──────────────────────────────────────────────────────────────────

class AssigneeType(models.TextChoices):
    ASSIGNED_RECRUITER = 'assigned_recruiter', 'Assigned Recruiter'
    HIRING_MANAGER     = 'hiring_manager',     'Hiring Manager'
    RECRUITER_MANAGER  = 'recruiter_manager',  'Recruiter Manager'
    WORKFLOW_OWNER     = 'workflow_owner',     'Workflow Owner'
    SPECIFIC_USER      = 'specific_user',      'Specific User'
    DYNAMIC_FIELD      = 'dynamic_field',      'Dynamic Field'


class TaskPriority(models.TextChoices):
    LOW    = 'low',    'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH   = 'high',   'High'
    URGENT = 'urgent', 'Urgent'


class TaskStatus(models.TextChoices):
    PENDING     = 'pending',     'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED   = 'completed',   'Completed'
    OVERDUE     = 'overdue',     'Overdue'
    CANCELLED   = 'cancelled',   'Cancelled'
    ESCALATED   = 'escalated',   'Escalated'


# ─── Model 1: WorkflowTaskRule ────────────────────────────────────────────────

class WorkflowTaskRule(BaseModel):
    """
    Defines what task should be created when a workflow node fires.
    """
    workflow_id               = models.UUIDField(db_index=True)
    node_id                   = models.CharField(max_length=100, blank=True)
    task_title_template       = models.CharField(max_length=500)
    task_description_template = models.TextField(blank=True)
    assignee_type             = models.CharField(max_length=30, choices=AssigneeType.choices)
    assignee_field            = models.CharField(max_length=100, blank=True)  # used when assignee_type=dynamic_field
    priority                  = models.CharField(max_length=10, choices=TaskPriority.choices, default=TaskPriority.MEDIUM)
    due_in_minutes            = models.PositiveIntegerField(default=1440)      # 24 h default
    escalate_after_minutes    = models.PositiveIntegerField(default=2880)      # 48 h default
    is_active                 = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'Workflow Task Rule'
        ordering     = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'workflow_id']),
            models.Index(fields=['tenant_id', 'is_active']),
        ]

    def __str__(self):
        return self.task_title_template[:80]


# ─── Model 2: WorkflowTaskExecution ──────────────────────────────────────────

class WorkflowTaskExecution(models.Model):
    """
    A single task instance created by the orchestrator.
    """
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id        = models.UUIDField(db_index=True)
    workflow_id      = models.UUIDField(db_index=True)
    execution_id     = models.UUIDField(null=True, blank=True, db_index=True)
    rule             = models.ForeignKey(
        WorkflowTaskRule,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='executions',
    )
    task_title       = models.CharField(max_length=500)
    task_description = models.TextField(blank=True)
    assignee_user_id = models.UUIDField(null=True, blank=True, db_index=True)
    priority         = models.CharField(max_length=10, choices=TaskPriority.choices, default=TaskPriority.MEDIUM, db_index=True)
    due_at           = models.DateTimeField(null=True, blank=True, db_index=True)
    status           = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING, db_index=True)
    escalated        = models.BooleanField(default=False, db_index=True)
    completed_at     = models.DateTimeField(null=True, blank=True)
    context_snapshot = models.JSONField(default=dict, blank=True)   # stores workflow payload at creation
    metadata         = models.JSONField(default=dict, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Workflow Task Execution'
        ordering     = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'assignee_user_id']),
            models.Index(fields=['tenant_id', 'priority', 'status']),
            models.Index(fields=['tenant_id', 'due_at', 'status']),
        ]

    def __str__(self):
        return f'{self.task_title[:60]} [{self.status}]'


# ─── Model 3: WorkflowTaskEscalation ─────────────────────────────────────────

class WorkflowTaskEscalation(models.Model):
    """
    Records each escalation event for a task execution.
    """
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id           = models.UUIDField(db_index=True)
    task_execution      = models.ForeignKey(
        WorkflowTaskExecution,
        on_delete=models.CASCADE,
        related_name='escalations',
    )
    escalation_level    = models.PositiveSmallIntegerField(default=1)
    escalated_to        = models.UUIDField(null=True, blank=True)     # user_id of escalation target
    escalated_to_role   = models.CharField(max_length=50, blank=True) # human-readable role label
    reason              = models.TextField(blank=True)
    escalated_at        = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Workflow Task Escalation'
        ordering     = ['task_execution', 'escalation_level']
        indexes = [
            models.Index(fields=['tenant_id', 'escalated_at']),
        ]

    def __str__(self):
        return f'L{self.escalation_level} escalation → task {self.task_execution_id}'


# ─── Model 4: WorkflowTaskDependency ─────────────────────────────────────────

class WorkflowTaskDependency(models.Model):
    """
    Defines a dependency between two task executions.
    The dependent task is only started when its dependency is completed.
    """
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id           = models.UUIDField(db_index=True)
    task_execution      = models.ForeignKey(
        WorkflowTaskExecution,
        on_delete=models.CASCADE,
        related_name='dependencies',
    )
    depends_on_task     = models.ForeignKey(
        WorkflowTaskExecution,
        on_delete=models.CASCADE,
        related_name='unlocks',
    )
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Workflow Task Dependency'
        unique_together = [('task_execution', 'depends_on_task')]
        indexes = [
            models.Index(fields=['tenant_id']),
        ]

    def __str__(self):
        return f'{self.task_execution_id} depends on {self.depends_on_task_id}'
