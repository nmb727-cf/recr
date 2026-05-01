from django.db import models

from shared.models import BaseModel
from apps.workflow_execution.models.execution import WorkflowInstance, WorkflowStageExecution


class WorkflowScheduledTask(BaseModel):
    TASK_TYPES = [
        ('stage_transition', 'Stage Transition'),
        ('wait_resume', 'Wait Resume'),
        ('retry_stage', 'Retry Stage'),
        ('recovery_retry', 'Recovery Retry'),
        ('sla_check', 'SLA Check'),
        ('escalation_check', 'Escalation Check'),
        ('notification_dispatch', 'Notification Dispatch'),
        ('workflow_resume', 'Workflow Resume'),
        ('analytics_rollup', 'Analytics Rollup'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='scheduled_tasks',
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scheduled_tasks',
    )
    task_type = models.CharField(max_length=32, choices=TASK_TYPES, db_index=True)
    scheduled_at = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='scheduled', db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    executed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_sched_tasks'
        ordering = ['scheduled_at', 'created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['workflow_instance', 'status']),
        ]


class WorkflowSchedulerLog(BaseModel):
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    task = models.ForeignKey(
        WorkflowScheduledTask,
        on_delete=models.CASCADE,
        related_name='scheduler_logs',
    )
    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='scheduler_logs',
    )
    task_type = models.CharField(max_length=32, choices=WorkflowScheduledTask.TASK_TYPES, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, db_index=True)
    message = models.TextField(blank=True)

    class Meta:
        db_table = 'wf_exec_sched_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'status']),
            models.Index(fields=['task_type', 'status']),
        ]
