import uuid
from django.db import models
from shared.models import BaseModel

class WorkflowEventDefinition(models.Model):
    """Registry of all available system events that can trigger workflows."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_key = models.CharField(max_length=128, unique=True, db_index=True)
    event_name = models.CharField(max_length=255)
    module_scope = models.CharField(max_length=64, db_index=True) # e.g., 'candidates', 'jobs'
    description = models.TextField(blank=True)
    payload_schema = models.JSONField(default=dict, blank=True) # Expected keys/types
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'icc_workflow_event_definitions'
        verbose_name = 'Workflow Event Definition'
        ordering = ['module_scope', 'event_name']

    def __str__(self):
        return f"{self.event_name} ({self.event_key})"

class WorkflowEventSubscription(BaseModel):
    """Links a specific workflow to a system event with optional filters."""
    workflow = models.ForeignKey('orchestration_center.Workflow', on_delete=models.CASCADE, related_name='event_subscriptions')
    event_definition = models.ForeignKey(WorkflowEventDefinition, on_delete=models.CASCADE, related_name='subscriptions')
    trigger_filters = models.JSONField(default=dict, blank=True) # e.g., {"stage": "shortlisted"}
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'icc_workflow_event_subscriptions'
        unique_together = ('workflow', 'event_definition', 'tenant_id')

class WorkflowEventLog(models.Model):
    """History of all emitted system events."""
    STATUS_CHOICES = [
        ('emitted', 'Emitted'),
        ('consumed', 'Consumed'),
        ('failed', 'Failed'),
        ('ignored', 'Ignored'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    event_key = models.CharField(max_length=128, db_index=True)
    entity_type = models.CharField(max_length=64, db_index=True) # e.g., 'candidate'
    entity_id = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict)
    source_module = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='emitted')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'icc_workflow_event_logs'
        ordering = ['-created_at']

class WorkflowEventDebugTrace(models.Model):
    """Detailed trace of why a workflow was or was not triggered by an event."""
    DECISION_CHOICES = [
        ('matched', 'Matched'),
        ('filtered_out', 'Filtered Out'),
        ('blocked', 'Blocked'),
        ('executed', 'Executed'),
        ('failed', 'Failed'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    event_log = models.ForeignKey(WorkflowEventLog, on_delete=models.CASCADE, related_name='debug_traces')
    workflow = models.ForeignKey('orchestration_center.Workflow', on_delete=models.CASCADE)
    decision = models.CharField(max_length=32, choices=DECISION_CHOICES)
    reason = models.TextField(blank=True)
    trace_payload = models.JSONField(default=dict, blank=True) # Captured state during evaluation
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'icc_workflow_event_debug_traces'
        ordering = ['-created_at']
