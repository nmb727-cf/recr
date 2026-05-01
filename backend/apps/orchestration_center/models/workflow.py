import uuid
from django.db import models
from django.utils import timezone
from shared.models import BaseModel

class Workflow(BaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('archived', 'Archived'),
    ]
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    trigger_event = models.CharField(max_length=128, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='draft', db_index=True)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    current_version = models.IntegerField(default=1)
    
    # Safety & Governance
    is_critical = models.BooleanField(default=False)
    require_approval = models.BooleanField(default=False)
    dry_run_mode = models.BooleanField(default=False)

    class Meta:
        db_table = 'icc_workflows'
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.name} [{self.trigger_event}]"

class WorkflowVersion(BaseModel):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    config_snapshot = models.JSONField() # Stores full nodes/edges state
    change_summary = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        db_table = 'icc_workflow_versions'
        unique_together = ('workflow', 'version_number')
        ordering = ['-version_number']

class WorkflowNode(models.Model):
    NODE_TYPES = [
        ('start', 'Start'),
        ('condition', 'Condition'),
        ('action', 'Action'),
        ('delay', 'Delay'),
        ('approval', 'Approval'),
        ('human_task', 'Human Task'),
        ('scheduling', 'Scheduling'),
        ('document', 'Document'),
        ('integration', 'Integration'),
        ('end', 'End'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='nodes')
    node_type = models.CharField(max_length=32, choices=NODE_TYPES)
    config = models.JSONField(default=dict, blank=True)
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'icc_workflow_nodes'

class WorkflowEdge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='edges')
    source_node = models.ForeignKey(WorkflowNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    target_node = models.ForeignKey(WorkflowNode, on_delete=models.CASCADE, related_name='incoming_edges')
    condition = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        db_table = 'icc_workflow_edges'

class WorkflowExecution(models.Model):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('paused', 'Paused'),
        ('rolled_back', 'Rolled Back'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    version = models.ForeignKey(WorkflowVersion, on_delete=models.SET_NULL, null=True, blank=True)
    entity_type = models.CharField(max_length=64, db_index=True)
    entity_id = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='running', db_index=True)
    is_dry_run = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    context_data = models.JSONField(default=dict, blank=True)
    execution_trace = models.JSONField(default=list, blank=True) # Detailed log of what happened

    class Meta:
        db_table = 'icc_workflow_executions'
        ordering = ['-started_at']

class WorkflowExecutionLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name='logs')
    node = models.ForeignKey(WorkflowNode, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=32)
    message = models.TextField(blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)
    state_before = models.JSONField(null=True, blank=True) # For rollback
    state_after = models.JSONField(null=True, blank=True) # For rollback

    class Meta:
        db_table = 'icc_workflow_execution_logs'
        ordering = ['executed_at']

class WorkflowTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=128, db_index=True)
    trigger_event = models.CharField(max_length=128, db_index=True)
    template_json = models.JSONField(default=dict) # Stores nodes and edges
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'icc_workflow_templates'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} [{self.category}]"
