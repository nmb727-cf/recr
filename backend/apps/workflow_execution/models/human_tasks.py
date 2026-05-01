from django.db import models

from shared.models import BaseModel
from apps.workflow_execution.models.execution import WorkflowInstance, WorkflowStageExecution


class WorkflowHumanTask(BaseModel):
    TASK_TYPES = [
        ('review', 'Review'),
        ('approval', 'Approval'),
        ('decision', 'Decision'),
        ('feedback', 'Feedback'),
        ('confirmation', 'Confirmation'),
        ('document_review', 'Document Review'),
        ('scheduling', 'Scheduling'),
        ('custom', 'Custom'),
    ]
    ASSIGNEE_TYPES = [
        ('recruiter', 'Recruiter'),
        ('hiring_manager', 'Hiring Manager'),
        ('hr', 'HR'),
        ('agency_recruiter', 'Agency Recruiter'),
        ('candidate', 'Candidate'),
        ('interviewer', 'Interviewer'),
        ('system', 'System'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='human_tasks',
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='human_tasks',
    )
    task_type = models.CharField(max_length=32, choices=TASK_TYPES, db_index=True)
    assigned_to_type = models.CharField(max_length=32, choices=ASSIGNEE_TYPES, blank=True, db_index=True)
    assigned_to_id = models.UUIDField(null=True, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'wf_exec_human_tasks'
        ordering = ['due_at', 'created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'status']),
            models.Index(fields=['assigned_to_id', 'status']),
        ]


class WorkflowApprovalRule(BaseModel):
    APPROVAL_TYPES = [
        ('single', 'Single'),
        ('multiple', 'Multiple'),
        ('sequential', 'Sequential'),
        ('parallel', 'Parallel'),
    ]

    workflow_id = models.UUIDField(db_index=True)
    stage_id = models.UUIDField(db_index=True)
    approval_type = models.CharField(max_length=16, choices=APPROVAL_TYPES, default='single', db_index=True)
    required_approvals = models.PositiveIntegerField(default=1)
    approval_role = models.CharField(max_length=64, blank=True)
    escalation_role = models.CharField(max_length=64, blank=True)
    timeout_hours = models.PositiveIntegerField(default=24)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_approval_rules'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_id', 'stage_id', 'is_active']),
        ]


class WorkflowApprovalLog(BaseModel):
    DECISION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('requested_changes', 'Requested Changes'),
    ]
    APPROVER_TYPES = [
        ('recruiter', 'Recruiter'),
        ('hiring_manager', 'Hiring Manager'),
        ('hr', 'HR'),
        ('agency_recruiter', 'Agency Recruiter'),
        ('candidate', 'Candidate'),
        ('interviewer', 'Interviewer'),
        ('system', 'System'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='approval_logs',
    )
    task = models.ForeignKey(
        WorkflowHumanTask,
        on_delete=models.CASCADE,
        related_name='approval_logs',
    )
    approver_type = models.CharField(max_length=32, choices=APPROVER_TYPES, db_index=True)
    approver_id = models.UUIDField(null=True, blank=True, db_index=True)
    decision = models.CharField(max_length=32, choices=DECISION_CHOICES, db_index=True)
    comments = models.TextField(blank=True)

    class Meta:
        db_table = 'wf_exec_approval_logs'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'decision']),
            models.Index(fields=['task', 'decision']),
        ]
