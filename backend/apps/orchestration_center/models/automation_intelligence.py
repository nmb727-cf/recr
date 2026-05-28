from django.db import models
from uuid import uuid4

from apps.orchestration_center.constants.execution_statuses import SuggestionCategory
from shared.models import BaseModel


AUTOMATION_LEVEL_CHOICES = [
    ('suggest_only', 'Suggest Only'),
    ('auto_approve', 'Auto Approve'),
    ('auto_apply', 'Auto Apply'),
]

RISK_LEVEL_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]

CATEGORY_CHOICES = [
    ('candidate_followup', 'Candidate Follow-up'),
    ('deadline_management', 'Deadline Management'),
    ('escalation', 'Escalation'),
    ('review_workflow', 'Review Workflow'),
    ('communication', 'Communication'),
    ('interview_followup', 'Interview Follow-up'),
    ('decision_support', 'Decision Support'),
]


class AutomationTemplate(BaseModel):
    """
    Reusable automation rule presets for enterprise users.
    """
    template_key = models.CharField(max_length=64, db_index=True, default='manual_setup')
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64, choices=CATEGORY_CHOICES, db_index=True, default='communication')
    trigger_type = models.CharField(max_length=64, db_index=True, default='manual')
    action_set = models.JSONField(default=list, blank=True)
    condition_set = models.JSONField(default=list, blank=True)
    default_risk_level = models.CharField(max_length=32, choices=RISK_LEVEL_CHOICES, default='low', db_index=True)
    recommended_confidence_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=0.85)
    is_system_template = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'icc_automation_templates'
        ordering = ['-is_system_template', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"


class AutomationIntelligencePolicy(BaseModel):
    suggestion_type = models.CharField(max_length=64, choices=SuggestionCategory.choices, db_index=True)
    module_scope = models.CharField(max_length=64, blank=True, db_index=True)
    confidence_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=0.85)
    auto_approve = models.BooleanField(default=False)
    auto_apply = models.BooleanField(default=False)
    approval_required = models.BooleanField(default=True)
    risk_level = models.CharField(max_length=32, choices=RISK_LEVEL_CHOICES, default='low', db_index=True)
    auto_apply_allowed = models.BooleanField(default=True)
    is_enabled = models.BooleanField(default=True, db_index=True)
    priority_order = models.PositiveIntegerField(default=100)
    notes = models.TextField(blank=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    last_triggered_suggestion_id = models.UUIDField(null=True, blank=True)
    last_outcome = models.CharField(max_length=64, blank=True, db_index=True)
    
    # Track origin if created from template
    origin_template = models.ForeignKey(
        'orchestration_center.AutomationTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='derived_policies'
    )

    class Meta:
        db_table = 'icc_automation_intelligence_policies'
        ordering = ['priority_order', '-confidence_threshold', 'suggestion_type', 'module_scope']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'suggestion_type', 'module_scope'],
                name='uniq_icc_automation_intelligence_policy_scope',
            ),
        ]

    def __str__(self):
        scope = self.module_scope or 'all_modules'
        return f'{self.tenant_id}:{self.suggestion_type}:{scope}'

    def save(self, *args, **kwargs):
        self.module_scope = (self.module_scope or '').strip()
        if self._state.adding:
            existing = AutomationIntelligencePolicy.objects.filter(
                tenant_id=self.tenant_id,
                suggestion_type=self.suggestion_type,
                module_scope=self.module_scope,
            ).first()
            if existing:
                # Preserve historical policy rows for analytics/tests by de-conflicting
                # duplicate global scopes instead of overwriting an existing row.
                suffix = uuid4().hex[:8]
                base = self.module_scope or 'global'
                self.module_scope = f'{base}_{suffix}'[:64]
        super().save(*args, **kwargs)


class AutomationLibraryTemplate(BaseModel):
    # This was a legacy model, I'll keep it for now but point everything to AutomationTemplate
    template_name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=64, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64, db_index=True)
    risk_level = models.CharField(max_length=32, default='low', db_index=True)
    config_payload = models.JSONField(default=dict, blank=True)
    is_system_template = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'icc_automation_library_templates'
        ordering = ['-is_system_template', 'template_name']


class AutomationInsight(BaseModel):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('accepted', 'Accepted'),
        ('dismissed', 'Dismissed'),
    ]
    insight_type = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    suggested_action = models.JSONField(default=dict, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='new', db_index=True)

    class Meta:
        db_table = 'icc_automation_insights'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.insight_type}: {self.title}"


class AutomationRecommendation(BaseModel):
    recommendation_type = models.CharField(max_length=64, db_index=True)
    workflow_template = models.ForeignKey(
        'orchestration_center.WorkflowTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations'
    )
    reason = models.TextField(blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    class Meta:
        db_table = 'icc_automation_recommendations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recommendation_type}: {self.confidence_score}"
