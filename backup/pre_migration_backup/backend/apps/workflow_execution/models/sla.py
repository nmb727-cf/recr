from django.db import models
from django.utils import timezone

from shared.models import BaseModel
from apps.workflow_execution.models.execution import WorkflowInstance, WorkflowStageExecution


class WorkflowStageSLA(BaseModel):
    ESCALATION_ROLES = [
        ('hiring_manager', 'Hiring Manager'),
        ('hr', 'HR'),
        ('admin', 'Admin'),
        ('workflow_owner', 'Workflow Owner'),
    ]

    workflow_id = models.UUIDField(db_index=True)
    stage_id = models.UUIDField(db_index=True)
    sla_duration = models.DurationField()
    warning_duration = models.DurationField()
    escalation_duration = models.DurationField()
    escalation_role = models.CharField(max_length=32, choices=ESCALATION_ROLES, blank=True)
    escalation_user = models.UUIDField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_stage_sla'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_id', 'stage_id', 'is_active']),
        ]


class WorkflowSLATracker(BaseModel):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('warning', 'Warning'),
        ('breached', 'Breached'),
        ('escalated', 'Escalated'),
        ('resolved', 'Resolved'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='sla_trackers',
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.CASCADE,
        related_name='sla_trackers',
    )
    stage_sla = models.ForeignKey(
        WorkflowStageSLA,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sla_trackers',
    )
    sla_start = models.DateTimeField(default=timezone.now, db_index=True)
    warning_at = models.DateTimeField(db_index=True)
    breach_at = models.DateTimeField(db_index=True)
    escalated_at = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active', db_index=True)

    class Meta:
        db_table = 'wf_exec_sla_trackers'
        ordering = ['-sla_start']
        indexes = [
            models.Index(fields=['workflow_instance', 'status']),
            models.Index(fields=['stage_execution', 'status']),
        ]


class WorkflowSLAEvent(BaseModel):
    EVENT_TYPES = [
        ('warning', 'Warning'),
        ('breach', 'Breach'),
        ('escalation', 'Escalation'),
        ('resolved', 'Resolved'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='sla_events',
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.CASCADE,
        related_name='sla_events',
    )
    event_type = models.CharField(max_length=16, choices=EVENT_TYPES, db_index=True)

    class Meta:
        db_table = 'wf_exec_sla_events'
        ordering = ['-created_at']
