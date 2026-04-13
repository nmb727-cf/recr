from django.db import models
from shared.models import BaseModel

class AutomationAIDecision(BaseModel):
    DECISION_TYPES = [
        ('execute_workflow', 'Execute Workflow'),
        ('delay_execution', 'Delay Execution'),
        ('escalate', 'Escalate'),
        ('retry', 'Retry'),
        ('fallback', 'Fallback'),
        ('create_automation', 'Create Automation'),
        ('pause_automation', 'Pause Automation'),
    ]
    decision_type = models.CharField(max_length=50, choices=DECISION_TYPES)
    decision_reason = models.TextField()
    decision_confidence = models.FloatField(default=0.0)
    decision_output = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'automation_ai_decisions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.decision_type} - {self.decision_confidence}"

class AutomationAIContext(BaseModel):
    CONTEXT_SOURCES = [
        ('candidate_state', 'Candidate State'),
        ('job_state', 'Job State'),
        ('pipeline_stage', 'Pipeline Stage'),
        ('sla_risk', 'SLA Risk'),
        ('workload', 'Workload'),
        ('team_availability', 'Team Availability'),
    ]
    entity_type = models.CharField(max_length=50, choices=CONTEXT_SOURCES)
    entity_id = models.UUIDField()
    context_data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'automation_ai_contexts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.entity_type} - {self.entity_id}"

class AutomationAIReasoning(BaseModel):
    REASONING_TYPES = [
        ('predictive', 'Predictive'),
        ('contextual', 'Contextual'),
        ('behavioral', 'Behavioral'),
        ('optimization', 'Optimization'),
    ]
    reasoning_type = models.CharField(max_length=50, choices=REASONING_TYPES)
    reasoning_data = models.JSONField(default=dict, blank=True)
    confidence_score = models.FloatField(default=0.0)

    class Meta:
        db_table = 'automation_ai_reasoning'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reasoning_type} - {self.confidence_score}"

class AutomationAIRecommendation(BaseModel):
    RECOMMENDATION_TYPES = [
        ('create_workflow', 'Create Workflow'),
        ('optimize_workflow', 'Optimize Workflow'),
        ('remove_workflow', 'Remove Workflow'),
        ('change_priority', 'Change Priority'),
        ('adjust_sla', 'Adjust SLA'),
    ]
    recommendation_type = models.CharField(max_length=50, choices=RECOMMENDATION_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    expected_impact = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.0)

    class Meta:
        db_table = 'automation_ai_recommendations'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
