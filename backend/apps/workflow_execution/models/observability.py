from django.db import models

from shared.models import BaseModel
from apps.workflow_execution.models.execution import WorkflowInstance, WorkflowStageExecution


class WorkflowExecutionTimelineEntry(BaseModel):
    ENTRY_TYPES = [
        ('workflow_started', 'Workflow Started'),
        ('stage_started', 'Stage Started'),
        ('stage_completed', 'Stage Completed'),
        ('transition_taken', 'Transition Taken'),
        ('decision_evaluated', 'Decision Evaluated'),
        ('action_executed', 'Action Executed'),
        ('wait_started', 'Wait Started'),
        ('wait_resumed', 'Wait Resumed'),
        ('human_task_created', 'Human Task Created'),
        ('human_task_completed', 'Human Task Completed'),
        ('approval_requested', 'Approval Requested'),
        ('approval_completed', 'Approval Completed'),
        ('sla_started', 'SLA Started'),
        ('sla_warning', 'SLA Warning'),
        ('sla_breached', 'SLA Breached'),
        ('routing_started', 'Routing Started'),
        ('routing_completed', 'Routing Completed'),
        ('notification_sent', 'Notification Sent'),
        ('failure_logged', 'Failure Logged'),
        ('retry_started', 'Retry Started'),
        ('workflow_completed', 'Workflow Completed'),
        ('workflow_failed', 'Workflow Failed'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='observability_timeline_entries',
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='observability_timeline_entries',
    )
    entry_type = models.CharField(max_length=32, choices=ENTRY_TYPES, db_index=True)
    entry_label = models.CharField(max_length=255)
    entry_description = models.TextField(blank=True)
    actor_type = models.CharField(max_length=64, blank=True)
    actor_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_obs_timeline_entries'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'entry_type', 'created_at']),
            models.Index(fields=['workflow_instance', 'created_at']),
        ]


class WorkflowExecutionTrace(BaseModel):
    TRACE_TYPES = [
        ('transition', 'Transition'),
        ('action', 'Action'),
        ('condition', 'Condition'),
        ('routing', 'Routing'),
        ('sla', 'SLA'),
        ('notification', 'Notification'),
        ('scheduler', 'Scheduler'),
        ('approval', 'Approval'),
        ('human_task', 'Human Task'),
        ('failure', 'Failure'),
    ]
    SEVERITIES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='execution_traces',
    )
    trace_key = models.CharField(max_length=128, db_index=True)
    trace_type = models.CharField(max_length=32, choices=TRACE_TYPES, db_index=True)
    source_module = models.CharField(max_length=128, db_index=True)
    source_id = models.CharField(max_length=128, blank=True)
    trace_message = models.TextField()
    severity = models.CharField(max_length=16, choices=SEVERITIES, default='info', db_index=True)

    class Meta:
        db_table = 'wf_exec_obs_traces'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'trace_type', 'created_at']),
            models.Index(fields=['workflow_instance', 'severity', 'created_at']),
        ]


class WorkflowObservabilitySnapshot(BaseModel):
    workflow_instance = models.OneToOneField(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='observability_snapshot',
    )
    current_stage_id = models.UUIDField(null=True, blank=True, db_index=True)
    current_status = models.CharField(max_length=32, db_index=True)
    wait_reason = models.CharField(max_length=255, blank=True)
    active_actor_type = models.CharField(max_length=64, blank=True)
    active_actor_id = models.UUIDField(null=True, blank=True, db_index=True)
    pending_task_count = models.IntegerField(default=0)
    pending_notification_count = models.IntegerField(default=0)
    has_failure = models.BooleanField(default=False, db_index=True)
    has_sla_risk = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'wf_exec_obs_snapshots'
        ordering = ['-updated_at']


class WorkflowExecutionMetric(BaseModel):
    METRIC_TYPES = [
        ('duration', 'Duration'),
        ('wait_time', 'Wait Time'),
        ('retry_count', 'Retry Count'),
        ('action_count', 'Action Count'),
        ('failure_count', 'Failure Count'),
        ('stage_count', 'Stage Count'),
        ('handoff_count', 'Handoff Count'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='execution_metrics',
    )
    metric_name = models.CharField(max_length=128, db_index=True)
    metric_value = models.FloatField(default=0.0)
    metric_type = models.CharField(max_length=32, choices=METRIC_TYPES, db_index=True)
    recorded_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = 'wf_exec_obs_metrics'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'metric_name', 'recorded_at']),
            models.Index(fields=['workflow_instance', 'metric_type', 'recorded_at']),
        ]
