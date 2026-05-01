import uuid
from django.db import models
from shared.models import BaseModel

# ─── Choices ──────────────────────────────────────────────────────────────────

class PlaybookCategory(models.TextChoices):
    CANDIDATE    = 'candidate',    'Candidate'
    INTERVIEW    = 'interview',    'Interview'
    OFFER        = 'offer',        'Offer'
    AGENCY       = 'agency',       'Agency'
    RECRUITER    = 'recruiter',    'Recruiter'
    SLA          = 'sla',          'SLA'
    EXECUTIVE    = 'executive',    'Executive'
    CROSS_MODULE = 'cross_module', 'Cross Module'


class PlaybookType(models.TextChoices):
    SYSTEM_DEFAULT = 'system_default', 'System Default'
    TENANT_CUSTOM  = 'tenant_custom',  'Tenant Custom'
    RECOMMENDED    = 'recommended',    'Recommended'
    IMPORTED       = 'imported',       'Imported'


class PlaybookItemType(models.TextChoices):
    WORKFLOW          = 'workflow',          'Workflow'
    NOTIFICATION_RULE = 'notification_rule', 'Notification Rule'
    TASK_RULE         = 'task_rule',         'Task Rule'
    SLA_POLICY        = 'sla_policy',        'SLA Policy'
    GOVERNANCE_RULE   = 'governance_rule',   'Governance Rule'
    PERMISSION_POLICY = 'permission_policy', 'Permission Policy'
    ANALYTICS_VIEW    = 'analytics_view',    'Analytics View'


class InstallStatus(models.TextChoices):
    DRAFT       = 'draft',       'Draft'
    INSTALLING  = 'installing',  'Installing'
    INSTALLED   = 'installed',   'Installed'
    PARTIAL     = 'partial',     'Partial'
    FAILED      = 'failed',      'Failed'
    ROLLED_BACK = 'rolled_back', 'Rolled Back'


class RecommendationSource(models.TextChoices):
    AI_INSIGHT         = 'ai_insight',         'AI Insight'
    ADMIN_DEFAULT      = 'admin_default',      'Admin Default'
    USAGE_PATTERN      = 'usage_pattern',      'Usage Pattern'
    MODULE_GAP         = 'module_gap',         'Module Gap'
    SLA_BREACH_PATTERN = 'sla_breach_pattern', 'SLA Breach Pattern'


class RecommendationStatus(models.TextChoices):
    NEW       = 'new',       'New'
    VIEWED    = 'viewed',    'Viewed'
    ACCEPTED  = 'accepted',  'Accepted'
    DISMISSED = 'dismissed', 'Dismissed'


# ─── Model 1: AutomationPlaybook ─────────────────────────────────────────────

class AutomationPlaybook(BaseModel):
    """
    High-level definition of a reusable automation bundle.
    """
    name               = models.CharField(max_length=255)
    description        = models.TextField(blank=True)
    category           = models.CharField(max_length=30, choices=PlaybookCategory.choices)
    module_scope       = models.CharField(max_length=100, blank=True)
    playbook_type      = models.CharField(max_length=30, choices=PlaybookType.choices, default=PlaybookType.SYSTEM_DEFAULT)
    version            = models.CharField(max_length=20, default='1.0.0')
    config_schema      = models.JSONField(default=dict, blank=True) # JSON Schema for guided setup
    playbook_payload   = models.JSONField(default=dict, blank=True) # Full bundle structure
    is_system_playbook = models.BooleanField(default=False, db_index=True)
    is_active          = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'Automation Playbook'
        ordering     = ['category', 'name']
        indexes = [
            models.Index(fields=['is_system_playbook', 'is_active']),
        ]

    def __str__(self):
        return f'{self.name} (v{self.version})'


# ─── Model 2: AutomationPlaybookItem ──────────────────────────────────────────

class AutomationPlaybookItem(models.Model):
    """
    Individual components within a playbook (Workflows, SLAs, etc).
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    playbook        = models.ForeignKey(
        AutomationPlaybook,
        on_delete=models.CASCADE,
        related_name='items'
    )
    item_type       = models.CharField(max_length=30, choices=PlaybookItemType.choices)
    item_key        = models.CharField(max_length=100, db_index=True)
    item_name       = models.CharField(max_length=255)
    config_payload  = models.JSONField(default=dict, blank=True)
    execution_order = models.PositiveIntegerField(default=0)
    is_required     = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Automation Playbook Item'
        ordering     = ['playbook', 'execution_order']

    def __str__(self):
        return f'{self.item_name} ({self.item_type})'


# ─── Model 3: AutomationPlaybookInstall ───────────────────────────────────────

class AutomationPlaybookInstall(BaseModel):
    """
    Tracks the installation of a playbook for a specific tenant.
    """
    playbook               = models.ForeignKey(
        AutomationPlaybook,
        on_delete=models.PROTECT,
        related_name='installs'
    )
    install_status         = models.CharField(max_length=20, choices=InstallStatus.choices, default=InstallStatus.DRAFT)
    installed_by           = models.UUIDField(null=True, blank=True)
    installed_at           = models.DateTimeField(null=True, blank=True)
    completed_at           = models.DateTimeField(null=True, blank=True)
    config_snapshot        = models.JSONField(default=dict, blank=True) # User-provided config values
    created_workflow_count = models.PositiveIntegerField(default=0)
    created_rule_count     = models.PositiveIntegerField(default=0)
    failure_reason         = models.TextField(blank=True)
    
    # Store IDs of created items for rollback
    created_entities_json  = models.JSONField(default=dict, blank=True) 

    class Meta:
        verbose_name = 'Automation Playbook Install'
        ordering     = ['-created_at']


# ─── Model 4: AutomationPlaybookRecommendation ────────────────────────────────

class AutomationPlaybookRecommendation(BaseModel):
    """
    AI or system recommendations for specific playbooks.
    """
    playbook              = models.ForeignKey(
        AutomationPlaybook,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    recommendation_reason = models.TextField()
    confidence_score      = models.FloatField(default=0.0)
    source_type           = models.CharField(max_length=30, choices=RecommendationSource.choices)
    status                = models.CharField(
        max_length=20, choices=RecommendationStatus.choices, default=RecommendationStatus.NEW
    )

    class Meta:
        verbose_name = 'Automation Playbook Recommendation'
        ordering     = ['-confidence_score', '-created_at']


# ─── Model 5: AutomationPlaybookAnalytics ─────────────────────────────────────

class AutomationPlaybookAnalytics(BaseModel):
    """
    Performance tracking for playbooks across the system.
    """
    playbook        = models.ForeignKey(
        AutomationPlaybook,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    snapshot_date   = models.DateField(db_index=True)
    install_count   = models.PositiveIntegerField(default=0)
    active_count    = models.PositiveIntegerField(default=0)
    workflow_count  = models.PositiveIntegerField(default=0)
    execution_count = models.PositiveIntegerField(default=0)
    success_rate    = models.FloatField(default=0.0)
    failure_rate    = models.FloatField(default=0.0)
    impact_summary  = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Automation Playbook Analytics'
        unique_together = ('tenant_id', 'playbook', 'snapshot_date')
        ordering     = ['-snapshot_date']
