import uuid
from django.db import models
from shared.models import BaseModel

class TraceStatus(models.TextChoices):
    STARTED = 'started', 'Started'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    SKIPPED = 'skipped', 'Skipped'

class WorkflowExecutionTrace(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    execution_id = models.UUIDField(db_index=True)
    trace_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    node_id = models.UUIDField(null=True, blank=True)
    event_type = models.CharField(max_length=100)
    execution_time_ms = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=TraceStatus.choices, default=TraceStatus.STARTED)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'icc_workflow_execution_traces'
        ordering = ['-created_at']

class EventSeverity(models.TextChoices):
    INFO = 'info', 'Info'
    WARNING = 'warning', 'Warning'
    ERROR = 'error', 'Error'
    CRITICAL = 'critical', 'Critical'

class WorkflowObservabilityEvent(BaseModel):
    workflow_id = models.UUIDField(db_index=True, null=True, blank=True)
    event_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=EventSeverity.choices, default=EventSeverity.INFO)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'icc_workflow_observability_events'
        ordering = ['-created_at']

class DependencyType(models.TextChoices):
    NOTIFICATION = 'notification', 'Notification Engine'
    TASK_ENGINE = 'task_engine', 'Task Engine'
    SLA_ENGINE = 'sla_engine', 'SLA Engine'
    CROSS_MODULE = 'cross_module', 'Cross Module'
    AI_ENGINE = 'ai_engine', 'AI Engine'
    PERMISSION_ENGINE = 'permission_engine', 'Permission Engine'

class DependencyStatus(models.TextChoices):
    HEALTHY = 'healthy', 'Healthy'
    DEGRADED = 'degraded', 'Degraded'
    FAILED = 'failed', 'Failed'

class WorkflowDependencyHealth(BaseModel):
    dependency_type = models.CharField(max_length=50, choices=DependencyType.choices)
    dependency_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=DependencyStatus.choices, default=DependencyStatus.HEALTHY)
    last_checked_at = models.DateTimeField(auto_now=True)
    failure_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'icc_workflow_dependency_health'
        unique_together = ('tenant_id', 'dependency_type')

class AnomalyType(models.TextChoices):
    FAILURE_RATE = 'unusual_failure_rate', 'Unusual Failure Rate'
    LATENCY = 'unusual_latency', 'Unusual Latency'
    REPEATED_RETRIES = 'repeated_retries', 'Repeated Retries'
    LOOP = 'execution_loop', 'Execution Loop'
    STUCK = 'execution_stuck', 'Execution Stuck'

class AnomalyStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    INVESTIGATING = 'investigating', 'Investigating'
    RESOLVED = 'resolved', 'Resolved'

class WorkflowAnomaly(BaseModel):
    workflow_id = models.UUIDField(db_index=True, null=True, blank=True)
    anomaly_type = models.CharField(max_length=50, choices=AnomalyType.choices)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=EventSeverity.choices, default=EventSeverity.WARNING)
    detected_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=AnomalyStatus.choices, default=AnomalyStatus.OPEN)

    class Meta:
        db_table = 'icc_workflow_anomalies'
        ordering = ['-detected_at']
