from django.db import models

from shared.models import BaseModel
from apps.workflow_execution.models.execution import WorkflowInstance, WorkflowStageExecution
from apps.workflow_execution.models.actions import WorkflowActionExecutionLog


class WorkflowRecoveryCase(BaseModel):
    RECOVERY_TYPES = [
        ('stage_failure', 'Stage Failure'),
        ('action_failure', 'Action Failure'),
        ('transition_failure', 'Transition Failure'),
        ('routing_failure', 'Routing Failure'),
        ('notification_failure', 'Notification Failure'),
        ('sla_failure', 'SLA Failure'),
        ('scheduler_failure', 'Scheduler Failure'),
        ('human_task_failure', 'Human Task Failure'),
    ]
    FAILURE_TYPES = [
        ('transient', 'Transient'),
        ('external_dependency', 'External Dependency'),
        ('validation', 'Validation'),
        ('permission', 'Permission'),
        ('data_integrity', 'Data Integrity'),
        ('timeout', 'Timeout'),
        ('logic_error', 'Logic Error'),
        ('unknown', 'Unknown'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('retry_scheduled', 'Retry Scheduled'),
        ('retrying', 'Retrying'),
        ('recovered', 'Recovered'),
        ('escalated', 'Escalated'),
        ('manual_intervention_required', 'Manual Intervention Required'),
        ('failed_permanently', 'Failed Permanently'),
        ('closed', 'Closed'),
    ]
    RETRY_STRATEGIES = [
        ('immediate', 'Immediate'),
        ('delayed', 'Delayed'),
        ('exponential_backoff', 'Exponential Backoff'),
        ('manual_only', 'Manual Only'),
        ('no_retry', 'No Retry'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='recovery_cases',
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recovery_cases',
    )
    action_execution_log = models.ForeignKey(
        WorkflowActionExecutionLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recovery_cases',
    )
    recovery_type = models.CharField(max_length=32, choices=RECOVERY_TYPES, db_index=True)
    failure_type = models.CharField(max_length=32, choices=FAILURE_TYPES, default='unknown', db_index=True)
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='open', db_index=True)
    retry_strategy = models.CharField(max_length=32, choices=RETRY_STRATEGIES, default='manual_only', db_index=True)
    retry_limit = models.PositiveIntegerField(default=0)
    retry_count = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_recovery_cases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'status']),
            models.Index(fields=['recovery_type', 'status']),
            models.Index(fields=['next_retry_at', 'status']),
        ]


class WorkflowRetryAttempt(BaseModel):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    recovery_case = models.ForeignKey(
        WorkflowRecoveryCase,
        on_delete=models.CASCADE,
        related_name='retry_attempts',
    )
    attempt_number = models.PositiveIntegerField()
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='running', db_index=True)
    error_message = models.TextField(blank=True)
    result_summary = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_exec_recovery_attempts'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['recovery_case', 'attempt_number']),
            models.Index(fields=['status', 'started_at']),
        ]


class WorkflowRecoveryActionLog(BaseModel):
    ACTION_TYPES = [
        ('retry_started', 'Retry Started'),
        ('retry_succeeded', 'Retry Succeeded'),
        ('retry_failed', 'Retry Failed'),
        ('escalated', 'Escalated'),
        ('manual_resume', 'Manual Resume'),
        ('manual_skip', 'Manual Skip'),
        ('manual_fail', 'Manual Fail'),
        ('workflow_recovered', 'Workflow Recovered'),
        ('permanent_failure', 'Permanent Failure'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='recovery_action_logs',
    )
    recovery_case = models.ForeignKey(
        WorkflowRecoveryCase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_logs',
    )
    action_type = models.CharField(max_length=32, choices=ACTION_TYPES, db_index=True)
    action_taken_by = models.CharField(max_length=128, blank=True)
    action_summary = models.TextField(blank=True)

    class Meta:
        db_table = 'wf_exec_recovery_action_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'action_type']),
        ]


class WorkflowRecoveryPolicy(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    stage_id = models.UUIDField(null=True, blank=True, db_index=True)
    action_type = models.CharField(max_length=64, blank=True, db_index=True)
    failure_type = models.CharField(
        max_length=32,
        choices=WorkflowRecoveryCase.FAILURE_TYPES,
        default='unknown',
        db_index=True,
    )
    retry_strategy = models.CharField(
        max_length=32,
        choices=WorkflowRecoveryCase.RETRY_STRATEGIES,
        default='manual_only',
        db_index=True,
    )
    retry_limit = models.PositiveIntegerField(default=0)
    retry_delay_seconds = models.PositiveIntegerField(default=0)
    escalate_after_failures = models.PositiveIntegerField(default=0)
    requires_manual_review = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_recovery_policies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_id', 'stage_id', 'failure_type', 'is_active']),
        ]
