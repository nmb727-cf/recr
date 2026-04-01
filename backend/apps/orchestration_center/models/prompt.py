from django.db import models

from shared.models import BaseModel
from apps.orchestration_center.constants.execution_statuses import PromptStatus, ValidationStatus


class PromptTemplate(BaseModel):
    prompt_key = models.CharField(max_length=128, db_index=True)
    prompt_title = models.CharField(max_length=255)
    module_scope = models.CharField(max_length=64, db_index=True)
    use_case_key = models.CharField(max_length=64, db_index=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=PromptStatus.choices, default=PromptStatus.DRAFT, db_index=True)
    active_version_id = models.UUIDField(null=True, blank=True)
    approval_required = models.BooleanField(default=True)
    tenant_override_allowed = models.BooleanField(default=False)
    safety_notes = models.TextField(blank=True)
    owner_role = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = 'icc_prompt_templates'
        ordering = ['module_scope', 'use_case_key', 'prompt_title']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'prompt_key'],
                condition=models.Q(is_deleted=False),
                name='uniq_icc_prompt_template_tenant_key_active',
            ),
        ]

    def __str__(self):
        return self.prompt_title


class PromptVersion(BaseModel):
    prompt_template = models.ForeignKey(PromptTemplate, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    status = models.CharField(max_length=32, choices=PromptStatus.choices, default=PromptStatus.DRAFT, db_index=True)
    system_prompt = models.TextField()
    user_prompt_template = models.TextField()
    variables_schema_json = models.JSONField(default=dict, blank=True)
    expected_output_schema_json = models.JSONField(default=dict, blank=True)
    validation_rules_json = models.JSONField(default=dict, blank=True)
    fallback_version_id = models.UUIDField(null=True, blank=True)
    approval_required = models.BooleanField(default=True)
    approved_by_id = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    activation_notes = models.TextField(blank=True)
    diff_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'icc_prompt_versions'
        ordering = ['-version_number']
        constraints = [
            models.UniqueConstraint(fields=['prompt_template', 'version_number'], name='uniq_icc_prompt_template_version'),
        ]

    def __str__(self):
        return f'{self.prompt_template.prompt_key} v{self.version_number}'


class PromptScope(BaseModel):
    prompt_template = models.ForeignKey(PromptTemplate, on_delete=models.CASCADE, related_name='scopes')
    module_scope = models.CharField(max_length=64, db_index=True)
    entity_type = models.CharField(max_length=64, blank=True)
    use_case_key = models.CharField(max_length=64, db_index=True)
    priority_order = models.PositiveSmallIntegerField(default=100)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'icc_prompt_scopes'
        ordering = ['priority_order', 'module_scope']

    def __str__(self):
        return f'{self.prompt_template.prompt_key}:{self.module_scope}:{self.use_case_key}'


class PromptTestRun(BaseModel):
    prompt_version = models.ForeignKey(PromptVersion, on_delete=models.CASCADE, related_name='test_runs')
    test_input_json = models.JSONField(default=dict, blank=True)
    raw_response_ref = models.CharField(max_length=255, blank=True)
    normalized_output_json = models.JSONField(default=dict, blank=True)
    validation_status = models.CharField(max_length=32, choices=ValidationStatus.choices, default=ValidationStatus.NOT_CHECKED, db_index=True)
    run_status = models.CharField(max_length=32, choices=ValidationStatus.choices, default=ValidationStatus.NOT_CHECKED, db_index=True)
    executed_by_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'icc_prompt_test_runs'
        ordering = ['-created_at']

    def __str__(self):
        return f'Test {self.prompt_version}'

