from django.db import models
from shared.models import BaseModel

class WorkflowAnalyticsSnapshot(BaseModel):
    workflow = models.ForeignKey('orchestration_center.Workflow', on_delete=models.CASCADE, related_name='analytics_snapshots')
    snapshot_date = models.DateField(db_index=True)
    execution_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    paused_count = models.IntegerField(default=0)
    avg_execution_time_ms = models.FloatField(default=0.0)
    avg_steps_per_execution = models.FloatField(default=0.0)
    completion_rate = models.FloatField(default=0.0)
    failure_rate = models.FloatField(default=0.0)

    class Meta:
        db_table = 'icc_workflow_analytics_snapshots'
        unique_together = ('tenant_id', 'workflow', 'snapshot_date')
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"{self.workflow.name} - {self.snapshot_date}"

class WorkflowActionMetric(BaseModel):
    workflow = models.ForeignKey('orchestration_center.Workflow', on_delete=models.CASCADE, related_name='action_metrics')
    action_type = models.CharField(max_length=64, db_index=True)
    action_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    avg_action_time_ms = models.FloatField(default=0.0)

    class Meta:
        db_table = 'icc_workflow_action_metrics'
        unique_together = ('tenant_id', 'workflow', 'action_type')

class WorkflowTriggerMetric(BaseModel):
    workflow = models.ForeignKey('orchestration_center.Workflow', on_delete=models.CASCADE, related_name='trigger_metrics')
    trigger_event = models.CharField(max_length=128, db_index=True)
    trigger_count = models.IntegerField(default=0)
    execution_started_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'icc_workflow_trigger_metrics'
        unique_together = ('tenant_id', 'workflow', 'trigger_event')

class WorkflowImpactMetric(BaseModel):
    IMPACT_TYPES = [
        ('hours_saved', 'Hours Saved'),
        ('reminders_sent', 'Reminders Sent'),
        ('escalations_prevented', 'Escalations Prevented'),
        ('stage_movements_automated', 'Stage Movements Automated'),
        ('interviews_auto_scheduled', 'Interviews Auto-Scheduled'),
        ('offers_auto_triggered', 'Offers Auto-Triggered'),
    ]
    workflow = models.ForeignKey('orchestration_center.Workflow', on_delete=models.CASCADE, related_name='impact_metrics')
    impact_type = models.CharField(max_length=64, choices=IMPACT_TYPES, db_index=True)
    metric_value = models.FloatField(default=0.0)
    metric_unit = models.CharField(max_length=32, blank=True)
    calculation_context = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'icc_workflow_impact_metrics'
        unique_together = ('tenant_id', 'workflow', 'impact_type')

class WorkflowFailureInsight(BaseModel):
    FAILURE_STATUS = [
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored'),
    ]
    workflow = models.ForeignKey('orchestration_center.Workflow', on_delete=models.CASCADE, related_name='failure_insights')
    failure_type = models.CharField(max_length=128, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    suggested_fix = models.TextField(blank=True)
    occurrence_count = models.IntegerField(default=0)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=FAILURE_STATUS, default='new', db_index=True)

    class Meta:
        db_table = 'icc_workflow_failure_insights'
        ordering = ['-last_seen_at']
