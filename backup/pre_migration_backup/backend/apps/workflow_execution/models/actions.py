from django.db import models

from shared.models import BaseModel
from apps.workflow_execution.models.execution import WorkflowInstance, WorkflowStageExecution


class WorkflowActionDefinition(BaseModel):
    ACTION_TYPES = [
        ('assign_actor', 'Assign Actor'),
        ('create_task', 'Create Task'),
        ('send_notification', 'Send Notification'),
        ('update_entity_status', 'Update Entity Status'),
        ('move_stage', 'Move Stage'),
        ('create_interview', 'Create Interview'),
        ('update_interview', 'Update Interview'),
        ('create_offer', 'Create Offer'),
        ('update_offer', 'Update Offer'),
        ('generate_document', 'Generate Document'),
        ('create_sla', 'Create SLA'),
        ('create_handoff', 'Create Handoff'),
        ('schedule_action', 'Schedule Action'),
        ('create_note', 'Create Note'),
        ('add_tag', 'Add Tag'),
        ('request_approval', 'Request Approval'),
    ]
    RUN_MODES = [
        ('immediate', 'Immediate'),
        ('deferred', 'Deferred'),
        ('async', 'Async'),
    ]

    workflow_id = models.UUIDField(db_index=True)
    stage_id = models.UUIDField(db_index=True)
    action_name = models.CharField(max_length=255)
    action_type = models.CharField(max_length=32, choices=ACTION_TYPES, db_index=True)
    action_config = models.JSONField(default=dict, blank=True)
    execution_order = models.IntegerField(default=0, db_index=True)
    run_mode = models.CharField(max_length=16, choices=RUN_MODES, default='immediate', db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_action_defs'
        ordering = ['execution_order', 'created_at']
        indexes = [
            models.Index(fields=['workflow_id', 'stage_id', 'is_active', 'execution_order']),
        ]


class WorkflowActionExecutionLog(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
        ('deferred', 'Deferred'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='action_execution_logs',
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_execution_logs',
    )
    action_definition = models.ForeignKey(
        WorkflowActionDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='execution_logs',
    )
    action_type = models.CharField(max_length=32, choices=WorkflowActionDefinition.ACTION_TYPES, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    execution_result = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_exec_action_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'status']),
            models.Index(fields=['action_type', 'status']),
        ]


class WorkflowActionDependency(BaseModel):
    DEPENDENCY_TYPES = [
        ('must_complete_first', 'Must Complete First'),
        ('run_if_success', 'Run If Success'),
        ('run_if_failed', 'Run If Failed'),
    ]

    action_definition = models.ForeignKey(
        WorkflowActionDefinition,
        on_delete=models.CASCADE,
        related_name='dependencies',
    )
    depends_on_action = models.ForeignKey(
        WorkflowActionDefinition,
        on_delete=models.CASCADE,
        related_name='dependents',
    )
    dependency_type = models.CharField(max_length=32, choices=DEPENDENCY_TYPES, default='must_complete_first', db_index=True)

    class Meta:
        db_table = 'wf_exec_action_dependencies'
        ordering = ['created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['action_definition', 'depends_on_action', 'dependency_type'],
                name='wf_exec_action_dependency_unique',
            )
        ]
