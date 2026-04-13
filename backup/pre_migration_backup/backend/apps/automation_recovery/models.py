from django.db import models
from shared.models import BaseModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RecoveryStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    RETRYING = 'retrying', 'Retrying'
    RESUMED = 'resumed', 'Resumed'
    FALLBACK_EXECUTED = 'fallback_executed', 'Fallback Executed'
    ROLLED_BACK = 'rolled_back', 'Rolled Back'
    DEAD_LETTERED = 'dead_lettered', 'Dead Lettered'
    MANUAL_INTERVENTION_REQUIRED = 'manual_intervention_required', 'Manual Intervention Required'
    RESOLVED = 'resolved', 'Resolved'
    FAILED = 'failed', 'Failed'


class RecoveryStrategy(models.TextChoices):
    IMMEDIATE_RETRY = 'immediate_retry', 'Immediate Retry'
    DELAYED_RETRY = 'delayed_retry', 'Delayed Retry'
    RESUME_FROM_NODE = 'resume_from_node', 'Resume from Node'
    FALLBACK_PATH = 'fallback_path', 'Fallback Path'
    ROLLBACK = 'rollback', 'Rollback'
    DEAD_LETTER = 'dead_letter', 'Dead Letter'
    MANUAL = 'manual', 'Manual Intervention'


class FailureType(models.TextChoices):
    TRANSIENT = 'transient', 'Transient'
    DEPENDENCY_UNAVAILABLE = 'dependency_unavailable', 'Dependency Unavailable'
    CONFIGURATION_ERROR = 'configuration_error', 'Configuration Error'
    PERMISSION_ERROR = 'permission_error', 'Permission Error'
    VALIDATION_ERROR = 'validation_error', 'Validation Error'
    PROVIDER_ERROR = 'provider_error', 'Provider Error'
    DATA_INTEGRITY_ERROR = 'data_integrity_error', 'Data Integrity Error'
    UNRECOVERABLE = 'unrecoverable', 'Unrecoverable'


class AttemptStatus(models.TextChoices):
    RUNNING = 'running', 'Running'
    SUCCEEDED = 'succeeded', 'Succeeded'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'


class DeadLetterStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    INVESTIGATING = 'investigating', 'Investigating'
    RETRIED = 'retried', 'Retried'
    RESOLVED = 'resolved', 'Resolved'
    IGNORED = 'ignored', 'Ignored'


class InsightType(models.TextChoices):
    REPEATED_RETRY_FAILURE = 'repeated_retry_failure', 'Repeated Retry Failure'
    DEPENDENCY_FAILURE_PATTERN = 'dependency_failure_pattern', 'Dependency Failure Pattern'
    FALLBACK_OVERUSE = 'fallback_overuse', 'Fallback Overuse'
    DEAD_LETTER_SPIKE = 'dead_letter_spike', 'Dead Letter Spike'
    ROLLBACK_RISK = 'rollback_risk', 'Rollback Risk'
    MANUAL_INTERVENTION_HOTSPOT = 'manual_intervention_hotspot', 'Manual Intervention Hotspot'


class InsightStatus(models.TextChoices):
    NEW = 'new', 'New'
    ACKNOWLEDGED = 'acknowledged', 'Acknowledged'
    RESOLVED = 'resolved', 'Resolved'
    IGNORED = 'ignored', 'Ignored'


# ---------------------------------------------------------------------------
# Model 1 — WorkflowRecoveryCase
# ---------------------------------------------------------------------------

class WorkflowRecoveryCase(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    execution_id = models.UUIDField(db_index=True)
    failure_node_id = models.UUIDField(null=True, blank=True)
    failure_type = models.CharField(
        max_length=30, choices=FailureType.choices, default=FailureType.TRANSIENT
    )
    recovery_status = models.CharField(
        max_length=40, choices=RecoveryStatus.choices, default=RecoveryStatus.OPEN, db_index=True
    )
    recovery_strategy = models.CharField(
        max_length=30, choices=RecoveryStrategy.choices, null=True, blank=True
    )
    retry_count = models.PositiveIntegerField(default=0)
    max_retry_limit = models.PositiveIntegerField(default=3)
    error_message = models.TextField(blank=True)
    execution_snapshot = models.JSONField(default=dict, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'wf_recovery_cases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'recovery_status']),
            models.Index(fields=['tenant_id', 'workflow_id']),
            models.Index(fields=['tenant_id', 'execution_id']),
        ]


# ---------------------------------------------------------------------------
# Model 2 — WorkflowRecoveryAttempt
# ---------------------------------------------------------------------------

class WorkflowRecoveryAttempt(BaseModel):
    recovery_case = models.ForeignKey(
        WorkflowRecoveryCase, on_delete=models.CASCADE, related_name='attempts'
    )
    attempt_number = models.PositiveIntegerField()
    strategy_used = models.CharField(max_length=30, choices=RecoveryStrategy.choices)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=AttemptStatus.choices, default=AttemptStatus.RUNNING
    )
    error_message = models.TextField(blank=True)
    recovery_output = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_recovery_attempts'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['tenant_id', 'recovery_case_id']),
        ]


# ---------------------------------------------------------------------------
# Model 3 — WorkflowDeadLetterItem
# ---------------------------------------------------------------------------

class WorkflowDeadLetterItem(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    execution_id = models.UUIDField(db_index=True)
    entity_type = models.CharField(max_length=100, blank=True)
    entity_id = models.UUIDField(null=True, blank=True)
    failed_node_id = models.UUIDField(null=True, blank=True)
    failure_reason = models.TextField()
    payload_snapshot = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20, choices=DeadLetterStatus.choices, default=DeadLetterStatus.PENDING, db_index=True
    )
    assigned_to = models.UUIDField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'wf_dead_letter_items'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'workflow_id']),
        ]


# ---------------------------------------------------------------------------
# Model 4 — WorkflowFallbackRule
# ---------------------------------------------------------------------------

class FallbackActionType(models.TextChoices):
    SEND_EMAIL = 'send_email', 'Send Email'
    ASSIGN_MANAGER = 'assign_manager', 'Assign to Manager'
    CREATE_TASK = 'create_task', 'Create Manual Task'
    SKIP_NODE = 'skip_node', 'Skip Node'
    NOTIFY_ADMIN = 'notify_admin', 'Notify Admin'
    CUSTOM_ACTION = 'custom_action', 'Custom Action'


class WorkflowFallbackRule(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    node_id = models.UUIDField(db_index=True)
    failure_type = models.CharField(
        max_length=30, choices=FailureType.choices, default=FailureType.TRANSIENT
    )
    fallback_action_type = models.CharField(max_length=30, choices=FallbackActionType.choices)
    fallback_config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'wf_fallback_rules'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'workflow_id', 'node_id']),
            models.Index(fields=['tenant_id', 'is_active']),
        ]


# ---------------------------------------------------------------------------
# Model 5 — WorkflowRecoveryInsight
# ---------------------------------------------------------------------------

class WorkflowRecoveryInsight(BaseModel):
    workflow_id = models.UUIDField(db_index=True, null=True, blank=True)
    insight_type = models.CharField(max_length=40, choices=InsightType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField()
    recommendation = models.TextField(blank=True)
    occurrence_count = models.PositiveIntegerField(default=1)
    last_seen_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20, choices=InsightStatus.choices, default=InsightStatus.NEW, db_index=True
    )

    class Meta:
        db_table = 'wf_recovery_insights'
        ordering = ['-last_seen_at']
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'insight_type']),
        ]
