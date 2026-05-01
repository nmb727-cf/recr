from django.db import models
from shared.models import BaseModel
from apps.orchestration_center.models.workflow import Workflow

class WorkflowTriggerRegistry(BaseModel):
    event_key = models.CharField(max_length=128, unique=True, db_index=True)
    event_name = models.CharField(max_length=255)
    module_scope = models.CharField(max_length=64, db_index=True)
    entity_type = models.CharField(max_length=64)
    payload_schema = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'wf_exec_trigger_registry'
        ordering = ['module_scope', 'event_name']

class WorkflowTriggerMapping(BaseModel):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='trigger_mappings')
    trigger_registry = models.ForeignKey(WorkflowTriggerRegistry, on_delete=models.CASCADE, related_name='mappings')
    trigger_filters = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'wf_exec_trigger_mappings'

class WorkflowEventLog(BaseModel):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('matched', 'Matched'),
        ('ignored', 'Ignored'),
        ('failed', 'Failed'),
    ]
    event_key = models.CharField(max_length=128, db_index=True)
    entity_type = models.CharField(max_length=64, db_index=True)
    entity_id = models.UUIDField(db_index=True)
    payload = models.JSONField(default=dict)
    source_module = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='received')
    matched_workflow_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'wf_exec_event_logs'
        ordering = ['-created_at']

class WorkflowEventMatchTrace(BaseModel):
    DECISION_CHOICES = [
        ('matched', 'Matched'),
        ('filtered_out', 'Filtered Out'),
        ('inactive', 'Inactive'),
        ('invalid', 'Invalid'),
        ('started', 'Started'),
        ('failed', 'Failed'),
    ]
    event_log = models.ForeignKey(WorkflowEventLog, on_delete=models.CASCADE, related_name='traces')
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='event_traces')
    decision = models.CharField(max_length=16, choices=DECISION_CHOICES)
    reason = models.TextField(blank=True)

    class Meta:
        db_table = 'wf_exec_event_traces'
        ordering = ['-created_at']
