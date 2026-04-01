from django.db import models

from shared.models import BaseModel
from apps.orchestration_center.constants.execution_statuses import ApprovalStatus, DeadLetterStatus, FailureSeverity, FailureStatus


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

    def __str__(self):
        return f'{self.category}:{self.status}'


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

    def __str__(self):
        return f'{self.item_type}:{self.reason_code}'


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

    def __str__(self):
        return f'{self.item_type}:{self.status}'

