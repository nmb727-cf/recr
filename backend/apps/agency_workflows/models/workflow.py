from django.db import models
from shared.models import BaseModel

class AgencyWorkflowDefinition(BaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
    ]
    SCOPE_CHOICES = [
        ('talent_pool', 'Talent Pool'),
        ('client_job', 'Client Job'),
        ('submission', 'Submission'),
        ('recruiter', 'Recruiter'),
        ('placement', 'Placement'),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    scope = models.CharField(max_length=32, choices=SCOPE_CHOICES)
    version = models.IntegerField(default=1)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='draft')
    trigger_event = models.CharField(max_length=128, blank=True)
    
    class Meta:
        app_label = 'agency_workflows'
        db_table = 'agency_workflow_definitions'
        ordering = ['-created_at']

class AgencyWorkflowNode(BaseModel):
    workflow = models.ForeignKey(AgencyWorkflowDefinition, on_delete=models.CASCADE, related_name='nodes')
    node_type = models.CharField(max_length=64)
    config = models.JSONField(default=dict)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)

    class Meta:
        app_label = 'agency_workflows'
        db_table = 'agency_workflow_nodes'

class AgencyWorkflowEdge(BaseModel):
    workflow = models.ForeignKey(AgencyWorkflowDefinition, on_delete=models.CASCADE, related_name='edges')
    source_node = models.ForeignKey(AgencyWorkflowNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    target_node = models.ForeignKey(AgencyWorkflowNode, on_delete=models.CASCADE, related_name='incoming_edges')
    condition = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'agency_workflows'
        db_table = 'agency_workflow_edges'
