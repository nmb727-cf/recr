from django.db import models
from shared.models import BaseModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskType(models.TextChoices):
    FAILURE_SPIKE     = 'failure_spike',     'Failure Spike'
    DEPENDENCY_RISK   = 'dependency_risk',   'Dependency Risk'
    WORKFLOW_CONFLICT = 'workflow_conflict',  'Workflow Conflict'
    GOVERNANCE_GAP    = 'governance_gap',    'Governance Gap'
    MANUAL_GAP        = 'manual_gap',        'Manual Gap'
    OVERLOAD_RISK     = 'overload_risk',     'Overload Risk'


class RiskSeverity(models.TextChoices):
    LOW      = 'low',      'Low'
    MEDIUM   = 'medium',   'Medium'
    HIGH     = 'high',     'High'
    CRITICAL = 'critical', 'Critical'


class RiskStatus(models.TextChoices):
    OPEN          = 'open',          'Open'
    ACKNOWLEDGED  = 'acknowledged',  'Acknowledged'
    MITIGATED     = 'mitigated',     'Mitigated'
    RESOLVED      = 'resolved',      'Resolved'
    IGNORED       = 'ignored',       'Ignored'


class OpportunityType(models.TextChoices):
    AUTOMATE_MANUAL    = 'automate_manual_process', 'Automate Manual Process'
    EXPAND_WORKFLOW    = 'expand_existing_workflow', 'Expand Existing Workflow'
    ENABLE_CROSS_MODULE= 'enable_cross_module',      'Enable Cross-Module Automation'
    IMPROVE_RELIABILITY= 'improve_reliability',       'Improve Reliability'
    ENABLE_AI          = 'enable_ai',                'Enable AI Automation'


class OpportunityPriority(models.TextChoices):
    LOW      = 'low',      'Low'
    MEDIUM   = 'medium',   'Medium'
    HIGH     = 'high',     'High'
    CRITICAL = 'critical', 'Critical'


class OpportunityStatus(models.TextChoices):
    NEW        = 'new',        'New'
    ASSIGNED   = 'assigned',   'Assigned'
    IN_PROGRESS= 'in_progress','In Progress'
    COMPLETED  = 'completed',  'Completed'
    DISMISSED  = 'dismissed',  'Dismissed'


class ROIPeriod(models.TextChoices):
    DAILY   = 'daily',   'Daily'
    WEEKLY  = 'weekly',  'Weekly'
    MONTHLY = 'monthly', 'Monthly'
    YEARLY  = 'yearly',  'Yearly'


# ---------------------------------------------------------------------------
# Model 1 — ExecutiveAutomationSummary
# ---------------------------------------------------------------------------

class ExecutiveAutomationSummary(BaseModel):
    """Daily snapshot of tenant-wide executive KPIs."""
    snapshot_date              = models.DateField(db_index=True)
    total_workflows            = models.PositiveIntegerField(default=0)
    active_workflows           = models.PositiveIntegerField(default=0)
    total_executions_today     = models.PositiveIntegerField(default=0)
    successful_executions_today= models.PositiveIntegerField(default=0)
    automation_coverage_percent= models.DecimalField(max_digits=5, decimal_places=2, default=0)
    automation_maturity_level  = models.CharField(max_length=20, default='manual')
    time_saved_hours           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tasks_automated            = models.PositiveIntegerField(default=0)
    sla_improvement_percent    = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    open_risks                 = models.PositiveIntegerField(default=0)
    open_opportunities         = models.PositiveIntegerField(default=0)
    business_impact_score      = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = 'exec_automation_summary'
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['tenant_id', 'snapshot_date']),
        ]


# ---------------------------------------------------------------------------
# Model 2 — ExecutiveAutomationROI
# ---------------------------------------------------------------------------

class ExecutiveAutomationROI(BaseModel):
    period                     = models.CharField(max_length=10, choices=ROIPeriod.choices, default=ROIPeriod.MONTHLY)
    period_start               = models.DateField(db_index=True)
    period_end                 = models.DateField()
    hours_saved                = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    manual_tasks_reduced       = models.PositiveIntegerField(default=0)
    operational_cost_reduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    productivity_gain_percent  = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    executions_count           = models.PositiveIntegerField(default=0)
    success_rate               = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = 'exec_automation_roi'
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['tenant_id', 'period', 'period_start']),
        ]


# ---------------------------------------------------------------------------
# Model 3 — ExecutiveAutomationRisk
# ---------------------------------------------------------------------------

class ExecutiveAutomationRisk(BaseModel):
    risk_type       = models.CharField(max_length=30, choices=RiskType.choices, db_index=True)
    severity        = models.CharField(max_length=20, choices=RiskSeverity.choices, default=RiskSeverity.MEDIUM, db_index=True)
    affected_module = models.CharField(max_length=100, blank=True)
    title           = models.CharField(max_length=255)
    description     = models.TextField()
    status          = models.CharField(max_length=20, choices=RiskStatus.choices, default=RiskStatus.OPEN, db_index=True)
    metric_value    = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'exec_automation_risks'
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'severity']),
            models.Index(fields=['tenant_id', 'risk_type']),
        ]


# ---------------------------------------------------------------------------
# Model 4 — ExecutiveAutomationDepartment
# ---------------------------------------------------------------------------

class ExecutiveAutomationDepartment(BaseModel):
    snapshot_date       = models.DateField(db_index=True)
    department_name     = models.CharField(max_length=200)
    automation_coverage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    adoption_score      = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    maturity_level      = models.CharField(max_length=20, default='manual')
    manual_gap_percent  = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    workflow_count      = models.PositiveIntegerField(default=0)
    executions_30d      = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'exec_automation_departments'
        ordering = ['-automation_coverage']
        indexes = [
            models.Index(fields=['tenant_id', 'snapshot_date']),
            models.Index(fields=['tenant_id', 'department_name']),
        ]


# ---------------------------------------------------------------------------
# Model 5 — ExecutiveAutomationOpportunity
# ---------------------------------------------------------------------------

class ExecutiveAutomationOpportunity(BaseModel):
    opportunity_type = models.CharField(max_length=40, choices=OpportunityType.choices)
    module           = models.CharField(max_length=100)
    title            = models.CharField(max_length=255)
    description      = models.TextField()
    expected_impact  = models.CharField(max_length=255)
    priority         = models.CharField(max_length=20, choices=OpportunityPriority.choices, default=OpportunityPriority.MEDIUM, db_index=True)
    status           = models.CharField(max_length=20, choices=OpportunityStatus.choices, default=OpportunityStatus.NEW, db_index=True)
    assigned_to      = models.UUIDField(null=True, blank=True)
    source_data      = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'exec_automation_opportunities'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'priority']),
            models.Index(fields=['tenant_id', 'opportunity_type']),
        ]
