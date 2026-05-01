from django.db import models

from shared.models import BaseModel
from apps.workflow_execution.models.execution import WorkflowInstance, WorkflowStageExecution


class WorkflowNotificationRule(BaseModel):
    TRIGGER_TYPES = [
        ('stage_started', 'Stage Started'),
        ('stage_completed', 'Stage Completed'),
        ('wait_started', 'Wait Started'),
        ('wait_resumed', 'Wait Resumed'),
        ('sla_warning', 'SLA Warning'),
        ('sla_breach', 'SLA Breach'),
        ('escalation', 'Escalation'),
        ('workflow_failed', 'Workflow Failed'),
        ('workflow_completed', 'Workflow Completed'),
    ]
    RECIPIENT_TYPES = [
        ('workflow_owner', 'Workflow Owner'),
        ('assigned_actor', 'Assigned Actor'),
        ('recruiter', 'Recruiter'),
        ('hiring_manager', 'Hiring Manager'),
        ('hr', 'HR'),
        ('candidate', 'Candidate'),
        ('agency_recruiter', 'Agency Recruiter'),
        ('admin', 'Admin'),
    ]
    CHANNEL_TYPES = [
        ('in_app', 'In App'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
    ]

    workflow_id = models.UUIDField(db_index=True)
    stage_id = models.UUIDField(null=True, blank=True, db_index=True)
    trigger_type = models.CharField(max_length=32, choices=TRIGGER_TYPES, db_index=True)
    recipient_type = models.CharField(max_length=32, choices=RECIPIENT_TYPES, db_index=True)
    channel = models.CharField(max_length=16, choices=CHANNEL_TYPES, db_index=True)
    template_key = models.CharField(max_length=128, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_wfnotif_rules'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_id', 'trigger_type', 'is_active']),
            models.Index(fields=['workflow_id', 'stage_id', 'trigger_type', 'is_active']),
        ]


class WorkflowNotificationLog(BaseModel):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    CHANNEL_TYPES = WorkflowNotificationRule.CHANNEL_TYPES
    RECIPIENT_TYPES = WorkflowNotificationRule.RECIPIENT_TYPES

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='notification_logs',
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_logs',
    )
    recipient_type = models.CharField(max_length=32, choices=RECIPIENT_TYPES, db_index=True)
    recipient_id = models.UUIDField(null=True, blank=True, db_index=True)
    channel = models.CharField(max_length=16, choices=CHANNEL_TYPES, db_index=True)
    template_key = models.CharField(max_length=128, db_index=True)
    message_preview = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='queued', db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_wfnotif_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'status']),
            models.Index(fields=['channel', 'status']),
        ]


class WorkflowNotificationQueue(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    CHANNEL_TYPES = WorkflowNotificationRule.CHANNEL_TYPES
    RECIPIENT_TYPES = WorkflowNotificationRule.RECIPIENT_TYPES

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='notification_queue_items',
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_queue_items',
    )
    recipient_type = models.CharField(max_length=32, choices=RECIPIENT_TYPES, db_index=True)
    recipient_id = models.UUIDField(null=True, blank=True, db_index=True)
    channel = models.CharField(max_length=16, choices=CHANNEL_TYPES, db_index=True)
    template_key = models.CharField(max_length=128, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', db_index=True)
    scheduled_at = models.DateTimeField(db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_wfnotif_queue'
        ordering = ['scheduled_at', 'created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['workflow_instance', 'status']),
        ]
