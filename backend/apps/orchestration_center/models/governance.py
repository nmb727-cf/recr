from django.db import models
from shared.models import BaseModel
from apps.orchestration_center.constants.execution_statuses import ApprovalStatus, DeadLetterStatus, FailureSeverity, FailureStatus
from apps.orchestration_center.models.workflow import Workflow, WorkflowVersion, WorkflowExecution

class WorkflowApproval(BaseModel):
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='approvals')
    version = models.ForeignKey(WorkflowVersion, on_delete=models.CASCADE, related_name='approval_requests')
    requested_by = models.UUIDField(db_index=True)
    status = models.CharField(max_length=32, choices=APPROVAL_STATUS, default='pending', db_index=True)
    approved_by = models.UUIDField(null=True, blank=True)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'icc_workflow_approvals'
        ordering = ['-created_at']

class WorkflowSafetyRule(BaseModel):
    workflow = models.OneToOneField(Workflow, on_delete=models.CASCADE, related_name='safety_rule')
    max_executions_per_hour = models.IntegerField(default=100)
    max_executions_per_day = models.IntegerField(default=1000)
    require_confirmation = models.BooleanField(default=False)
    alert_threshold_percentage = models.IntegerField(default=80)
    is_paused_by_system = models.BooleanField(default=False)
    last_violation_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'icc_workflow_safety_rules'

class WorkflowRollbackLog(BaseModel):
    execution = models.OneToOneField(WorkflowExecution, on_delete=models.CASCADE, related_name='rollback_log')
    rollback_time = models.DateTimeField(auto_now_add=True)
    performed_by = models.UUIDField()
    status = models.CharField(max_length=32, default='completed') # completed, failed
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'icc_workflow_rollback_logs'

class WorkflowAuditLog(BaseModel):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('edited', 'Edited'),
        ('version_created', 'Version Created'),
        ('activated', 'Activated'),
        ('paused', 'Paused'),
        ('archived', 'Archived'),
        ('executed', 'Executed'),
        ('failed', 'Failed'),
        ('rollback', 'Rollback'),
        ('limit_exceeded', 'Limit Exceeded'),
        ('approval_requested', 'Approval Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=64, choices=ACTION_CHOICES, db_index=True)
    performed_by = models.UUIDField(null=True, blank=True)
    version_number = models.IntegerField(null=True, blank=True)
    execution_id = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'icc_workflow_audit_logs'
        ordering = ['-timestamp']

class ExecutionFailure(BaseModel):
    failure_type = models.CharField(max_length=32, db_index=True)
    related_request_id = models.UUIDField(null=True, blank=True, db_index=True)
    related_run_id = models.UUIDField(null=True, blank=True, db_index=True)
    category = models.CharField(max_length=64, db_index=True)
    severity = models.CharField(max_length=32, choices=FailureSeverity.choices, default=FailureSeverity.MEDIUM, db_index=True)
    status = models.CharField(max_length=32, choices=FailureStatus.choices, default=FailureStatus.NEW, db_index=True)
    retryable = models.BooleanField(default=True, db_index=True)
    max_retries = models.PositiveSmallIntegerField(default=2)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    operator_notes = models.TextField(blank=True)
    last_error_message = models.TextField(blank=True)
    resolved_by_id = models.UUIDField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'icc_execution_failures'
        ordering = ['-created_at']

class DeadLetterItem(BaseModel):
    item_type = models.CharField(max_length=32, db_index=True)
    related_object_id = models.UUIDField(db_index=True)
    reason_code = models.CharField(max_length=64, db_index=True)
    payload_snapshot_json = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, choices=DeadLetterStatus.choices, default=DeadLetterStatus.OPEN, db_index=True)
    requeue_count = models.PositiveSmallIntegerField(default=0)
    resolved_by_id = models.UUIDField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'icc_dead_letter_items'
        ordering = ['-created_at']

class ApprovalQueueItem(BaseModel):
    item_type = models.CharField(max_length=64, db_index=True)
    origin_type = models.CharField(max_length=32, db_index=True)
    origin_id = models.UUIDField(db_index=True)
    requested_action = models.CharField(max_length=64)
    summary_payload_json = models.JSONField(default=dict, blank=True)
    recommended_decision = models.CharField(max_length=32, blank=True)
    approver_role = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING, db_index=True)
    decision_comment = models.TextField(blank=True)
    decided_by_id = models.UUIDField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    applied_by_id = models.UUIDField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'icc_approval_queue_items'
        ordering = ['-created_at']

class AIGovernanceRule(BaseModel):
    RULE_TYPES = [
        ('suggestion_apply', 'Suggestion Apply'),
        ('automation_execute', 'Automation Execute'),
        ('policy_change', 'Policy Change'),
        ('prompt_change', 'Prompt Change'),
        ('execution_retry', 'Execution Retry'),
    ]
    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    rule_name = models.CharField(max_length=255)
    rule_type = models.CharField(max_length=64, choices=RULE_TYPES, db_index=True)
    requires_approval = models.BooleanField(default=True)
    auto_apply_allowed = models.BooleanField(default=False)
    risk_level = models.CharField(max_length=32, choices=RISK_LEVELS, default='medium', db_index=True)

    class Meta:
        db_table = 'icc_ai_governance_rules'

class AIGovernanceApproval(BaseModel):
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    request_type = models.CharField(max_length=64, db_index=True)
    request_payload = models.JSONField(default=dict, blank=True)
    requested_by = models.UUIDField(db_index=True)
    approval_status = models.CharField(max_length=32, choices=APPROVAL_STATUS, default='pending', db_index=True)
    approved_by = models.UUIDField(null=True, blank=True)
    rejected_by = models.UUIDField(null=True, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        db_table = 'icc_ai_governance_approvals'
        ordering = ['-created_at']

class AutomationUsageLimit(BaseModel):
    tenant_id = models.UUIDField(unique=True, db_index=True)
    daily_limit = models.IntegerField(default=1000)
    hourly_limit = models.IntegerField(default=100)
    max_auto_apply = models.IntegerField(default=500)
    max_failures = models.IntegerField(default=50)

    class Meta:
        db_table = 'icc_automation_usage_limits'

class AutomationGovernanceAudit(BaseModel):
    ACTION_CHOICES = [
        ('policy_change', 'Policy Change'),
        ('auto_apply', 'Auto Apply'),
        ('manual_override', 'Manual Override'),
        ('execution_failure', 'Execution Failure'),
        ('kill_switch_toggled', 'Kill Switch Toggled'),
        ('limit_exceeded', 'Limit Exceeded'),
    ]
    action = models.CharField(max_length=64, choices=ACTION_CHOICES, db_index=True)
    performed_by = models.UUIDField(null=True, blank=True)
    target_id = models.UUIDField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'icc_automation_governance_audits'
        ordering = ['-timestamp']
