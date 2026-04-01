from django.db import models

from shared.models import BaseModel
from apps.orchestration_center.constants.execution_statuses import (
    ConfidenceBand,
    SuggestionCategory,
    SuggestionConversionStatus,
    SuggestionStatus,
)


class AISuggestion(BaseModel):
    suggestion_key = models.CharField(max_length=64, db_index=True)
    category = models.CharField(max_length=64, choices=SuggestionCategory.choices, db_index=True)
    status = models.CharField(max_length=32, choices=SuggestionStatus.choices, default=SuggestionStatus.DRAFT, db_index=True)
    source_event = models.CharField(max_length=128, blank=True, db_index=True)
    source_module = models.CharField(max_length=64, db_index=True)
    source_entity_type = models.CharField(max_length=64, db_index=True)
    source_entity_id = models.CharField(max_length=64, db_index=True)
    owner_module = models.CharField(max_length=64, blank=True, db_index=True)
    proposed_action_family = models.CharField(max_length=64, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    confidence_band = models.CharField(
        max_length=16,
        choices=ConfidenceBand.choices,
        default=ConfidenceBand.MEDIUM,
        db_index=True,
    )
    payload_json = models.JSONField(default=dict, blank=True)
    rationale_json = models.JSONField(default=dict, blank=True)
    audit_metadata_json = models.JSONField(default=dict, blank=True)
    requires_approval = models.BooleanField(default=False)
    manual_override_allowed = models.BooleanField(default=True)
    review_comment = models.TextField(blank=True)
    approval_comment = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=255, blank=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='superseded_suggestions',
    )
    ai_request = models.ForeignKey(
        'orchestration_center.AIExecutionRequest',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='suggestions',
    )
    approval_item = models.ForeignKey(
        'orchestration_center.ApprovalQueueItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suggestions',
    )
    converted_artifact_type = models.CharField(max_length=64, blank=True)
    converted_artifact_id = models.UUIDField(null=True, blank=True)
    reviewed_by_id = models.UUIDField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_by_id = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by_id = models.UUIDField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    converted_by_id = models.UUIDField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'icc_ai_suggestions'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['idempotency_key'],
                condition=~models.Q(idempotency_key=''),
                name='uniq_icc_ai_suggestion_idempotency_key',
            ),
        ]

    def __str__(self):
        return f'{self.category}:{self.source_entity_type}:{self.status}'


class AISuggestionConversion(BaseModel):
    suggestion = models.ForeignKey(AISuggestion, on_delete=models.CASCADE, related_name='conversions')
    conversion_type = models.CharField(max_length=64, db_index=True)
    status = models.CharField(
        max_length=32,
        choices=SuggestionConversionStatus.choices,
        default=SuggestionConversionStatus.PENDING,
        db_index=True,
    )
    idempotency_key = models.CharField(max_length=255, blank=True, db_index=True)
    requested_by_id = models.UUIDField(null=True, blank=True)
    requested_action_payload_json = models.JSONField(default=dict, blank=True)
    result_payload_json = models.JSONField(default=dict, blank=True)
    error_category = models.CharField(max_length=64, blank=True, db_index=True)
    error_message = models.TextField(blank=True)
    retry_safe = models.BooleanField(default=True, db_index=True)
    approval_item = models.ForeignKey(
        'orchestration_center.ApprovalQueueItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suggestion_conversions',
    )

    class Meta:
        db_table = 'icc_ai_suggestion_conversions'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['idempotency_key'],
                condition=~models.Q(idempotency_key=''),
                name='uniq_icc_ai_suggestion_conversion_idempotency_key',
            ),
        ]

    def __str__(self):
        return f'{self.suggestion_id}:{self.conversion_type}:{self.status}'
