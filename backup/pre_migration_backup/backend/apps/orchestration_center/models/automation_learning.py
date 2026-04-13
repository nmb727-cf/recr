from django.db import models
from shared.models import BaseModel

class AutomationLearningSignal(BaseModel):
    OUTCOME_TYPES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('dismissed', 'Dismissed'),
        ('applied', 'Applied'),
        ('overridden', 'Overridden'),
    ]

    automation_id = models.UUIDField(null=True, blank=True, db_index=True)
    suggestion_id = models.UUIDField(null=True, blank=True, db_index=True)
    policy_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    suggestion_type = models.CharField(max_length=64, blank=True, db_index=True, default='general')
    success_rate = models.FloatField(default=0.0)
    failure_rate = models.FloatField(default=0.0)
    override_rate = models.FloatField(default=0.0)
    confidence_score = models.FloatField(default=0.0)
    recommendation = models.TextField(blank=True)
    
    outcome_type = models.CharField(max_length=32, choices=OUTCOME_TYPES, db_index=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    user_action = models.CharField(max_length=64, blank=True)
    
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'icc_automation_learning_signals'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.suggestion_type} {self.outcome_type} @ {self.created_at}"
