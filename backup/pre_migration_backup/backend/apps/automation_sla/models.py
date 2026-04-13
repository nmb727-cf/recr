import uuid
from django.db import models
from shared.models import BaseModel

# ─── Choices ──────────────────────────────────────────────────────────────────

class SLAModuleScope(models.TextChoices):
    CANDIDATES   = 'candidates',   'Candidates'
    JOBS         = 'jobs',         'Jobs'
    PIPELINE     = 'pipeline',     'Pipeline'
    INTERVIEWS   = 'interviews',   'Interviews'
    OFFERS       = 'offers',       'Offers'
    AGENCIES     = 'agencies',     'Agencies'
    TASKS        = 'tasks',        'Tasks'
    CROSS_MODULE = 'cross_module', 'Cross Module'


class SLAPriority(models.TextChoices):
    LOW      = 'low',      'Low'
    MEDIUM   = 'medium',   'Medium'
    HIGH     = 'high',     'High'
    CRITICAL = 'critical', 'Critical'


class SLAExecutionStatus(models.TextChoices):
    ACTIVE      = 'active',      'Active'
    WARNING_DUE = 'warning_due', 'Warning Due'
    BREACHED    = 'breached',    'Breached'
    ESCALATED   = 'escalated',   'Escalated'
    COMPLETED   = 'completed',   'Completed'
    CANCELLED   = 'cancelled',   'Cancelled'


class SLAReminderType(models.TextChoices):
    WARNING    = 'warning',    'Warning'
    BREACH     = 'breach',     'Breach'
    ESCALATION = 'escalation', 'Escalation'
    FINAL_NOTICE = 'final_notice', 'Final Notice'


class SLAReminderStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    SENT      = 'sent',      'Sent'
    FAILED    = 'failed',    'Failed'
    SKIPPED   = 'skipped',   'Skipped'
    CANCELLED = 'cancelled', 'Cancelled'


class SLABreachInsightType(models.TextChoices):
    REPEATED_BREACH          = 'repeated_breach',          'Repeated Breach'
    HIGH_DELAY_TEAM          = 'high_delay_team',          'High Delay Team'
    SLOW_STAGE_TRANSITION    = 'slow_stage_transition',    'Slow Stage Transition'
    AGENCY_RESPONSE_DELAY    = 'agency_response_delay',    'Agency Response Delay'
    INTERVIEW_FEEDBACK_DELAY = 'interview_feedback_delay', 'Interview Feedback Delay'
    OFFER_RESPONSE_DELAY     = 'offer_response_delay',     'Offer Response Delay'


class SLABreachInsightStatus(models.TextChoices):
    NEW          = 'new',          'New'
    ACKNOWLEDGED = 'acknowledged', 'Acknowledged'
    RESOLVED     = 'resolved',     'Resolved'
    IGNORED      = 'ignored',      'Ignored'


# ─── Model 1: WorkflowSLAPolicy ──────────────────────────────────────────────

class WorkflowSLAPolicy(BaseModel):
    """
    Defines the SLA rules for specific trigger events and modules.
    """
    name                    = models.CharField(max_length=255)
    description             = models.TextField(blank=True)
    module_scope            = models.CharField(max_length=30, choices=SLAModuleScope.choices)
    trigger_event           = models.CharField(max_length=128, db_index=True)
    entity_type             = models.CharField(max_length=64)
    deadline_minutes        = models.PositiveIntegerField()
    warning_before_minutes  = models.PositiveIntegerField(default=60)
    escalation_after_minutes = models.PositiveIntegerField(default=120)
    priority                = models.CharField(max_length=10, choices=SLAPriority.choices, default=SLAPriority.MEDIUM)
    is_active               = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'Workflow SLA Policy'
        ordering     = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'is_active']),
            models.Index(fields=['tenant_id', 'trigger_event']),
        ]

    def __str__(self):
        return self.name


# ─── Model 2: WorkflowSLAExecution ───────────────────────────────────────────

class WorkflowSLAExecution(BaseModel):
    """
    A single SLA tracking instance for a specific entity.
    """
    workflow_id      = models.UUIDField(null=True, blank=True, db_index=True)
    sla_policy       = models.ForeignKey(
        WorkflowSLAPolicy,
        on_delete=models.CASCADE,
        related_name='executions',
    )
    entity_type      = models.CharField(max_length=64, db_index=True)
    entity_id        = models.CharField(max_length=64, db_index=True)
    owner_user_id    = models.UUIDField(null=True, blank=True, db_index=True)
    current_status   = models.CharField(
        max_length=20, choices=SLAExecutionStatus.choices, default=SLAExecutionStatus.ACTIVE, db_index=True
    )
    started_at       = models.DateTimeField(auto_now_add=True, db_index=True)
    due_at           = models.DateTimeField(db_index=True)
    warning_at       = models.DateTimeField(null=True, blank=True, db_index=True)
    breached_at      = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_at     = models.DateTimeField(null=True, blank=True, db_index=True)
    escalation_level = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Workflow SLA Execution'
        ordering     = ['-started_at']
        indexes = [
            models.Index(fields=['tenant_id', 'current_status']),
            models.Index(fields=['tenant_id', 'due_at']),
        ]

    def __str__(self):
        return f'{self.sla_policy.name} for {self.entity_type}:{self.entity_id}'


# ─── Model 3: WorkflowSLAReminder ────────────────────────────────────────────

class WorkflowSLAReminder(BaseModel):
    """
    Scheduled or sent reminders for an SLA execution.
    """
    sla_execution    = models.ForeignKey(
        WorkflowSLAExecution,
        on_delete=models.CASCADE,
        related_name='reminders',
    )
    reminder_type    = models.CharField(max_length=20, choices=SLAReminderType.choices)
    recipient_type   = models.CharField(max_length=50) # owner, manager, admin
    channel          = models.CharField(max_length=20, default='in_app') # email, slack, push, in_app
    scheduled_at     = models.DateTimeField(db_index=True)
    sent_at          = models.DateTimeField(null=True, blank=True)
    status           = models.CharField(
        max_length=20, choices=SLAReminderStatus.choices, default=SLAReminderStatus.SCHEDULED, db_index=True
    )

    class Meta:
        verbose_name = 'Workflow SLA Reminder'
        ordering     = ['scheduled_at']


# ─── Model 4: WorkflowSLAEscalationRule ──────────────────────────────────────

class WorkflowSLAEscalationRule(BaseModel):
    """
    Rules defining who to notify when an SLA is breached.
    """
    sla_policy          = models.ForeignKey(
        WorkflowSLAPolicy,
        on_delete=models.CASCADE,
        related_name='escalation_rules',
    )
    escalation_level    = models.PositiveSmallIntegerField(default=1)
    escalate_after_minutes = models.PositiveIntegerField()
    target_role         = models.CharField(max_length=50, blank=True)
    target_user_id      = models.UUIDField(null=True, blank=True)
    notification_template_id = models.CharField(max_length=100, blank=True)
    is_active           = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Workflow SLA Escalation Rule'
        unique_together = [('sla_policy', 'escalation_level')]
        ordering     = ['sla_policy', 'escalation_level']


# ─── Model 5: WorkflowSLABreachInsight ───────────────────────────────────────

class WorkflowSLABreachInsight(BaseModel):
    """
    System-generated insights based on SLA performance.
    """
    sla_policy       = models.ForeignKey(
        WorkflowSLAPolicy,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='breach_insights',
    )
    workflow_id      = models.UUIDField(null=True, blank=True, db_index=True)
    insight_type     = models.CharField(max_length=50, choices=SLABreachInsightType.choices)
    title            = models.CharField(max_length=255)
    description      = models.TextField()
    breach_count     = models.PositiveIntegerField(default=0)
    impacted_module  = models.CharField(max_length=30, choices=SLAModuleScope.choices)
    suggested_fix    = models.TextField(blank=True)
    status           = models.CharField(
        max_length=20, choices=SLABreachInsightStatus.choices, default=SLABreachInsightStatus.NEW, db_index=True
    )

    class Meta:
        verbose_name = 'Workflow SLA Breach Insight'
        ordering     = ['-created_at']
