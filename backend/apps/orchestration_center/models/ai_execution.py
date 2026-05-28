from django.db import models

from shared.models import BaseModel
from apps.orchestration_center.constants.execution_statuses import (
    AIExecutionStatus,
    ApplicationStatus,
    ApprovalMode,
    ReviewStatus,
    ValidationStatus,
)
from apps.orchestration_center.models.prompt import PromptVersion
from apps.orchestration_center.models.prompt import PromptTemplate
from apps.orchestration_center.constants.execution_statuses import PromptStatus
from apps.orchestration_center.models.provider import AIModel, AIProvider


class AIExecutionRequest(BaseModel):
    module_scope = models.CharField(max_length=64, db_index=True)
    use_case_key = models.CharField(max_length=64, db_index=True)
    source_event = models.CharField(max_length=128, blank=True, db_index=True)
    source_entity_type = models.CharField(max_length=64, db_index=True)
    source_entity_id = models.CharField(max_length=64, db_index=True)
    source_module = models.CharField(max_length=64, db_index=True)
    prompt_version = models.ForeignKey(PromptVersion, on_delete=models.PROTECT, related_name='execution_requests')
    provider = models.ForeignKey(AIProvider, on_delete=models.PROTECT, null=True, blank=True, related_name='execution_requests')
    model = models.ForeignKey(AIModel, on_delete=models.PROTECT, null=True, blank=True, related_name='execution_requests')
    mode = models.CharField(max_length=32, choices=ApprovalMode.choices, default=ApprovalMode.SUGGESTION_ONLY)
    status = models.CharField(max_length=32, choices=AIExecutionStatus.choices, default=AIExecutionStatus.QUEUED, db_index=True)
    context_snapshot_json = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=255, blank=True, db_index=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    max_retries = models.PositiveSmallIntegerField(default=2)
    queued_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    failure_category = models.CharField(max_length=64, blank=True)
    failure_reason = models.TextField(blank=True)
    requires_review = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    final_disposition = models.CharField(max_length=32, blank=True)

    class Meta:
        db_table = 'icc_ai_execution_requests'
        ordering = ['-queued_at']
        constraints = [
            models.UniqueConstraint(
                fields=['idempotency_key'],
                condition=~models.Q(idempotency_key=''),
                name='uniq_icc_ai_execution_idempotency_key',
            ),
        ]

    def __str__(self):
        return f'{self.module_scope}:{self.use_case_key}:{self.status}'

    def save(self, *args, **kwargs):
        if not self.prompt_version_id:
            prompt_version = PromptVersion.objects.filter(
                prompt_template__tenant_id=self.tenant_id,
                prompt_template__is_deleted=False,
                is_deleted=False,
            ).order_by('-created_at').first()
            if prompt_version is None:
                template = PromptTemplate.objects.create(
                    tenant_id=self.tenant_id,
                    prompt_key=f'auto:{self.module_scope}:{self.use_case_key}',
                    prompt_title=f'Auto prompt for {self.use_case_key}',
                    module_scope=self.module_scope or 'global',
                    use_case_key=self.use_case_key or 'generic',
                    status=PromptStatus.ACTIVE,
                    approval_required=False,
                    tenant_override_allowed=True,
                )
                prompt_version = PromptVersion.objects.create(
                    tenant_id=self.tenant_id,
                    prompt_template=template,
                    version_number=1,
                    status=PromptStatus.ACTIVE,
                    system_prompt='Auto-generated prompt placeholder',
                    user_prompt_template='Auto-generated prompt placeholder',
                    approval_required=False,
                )
            self.prompt_version = prompt_version
        super().save(*args, **kwargs)


class AIExecutionResult(BaseModel):
    request = models.OneToOneField(AIExecutionRequest, on_delete=models.CASCADE, related_name='result')
    raw_response_ref = models.CharField(max_length=255, blank=True)
    normalized_output_json = models.JSONField(default=dict, blank=True)
    validation_status = models.CharField(max_length=32, choices=ValidationStatus.choices, default=ValidationStatus.NOT_CHECKED, db_index=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    token_input_count = models.IntegerField(null=True, blank=True)
    token_output_count = models.IntegerField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    execution_ms = models.IntegerField(null=True, blank=True)
    schema_errors_json = models.JSONField(default=list, blank=True)
    warnings_json = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'icc_ai_execution_results'
        ordering = ['-created_at']

    def __str__(self):
        return f'Result for {self.request_id}'


class AIExecutionArtifact(BaseModel):
    request = models.ForeignKey(AIExecutionRequest, on_delete=models.CASCADE, related_name='artifacts')
    artifact_type = models.CharField(max_length=64, db_index=True)
    storage_ref = models.CharField(max_length=255)
    content_hash = models.CharField(max_length=128, blank=True)

    class Meta:
        db_table = 'icc_ai_execution_artifacts'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.artifact_type} for {self.request_id}'


class AIExecutionReview(BaseModel):
    request = models.OneToOneField(AIExecutionRequest, on_delete=models.CASCADE, related_name='review')
    review_status = models.CharField(max_length=32, choices=ReviewStatus.choices, default=ReviewStatus.PENDING, db_index=True)
    reviewed_by_id = models.UUIDField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    decision_comment = models.TextField(blank=True)
    applied_by_id = models.UUIDField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    application_status = models.CharField(max_length=32, choices=ApplicationStatus.choices, default=ApplicationStatus.PENDING)

    class Meta:
        db_table = 'icc_ai_execution_reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f'Review for {self.request_id}'
