from django.db import models

from shared.models import BaseModel
from apps.workflow_execution.models.execution import WorkflowInstance, WorkflowStageExecution


class WorkflowConditionRule(BaseModel):
    CONDITION_TYPES = [
        ('workflow_context', 'Workflow Context'),
        ('entity_field', 'Entity Field'),
        ('actor_field', 'Actor Field'),
        ('score_field', 'Score Field'),
        ('status_field', 'Status Field'),
        ('time_field', 'Time Field'),
        ('custom', 'Custom'),
    ]
    OPERATORS = [
        ('equals', 'Equals'),
        ('not_equals', 'Not Equals'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('greater_or_equal', 'Greater Or Equal'),
        ('less_or_equal', 'Less Or Equal'),
        ('contains', 'Contains'),
        ('not_contains', 'Not Contains'),
        ('in_list', 'In List'),
        ('not_in_list', 'Not In List'),
        ('is_true', 'Is True'),
        ('is_false', 'Is False'),
        ('exists', 'Exists'),
        ('not_exists', 'Not Exists'),
    ]
    LOGICAL_JOINS = [
        ('AND', 'AND'),
        ('OR', 'OR'),
    ]

    workflow_id = models.UUIDField(db_index=True)
    stage_id = models.UUIDField(db_index=True)
    rule_name = models.CharField(max_length=255)
    rule_group = models.CharField(max_length=128, default='default', db_index=True)
    condition_type = models.CharField(max_length=32, choices=CONDITION_TYPES, db_index=True)
    field_name = models.CharField(max_length=255, db_index=True)
    operator = models.CharField(max_length=32, choices=OPERATORS, db_index=True)
    expected_value = models.JSONField(default=dict, blank=True)
    logical_join = models.CharField(max_length=3, choices=LOGICAL_JOINS, default='AND')
    priority = models.IntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_condition_rules'
        ordering = ['priority', 'created_at']
        indexes = [
            models.Index(fields=['workflow_id', 'stage_id', 'rule_group', 'is_active']),
            models.Index(fields=['workflow_id', 'stage_id', 'priority']),
        ]


class WorkflowConditionGroup(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    stage_id = models.UUIDField(db_index=True)
    group_name = models.CharField(max_length=128, default='default', db_index=True)
    success_transition_id = models.UUIDField(null=True, blank=True, db_index=True)
    failure_transition_id = models.UUIDField(null=True, blank=True, db_index=True)
    default_transition_id = models.UUIDField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_condition_groups'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_id', 'stage_id', 'is_active']),
            models.Index(fields=['workflow_id', 'stage_id', 'group_name', 'is_active']),
        ]


class WorkflowConditionEvaluationLog(BaseModel):
    RESULT_CHOICES = [
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='condition_evaluation_logs',
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='condition_evaluation_logs',
    )
    condition_group = models.ForeignKey(
        WorkflowConditionGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluation_logs',
    )
    rule = models.ForeignKey(
        WorkflowConditionRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluation_logs',
    )
    evaluated_value = models.JSONField(default=dict, blank=True)
    expected_value = models.JSONField(default=dict, blank=True)
    result = models.CharField(max_length=16, choices=RESULT_CHOICES, db_index=True)
    reason = models.TextField(blank=True)

    class Meta:
        db_table = 'wf_exec_condition_eval_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'result']),
            models.Index(fields=['condition_group', 'result']),
        ]
