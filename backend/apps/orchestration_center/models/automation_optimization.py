from django.db import models
from shared.models import BaseModel
from apps.orchestration_center.models.automation_intelligence import AutomationIntelligencePolicy

class AutomationOptimizationRecommendation(BaseModel):
    RECOMMENDATION_TYPES = [
        ('increase_confidence_threshold', 'Increase Confidence Threshold'),
        ('decrease_confidence_threshold', 'Decrease Confidence Threshold'),
        ('enable_auto_approve', 'Enable Auto-Approve'),
        ('disable_auto_approve', 'Disable Auto-Approve'),
        ('enable_auto_apply', 'Enable Auto-Apply'),
        ('disable_auto_apply', 'Disable Auto-Apply'),
        ('change_risk_level', 'Change Risk Level'),
    ]

    policy = models.ForeignKey(
        AutomationIntelligencePolicy,
        on_delete=models.CASCADE,
        related_name='optimization_recommendations'
    )
    recommendation_type = models.CharField(max_length=64, choices=RECOMMENDATION_TYPES)
    current_value = models.JSONField(null=True, blank=True)
    recommended_value = models.JSONField(null=True, blank=True)
    reason = models.TextField()
    confidence = models.FloatField(default=0.0)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'icc_automation_optimization_recommendations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recommendation_type} for {self.policy.suggestion_type} @ {self.created_at}"
