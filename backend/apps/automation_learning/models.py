from shared.models import BaseModel
from django.db import models


class AutomationLearningEvent(BaseModel):
    EVENT_TYPES = [
        ('workflow_success', 'Workflow Success'),
        ('workflow_failure', 'Workflow Failure'),
        ('manual_override', 'Manual Override'),
        ('retry_success', 'Retry Success'),
        ('retry_failure', 'Retry Failure'),
        ('fallback_used', 'Fallback Used'),
        ('slow_execution', 'Slow Execution'),
    ]
    workflow_id = models.UUIDField(db_index=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    event_data = models.JSONField(default=dict, blank=True)
    outcome = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'automation_learning_events'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.workflow_id}"


class AutomationLearningPattern(BaseModel):
    PATTERN_TYPES = [
        ('repeated_failure', 'Repeated Failure'),
        ('repeated_manual_action', 'Repeated Manual Action'),
        ('delay_pattern', 'Delay Pattern'),
        ('dependency_pattern', 'Dependency Pattern'),
        ('user_behavior_pattern', 'User Behavior Pattern'),
    ]
    pattern_type = models.CharField(max_length=50, choices=PATTERN_TYPES)
    module_scope = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    frequency = models.IntegerField(default=1)
    confidence_score = models.FloatField(default=0.0)

    class Meta:
        db_table = 'automation_learning_patterns'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pattern_type} - {self.confidence_score}"


class AutomationOptimizationSuggestion(BaseModel):
    SUGGESTION_TYPES = [
        ('optimize_workflow', 'Optimize Workflow'),
        ('add_fallback', 'Add Fallback'),
        ('adjust_priority', 'Adjust Priority'),
        ('add_retry', 'Add Retry'),
        ('create_new_workflow', 'Create New Workflow'),
        ('modify_sla', 'Modify SLA'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('applied', 'Applied'),
        ('dismissed', 'Dismissed'),
    ]
    suggestion_type = models.CharField(max_length=50, choices=SUGGESTION_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    expected_impact = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'automation_optimization_suggestions'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AutomationLearningModel(BaseModel):
    MODEL_TYPES = [
        ('failure_prediction', 'Failure Prediction'),
        ('delay_prediction', 'Delay Prediction'),
        ('optimization_prediction', 'Optimization Prediction'),
        ('automation_recommendation', 'Automation Recommendation'),
    ]
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES)
    training_data_range = models.JSONField(default=dict, blank=True)
    accuracy_score = models.FloatField(default=0.0)
    last_trained_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'automation_learning_models'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.model_type} - {self.accuracy_score}"
