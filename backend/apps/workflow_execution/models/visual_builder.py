from django.db import models

from shared.models import BaseModel


class WorkflowBuilderNode(BaseModel):
    NODE_TYPES = [
        ('start', 'Start'),
        ('stage', 'Stage'),
        ('decision', 'Decision'),
        ('action', 'Action'),
        ('human_task', 'Human Task'),
        ('approval', 'Approval'),
        ('delay', 'Delay'),
        ('end', 'End'),
    ]

    workflow_id = models.UUIDField(db_index=True)
    node_type = models.CharField(max_length=32, choices=NODE_TYPES, db_index=True)
    node_name = models.CharField(max_length=255)
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_builder_nodes'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['workflow_id', 'is_active']),
            models.Index(fields=['workflow_id', 'node_type', 'is_active']),
        ]


class WorkflowBuilderConnection(BaseModel):
    CONNECTION_TYPES = [
        ('default', 'Default'),
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('conditional', 'Conditional'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
    ]

    workflow_id = models.UUIDField(db_index=True)
    source_node_id = models.UUIDField(db_index=True)
    target_node_id = models.UUIDField(db_index=True)
    condition_label = models.CharField(max_length=255, blank=True)
    connection_type = models.CharField(max_length=32, choices=CONNECTION_TYPES, default='default', db_index=True)

    class Meta:
        db_table = 'wf_exec_builder_connections'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['workflow_id', 'source_node_id']),
            models.Index(fields=['workflow_id', 'target_node_id']),
            models.Index(fields=['workflow_id', 'connection_type']),
        ]


class WorkflowBuilderLayout(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    canvas_config = models.JSONField(default=dict, blank=True)
    zoom_level = models.FloatField(default=1.0)
    viewport = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_exec_builder_layouts'
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['workflow_id'], name='wf_exec_builder_layout_unique'),
        ]
