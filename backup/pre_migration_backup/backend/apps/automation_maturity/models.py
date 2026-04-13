from django.db import models
from shared.models import BaseModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MaturityLevel(models.TextChoices):
    MANUAL      = 'manual',      'Manual'
    ASSISTED    = 'assisted',    'Assisted'
    STRUCTURED  = 'structured',  'Structured'
    OPTIMIZED   = 'optimized',   'Optimized'
    AUTONOMOUS  = 'autonomous',  'Autonomous'


class ModuleScope(models.TextChoices):
    CANDIDATES   = 'candidates',   'Candidates'
    JOBS         = 'jobs',         'Jobs'
    PIPELINE     = 'pipeline',     'Pipeline'
    INTERVIEWS   = 'interviews',   'Interviews'
    OFFERS       = 'offers',       'Offers'
    AGENCIES     = 'agencies',     'Agencies'
    TASKS        = 'tasks',        'Tasks'
    SLA          = 'sla',          'SLA'
    NOTIFICATIONS= 'notifications','Notifications'
    CROSS_MODULE = 'cross_module', 'Cross Module'


class RecommendationType(models.TextChoices):
    INCREASE_COVERAGE     = 'increase_coverage',     'Increase Coverage'
    IMPROVE_GOVERNANCE    = 'improve_governance',    'Improve Governance'
    IMPROVE_RELIABILITY   = 'improve_reliability',   'Improve Reliability'
    ENABLE_PLAYBOOKS      = 'enable_playbooks',      'Enable Playbooks'
    EXPAND_CROSS_MODULE   = 'expand_cross_module',   'Expand Cross Module'
    IMPROVE_SLA_USAGE     = 'improve_sla_usage',     'Improve SLA Usage'
    INCREASE_AI_ADOPTION  = 'increase_ai_adoption',  'Increase AI Adoption'
    STRENGTHEN_SANDBOX    = 'strengthen_sandbox_usage', 'Strengthen Sandbox Usage'


class RecommendationPriority(models.TextChoices):
    LOW      = 'low',      'Low'
    MEDIUM   = 'medium',   'Medium'
    HIGH     = 'high',     'High'
    CRITICAL = 'critical', 'Critical'


class RecommendationStatus(models.TextChoices):
    NEW          = 'new',          'New'
    ACKNOWLEDGED = 'acknowledged', 'Acknowledged'
    IN_PROGRESS  = 'in_progress',  'In Progress'
    COMPLETED    = 'completed',    'Completed'
    IGNORED      = 'ignored',      'Ignored'


# ---------------------------------------------------------------------------
# Model 1 — AutomationMaturityAssessment
# ---------------------------------------------------------------------------

class AutomationMaturityAssessment(BaseModel):
    """Tenant-level overall maturity snapshot."""
    assessment_date      = models.DateField(db_index=True)
    overall_maturity_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    maturity_level       = models.CharField(
        max_length=20, choices=MaturityLevel.choices, default=MaturityLevel.MANUAL, db_index=True
    )
    coverage_score     = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    adoption_score     = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    governance_score   = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    reliability_score  = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    intelligence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    operating_score    = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    business_impact_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    score_breakdown    = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_maturity_assessments'
        ordering = ['-assessment_date']
        indexes = [
            models.Index(fields=['tenant_id', 'assessment_date']),
            models.Index(fields=['tenant_id', 'maturity_level']),
        ]


# ---------------------------------------------------------------------------
# Model 2 — AutomationModuleMaturity
# ---------------------------------------------------------------------------

class AutomationModuleMaturity(BaseModel):
    """Per-module maturity snapshot (refreshed on each assessment)."""
    assessment         = models.ForeignKey(
        AutomationMaturityAssessment, on_delete=models.CASCADE, related_name='module_scores'
    )
    module_scope            = models.CharField(max_length=30, choices=ModuleScope.choices, db_index=True)
    maturity_score          = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    maturity_level          = models.CharField(max_length=20, choices=MaturityLevel.choices, default=MaturityLevel.MANUAL)
    automation_coverage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    workflow_count          = models.PositiveIntegerField(default=0)
    playbook_count          = models.PositiveIntegerField(default=0)
    reliability_score       = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    governance_score        = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = 'wf_maturity_module_scores'
        ordering = ['-maturity_score']
        indexes = [
            models.Index(fields=['tenant_id', 'module_scope']),
            models.Index(fields=['tenant_id', 'assessment_id']),
        ]


# ---------------------------------------------------------------------------
# Model 3 — AutomationTeamAdoption
# ---------------------------------------------------------------------------

class AutomationTeamAdoption(BaseModel):
    """Per-team / per-user-group adoption metrics."""
    assessment          = models.ForeignKey(
        AutomationMaturityAssessment, on_delete=models.CASCADE, related_name='team_scores'
    )
    team_name           = models.CharField(max_length=200)
    department_id       = models.UUIDField(null=True, blank=True)
    adoption_score      = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    active_user_count   = models.PositiveIntegerField(default=0)
    workflow_usage_count= models.PositiveIntegerField(default=0)
    playbook_usage_count= models.PositiveIntegerField(default=0)
    manual_override_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'wf_maturity_team_adoption'
        ordering = ['-adoption_score']
        indexes = [
            models.Index(fields=['tenant_id', 'assessment_id']),
        ]


# ---------------------------------------------------------------------------
# Model 4 — AutomationMaturityRecommendation
# ---------------------------------------------------------------------------

class AutomationMaturityRecommendation(BaseModel):
    recommendation_type   = models.CharField(max_length=40, choices=RecommendationType.choices)
    title                 = models.CharField(max_length=255)
    description           = models.TextField()
    target_area           = models.CharField(max_length=100)
    expected_maturity_gain= models.DecimalField(max_digits=5, decimal_places=2, default=0)
    priority              = models.CharField(
        max_length=20, choices=RecommendationPriority.choices, default=RecommendationPriority.MEDIUM, db_index=True
    )
    status                = models.CharField(
        max_length=20, choices=RecommendationStatus.choices, default=RecommendationStatus.NEW, db_index=True
    )

    class Meta:
        db_table = 'wf_maturity_recommendations'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'priority']),
            models.Index(fields=['tenant_id', 'recommendation_type']),
        ]


# ---------------------------------------------------------------------------
# Model 5 — AutomationMaturityRoadmap
# ---------------------------------------------------------------------------

class AutomationMaturityRoadmap(BaseModel):
    roadmap_name          = models.CharField(max_length=255)
    current_level         = models.CharField(max_length=20, choices=MaturityLevel.choices)
    target_level          = models.CharField(max_length=20, choices=MaturityLevel.choices)
    roadmap_steps         = models.JSONField(default=list)
    expected_timeline_days= models.PositiveIntegerField(default=90)
    created_by            = models.UUIDField(null=True, blank=True)
    is_active             = models.BooleanField(default=True)

    class Meta:
        db_table = 'wf_maturity_roadmaps'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'is_active']),
        ]


# ---------------------------------------------------------------------------
# Model 6 — AutomationBusinessTransformationMetric
# ---------------------------------------------------------------------------

class AutomationBusinessTransformationMetric(BaseModel):
    metric_date                      = models.DateField(db_index=True)
    process_name                     = models.CharField(max_length=200)
    manual_effort_reduction_percent  = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    response_time_improvement_percent= models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sla_improvement_percent          = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    automation_usage_percent         = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    executions_this_period           = models.PositiveIntegerField(default=0)
    baseline_executions              = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'wf_maturity_transformation_metrics'
        ordering = ['-metric_date']
        indexes = [
            models.Index(fields=['tenant_id', 'metric_date']),
            models.Index(fields=['tenant_id', 'process_name']),
        ]
