import uuid
from django.db import models
from shared.models import BaseModel

# ─── Choices ──────────────────────────────────────────────────────────────────

class RuntimeStatus(models.TextChoices):
    HEALTHY        = 'healthy',        'Healthy'
    DEGRADED       = 'degraded',       'Degraded'
    PAUSED         = 'paused',         'Paused'
    EMERGENCY_MODE = 'emergency_mode', 'Emergency Mode'
    FAILED         = 'failed',         'Failed'

class OrchestrationMode(models.TextChoices):
    NORMAL             = 'normal',             'Normal'
    SAFE_MODE          = 'safe_mode',          'Safe Mode'
    LIMITED_MODE       = 'limited_mode',       'Limited Mode'
    MAINTENANCE_MODE   = 'maintenance_mode',   'Maintenance Mode'
    EMERGENCY_OVERRIDE = 'emergency_override', 'Emergency Override'

class EngineType(models.TextChoices):
    WORKFLOW      = 'workflow',      'Workflow'
    NOTIFICATION  = 'notification',  'Notification'
    TASK          = 'task',          'Task'
    SLA           = 'sla',           'SLA'
    ANALYTICS     = 'analytics',     'Analytics'
    GOVERNANCE    = 'governance',    'Governance'
    OBSERVABILITY = 'observability', 'Observability'
    RECOVERY      = 'recovery',      'Recovery'
    PLAYBOOK      = 'playbook',      'Playbook'
    PERMISSION    = 'permission',    'Permission'
    SANDBOX       = 'sandbox',       'Sandbox'
    CHANGE_IMPACT = 'change_impact', 'Change Impact'

class EngineStatus(models.TextChoices):
    ACTIVE      = 'active',      'Active'
    PAUSED      = 'paused',      'Paused'
    DEGRADED    = 'degraded',    'Degraded'
    FAILED      = 'failed',      'Failed'
    MAINTENANCE = 'maintenance', 'Maintenance'

class QueueStrategy(models.TextChoices):
    FIFO                = 'fifo',                'FIFO'
    PRIORITY_FIRST      = 'priority_first',      'Priority First'
    MODULE_WEIGHTED     = 'module_weighted',     'Module Weighted'
    SLA_FIRST           = 'sla_first',           'SLA First'
    CRITICAL_PATH_FIRST = 'critical_path_first', 'Critical Path First'

class OverflowStrategy(models.TextChoices):
    QUEUE              = 'queue',              'Queue'
    REROUTE            = 'reroute',            'Reroute'
    DEFER              = 'defer',              'Defer'
    REJECT_NONCRITICAL = 'reject_noncritical', 'Reject Non-Critical'
    EMERGENCY_PAUSE    = 'emergency_pause',    'Emergency Pause'

class BucketStatus(models.TextChoices):
    NORMAL    = 'normal',    'Normal'
    HIGH_LOAD = 'high_load', 'High Load'
    SATURATED = 'saturated', 'Saturated'
    THROTTLED = 'throttled', 'Throttled'

class EventSeverity(models.TextChoices):
    INFO     = 'info',     'Info'
    WARNING  = 'warning',  'Warning'
    ERROR    = 'error',    'Error'
    CRITICAL = 'critical', 'Critical'

class InsightImpactLevel(models.TextChoices):
    LOW      = 'low',      'Low'
    MEDIUM   = 'medium',   'Medium'
    HIGH     = 'high',     'High'
    CRITICAL = 'critical', 'Critical'

class InsightStatus(models.TextChoices):
    NEW         = 'new',         'New'
    ACKNOWLEDGED = 'acknowledged', 'Acknowledged'
    ACTED_ON    = 'acted_on',    'Acted On'
    IGNORED     = 'ignored',      'Ignored'

# ─── Model 1: AutomationRuntimeState ──────────────────────────────────────────

class AutomationRuntimeState(BaseModel):
    runtime_status         = models.CharField(max_length=30, choices=RuntimeStatus.choices, default=RuntimeStatus.HEALTHY)
    orchestration_mode     = models.CharField(max_length=30, choices=OrchestrationMode.choices, default=OrchestrationMode.NORMAL)
    active_workflow_count  = models.IntegerField(default=0)
    active_execution_count = models.IntegerField(default=0)
    degraded_engine_count  = models.IntegerField(default=0)
    paused_engine_count    = models.IntegerField(default=0)
    failed_engine_count    = models.IntegerField(default=0)
    last_runtime_check_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'icc_automation_runtime_states'
        verbose_name = 'Automation Runtime State'

# ─── Model 2: AutomationEngineRegistry ────────────────────────────────────────

class AutomationEngineRegistry(BaseModel):
    engine_key        = models.CharField(max_length=100, db_index=True)
    engine_name       = models.CharField(max_length=255)
    engine_type       = models.CharField(max_length=30, choices=EngineType.choices)
    status            = models.CharField(max_length=30, choices=EngineStatus.choices, default=EngineStatus.ACTIVE)
    priority          = models.IntegerField(default=100) # Lower is higher priority
    supports_recovery = models.BooleanField(default=True)
    supports_pause    = models.BooleanField(default=True)
    supports_dry_run  = models.BooleanField(default=True)
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    metadata          = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'icc_automation_engine_registries'
        unique_together = ('tenant_id', 'engine_key')
        verbose_name = 'Automation Engine Registry'

# ─── Model 3: AutomationExecutionPolicy ───────────────────────────────────────

class AutomationExecutionPolicy(BaseModel):
    name               = models.CharField(max_length=255)
    description        = models.TextField(blank=True)
    module_scope       = models.CharField(max_length=100, blank=True) # e.g. "candidates,jobs"
    trigger_priority   = models.IntegerField(default=100)
    concurrency_limit  = models.IntegerField(default=10)
    queue_strategy     = models.CharField(max_length=30, choices=QueueStrategy.choices, default=QueueStrategy.FIFO)
    retry_policy       = models.JSONField(default=dict, blank=True)
    fallback_policy    = models.JSONField(default=dict, blank=True)
    escalation_policy  = models.JSONField(default=dict, blank=True)
    is_active          = models.BooleanField(default=True, db_index=True)
    created_by         = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'icc_automation_execution_policies'
        verbose_name = 'Automation Execution Policy'

# ─── Model 4: AutomationWorkloadBucket ────────────────────────────────────────

class AutomationWorkloadBucket(BaseModel):
    bucket_name       = models.CharField(max_length=255)
    module_scope      = models.CharField(max_length=100)
    current_load      = models.IntegerField(default=0)
    max_capacity      = models.IntegerField(default=1000)
    overflow_strategy = models.CharField(max_length=30, choices=OverflowStrategy.choices, default=OverflowStrategy.QUEUE)
    status            = models.CharField(max_length=30, choices=BucketStatus.choices, default=BucketStatus.NORMAL)

    class Meta:
        db_table = 'icc_automation_workload_buckets'
        verbose_name = 'Automation Workload Bucket'

# ─── Model 5: AutomationBusinessCoverage ──────────────────────────────────────

class AutomationBusinessCoverage(BaseModel):
    module_scope                = models.CharField(max_length=100)
    process_name                = models.CharField(max_length=255)
    automation_coverage_percent = models.FloatField(default=0.0)
    manual_gap_percent          = models.FloatField(default=100.0)
    active_playbook_count       = models.IntegerField(default=0)
    active_workflow_count       = models.IntegerField(default=0)
    last_calculated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'icc_automation_business_coverages'
        verbose_name = 'Automation Business Coverage'

# ─── Model 6: AutomationOperatingEvent ────────────────────────────────────────

class AutomationOperatingEvent(BaseModel):
    event_type    = models.CharField(max_length=100, db_index=True)
    severity      = models.CharField(max_length=20, choices=EventSeverity.choices, default=EventSeverity.INFO)
    source_engine = models.CharField(max_length=100)
    message       = models.TextField()
    event_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'icc_automation_operating_events'
        ordering = ['-created_at']
        verbose_name = 'Automation Operating Event'

# ─── Model 7: AutomationOperatingInsight ──────────────────────────────────────

class AutomationOperatingInsight(BaseModel):
    insight_type   = models.CharField(max_length=100, db_index=True)
    title          = models.CharField(max_length=255)
    description    = models.TextField()
    recommendation = models.TextField(blank=True)
    impact_level   = models.CharField(max_length=20, choices=InsightImpactLevel.choices, default=InsightImpactLevel.MEDIUM)
    status         = models.CharField(max_length=20, choices=InsightStatus.choices, default=InsightStatus.NEW)

    class Meta:
        db_table = 'icc_automation_operating_insights'
        ordering = ['-created_at']
        verbose_name = 'Automation Operating Insight'
