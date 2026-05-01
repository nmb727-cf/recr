import uuid
from django.db import models
from shared.models import BaseModel

class ImpactLevel(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'

class WorkflowChangeSet(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    from_version = models.IntegerField(null=True, blank=True)
    to_version = models.IntegerField(null=True, blank=True)
    change_summary = models.JSONField(default=dict, blank=True)
    risk_score = models.IntegerField(default=0)
    impact_level = models.CharField(max_length=20, choices=ImpactLevel.choices, default=ImpactLevel.LOW)

    class Meta:
        db_table = 'icc_workflow_change_sets'
        ordering = ['-created_at']

class WorkflowImpactAnalysis(BaseModel):
    change_set = models.OneToOneField(WorkflowChangeSet, on_delete=models.CASCADE, related_name='impact_analysis')
    affected_module = models.JSONField(default=list, blank=True)
    affected_workflows = models.JSONField(default=list, blank=True)
    affected_slas = models.JSONField(default=list, blank=True)
    affected_notifications = models.JSONField(default=list, blank=True)
    affected_tasks = models.JSONField(default=list, blank=True)
    affected_users_count = models.IntegerField(default=0)
    risk_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'icc_workflow_impact_analyses'
        ordering = ['-created_at']

class DependencyType(models.TextChoices):
    TRIGGER = 'trigger_dependency', 'Trigger Dependency'
    ACTION = 'action_dependency', 'Action Dependency'
    SLA = 'sla_dependency', 'SLA Dependency'
    TASK = 'task_dependency', 'Task Dependency'
    NOTIFICATION = 'notification_dependency', 'Notification Dependency'
    CROSS_MODULE = 'cross_module_dependency', 'Cross Module Dependency'

class WorkflowDependencyMap(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    dependent_workflow_id = models.UUIDField(db_index=True, null=True, blank=True)
    dependency_type = models.CharField(max_length=50, choices=DependencyType.choices)

    class Meta:
        db_table = 'icc_workflow_dependency_maps'
        ordering = ['-created_at']

class DeploymentStrategy(models.TextChoices):
    IMMEDIATE = 'immediate', 'Immediate'
    STAGED = 'staged', 'Staged'
    CANARY = 'canary', 'Canary'
    MANUAL_APPROVAL = 'manual_approval', 'Manual Approval'

class WorkflowDeploymentPlan(BaseModel):
    change_set = models.OneToOneField(WorkflowChangeSet, on_delete=models.CASCADE, related_name='deployment_plan')
    deployment_strategy = models.CharField(max_length=30, choices=DeploymentStrategy.choices, default=DeploymentStrategy.IMMEDIATE)
    rollout_percentage = models.IntegerField(default=100)
    rollout_steps = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=30, default='pending') # pending, in_progress, completed, failed

    class Meta:
        db_table = 'icc_workflow_deployment_plans'
        ordering = ['-created_at']

class WorkflowRollbackPreview(BaseModel):
    change_set = models.OneToOneField(WorkflowChangeSet, on_delete=models.CASCADE, related_name='rollback_preview')
    rollback_possible = models.BooleanField(default=True)
    rollback_impact = models.TextField(blank=True)

    class Meta:
        db_table = 'icc_workflow_rollback_previews'
        ordering = ['-created_at']
