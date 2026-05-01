from django.db import models

from shared.models import BaseModel


class WorkflowMetricSnapshot(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    snapshot_date = models.DateField(db_index=True)
    total_instances = models.PositiveIntegerField(default=0)
    completed_instances = models.PositiveIntegerField(default=0)
    failed_instances = models.PositiveIntegerField(default=0)
    in_progress_instances = models.PositiveIntegerField(default=0)
    average_completion_time_seconds = models.FloatField(default=0.0)
    average_wait_time_seconds = models.FloatField(default=0.0)
    average_stage_count = models.FloatField(default=0.0)
    average_retry_count = models.FloatField(default=0.0)

    class Meta:
        db_table = 'wf_exec_metric_snapshots'
        ordering = ['-snapshot_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['workflow_id', 'snapshot_date'],
                name='wf_exec_metric_snapshot_unique_by_day',
            )
        ]
        indexes = [
            models.Index(fields=['workflow_id', 'snapshot_date']),
        ]


class WorkflowStageMetric(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    stage_id = models.UUIDField(db_index=True)
    metric_date = models.DateField(db_index=True)
    total_entries = models.PositiveIntegerField(default=0)
    completed_entries = models.PositiveIntegerField(default=0)
    failed_entries = models.PositiveIntegerField(default=0)
    average_time_in_stage_seconds = models.FloatField(default=0.0)
    average_wait_time_seconds = models.FloatField(default=0.0)
    average_retry_count = models.FloatField(default=0.0)
    sla_breach_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'wf_exec_stage_metrics'
        ordering = ['-metric_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['workflow_id', 'stage_id', 'metric_date'],
                name='wf_exec_stage_metric_unique_by_day',
            )
        ]
        indexes = [
            models.Index(fields=['workflow_id', 'metric_date']),
            models.Index(fields=['workflow_id', 'stage_id', 'metric_date']),
        ]


class WorkflowFailureMetric(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    stage_id = models.UUIDField(null=True, blank=True, db_index=True)
    metric_date = models.DateField(db_index=True)
    failure_type = models.CharField(max_length=64, db_index=True)
    failure_count = models.PositiveIntegerField(default=0)
    recovered_count = models.PositiveIntegerField(default=0)
    permanent_failure_count = models.PositiveIntegerField(default=0)
    average_recovery_time_seconds = models.FloatField(default=0.0)

    class Meta:
        db_table = 'wf_exec_failure_metrics'
        ordering = ['-metric_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['workflow_id', 'stage_id', 'metric_date', 'failure_type'],
                name='wf_exec_failure_metric_unique_by_day',
            )
        ]
        indexes = [
            models.Index(fields=['workflow_id', 'metric_date']),
            models.Index(fields=['workflow_id', 'failure_type', 'metric_date']),
        ]


class WorkflowActionMetric(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    stage_id = models.UUIDField(null=True, blank=True, db_index=True)
    action_type = models.CharField(max_length=64, db_index=True)
    metric_date = models.DateField(db_index=True)
    execution_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    average_duration_seconds = models.FloatField(default=0.0)

    class Meta:
        db_table = 'wf_exec_action_metrics'
        ordering = ['-metric_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['workflow_id', 'stage_id', 'action_type', 'metric_date'],
                name='wf_exec_action_metric_unique_by_day',
            )
        ]
        indexes = [
            models.Index(fields=['workflow_id', 'metric_date']),
            models.Index(fields=['workflow_id', 'action_type', 'metric_date']),
        ]


class WorkflowAutomationImpactMetric(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    metric_date = models.DateField(db_index=True)
    tasks_automated_count = models.PositiveIntegerField(default=0)
    approvals_automated_count = models.PositiveIntegerField(default=0)
    notifications_sent_count = models.PositiveIntegerField(default=0)
    manual_steps_saved_count = models.PositiveIntegerField(default=0)
    estimated_time_saved_minutes = models.FloatField(default=0.0)
    estimated_cost_saved = models.FloatField(default=0.0)

    class Meta:
        db_table = 'wf_exec_automation_impact_metrics'
        ordering = ['-metric_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['workflow_id', 'metric_date'],
                name='wf_exec_automation_impact_unique_by_day',
            )
        ]
        indexes = [
            models.Index(fields=['workflow_id', 'metric_date']),
        ]
