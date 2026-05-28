from django.db import models
from shared.models import BaseModel
from .workflow import AgencyWorkflowDefinition

class AgencyWorkflowEventDefinition(BaseModel):
    event_key = models.CharField(max_length=128, unique=True, db_index=True)
    event_name = models.CharField(max_length=255)
    module_scope = models.CharField(max_length=64, db_index=True) # e.g., 'talent_pool', 'submissions'
    description = models.TextField(blank=True)
    payload_schema = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'agency_workflows'
        db_table = 'agency_workflow_event_definitions'
        ordering = ['event_name']

class AgencyWorkflowEventSubscription(BaseModel):
    workflow = models.ForeignKey(AgencyWorkflowDefinition, on_delete=models.CASCADE, related_name='event_subscriptions')
    event_definition = models.ForeignKey(AgencyWorkflowEventDefinition, on_delete=models.CASCADE, related_name='subscriptions')
    trigger_filters = models.JSONField(default=dict, blank=True) # e.g., {"client_id": "..."}
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'agency_workflows'
        db_table = 'agency_workflow_event_subscriptions'

class AgencyWorkflowEventLog(BaseModel):
    STATUS_CHOICES = [
        ('emitted', 'Emitted'),
        ('consumed', 'Consumed'),
        ('failed', 'Failed'),
        ('ignored', 'Ignored'),
    ]
    event_key = models.CharField(max_length=128, db_index=True)
    entity_type = models.CharField(max_length=64, db_index=True)
    entity_id = models.UUIDField(db_index=True)
    related_candidate_id = models.UUIDField(null=True, blank=True, db_index=True)
    related_client_id = models.UUIDField(null=True, blank=True, db_index=True)
    related_job_id = models.UUIDField(null=True, blank=True, db_index=True)
    payload = models.JSONField(default=dict)
    source_module = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='emitted')

    class Meta:
        app_label = 'agency_workflows'
        db_table = 'agency_workflow_event_logs'
        ordering = ['-created_at']

class AgencyWorkflowEventDebugTrace(BaseModel):
    DECISION_CHOICES = [
        ('matched', 'Matched'),
        ('filtered_out', 'Filtered Out'),
        ('blocked', 'Blocked'),
        ('executed', 'Executed'),
        ('failed', 'Failed'),
    ]
    event_log = models.ForeignKey(AgencyWorkflowEventLog, on_delete=models.CASCADE, related_name='traces', null=True, blank=True)
    workflow = models.ForeignKey(AgencyWorkflowDefinition, on_delete=models.CASCADE, related_name='event_traces')
    decision = models.CharField(max_length=16, choices=DECISION_CHOICES)
    reason = models.TextField(blank=True)
    trace_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'agency_workflows'
        db_table = 'agency_workflow_event_debug_traces'
        ordering = ['-created_at']
