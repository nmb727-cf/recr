from django.db import models

from shared.models import BaseModel
from apps.orchestration_center.constants.execution_statuses import ApprovalMode, HealthStatus, ProviderStatus


class AIProvider(BaseModel):
    class ProviderType(models.TextChoices):
        LOCAL = 'local', 'Local'
        EXTERNAL_API = 'external_api', 'External API'
        INTERNAL_SERVICE = 'internal_service', 'Internal Service'

    provider_key = models.CharField(max_length=64, db_index=True)
    provider_name = models.CharField(max_length=128, db_index=True)
    provider_type = models.CharField(max_length=32, choices=ProviderType.choices, default=ProviderType.EXTERNAL_API)
    status = models.CharField(max_length=32, choices=ProviderStatus.choices, default=ProviderStatus.ACTIVE, db_index=True)
    base_url = models.URLField(blank=True)
    api_version = models.CharField(max_length=32, blank=True)
    timeout_seconds = models.PositiveIntegerField(default=30)
    connect_timeout_seconds = models.PositiveIntegerField(default=5)
    read_timeout_seconds = models.PositiveIntegerField(default=25)
    max_retries = models.PositiveSmallIntegerField(default=2)
    priority_order = models.PositiveSmallIntegerField(default=100, db_index=True)
    supports_streaming = models.BooleanField(default=False)
    supports_structured_output = models.BooleanField(default=False)
    health_status = models.CharField(max_length=32, choices=HealthStatus.choices, default=HealthStatus.UNKNOWN, db_index=True)
    last_health_checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'icc_ai_providers'
        ordering = ['priority_order', 'provider_name']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'provider_key'],
                condition=models.Q(is_deleted=False),
                name='uniq_icc_provider_tenant_key_active',
            ),
        ]

    def __str__(self):
        return self.provider_name


class AIModel(BaseModel):
    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, related_name='models')
    model_key = models.CharField(max_length=128)
    model_name = models.CharField(max_length=128)
    capability_type = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, choices=ProviderStatus.choices, default=ProviderStatus.ACTIVE, db_index=True)
    context_window = models.IntegerField(null=True, blank=True)
    max_output_tokens = models.IntegerField(null=True, blank=True)
    cost_class = models.CharField(max_length=32, blank=True)
    supports_json_schema = models.BooleanField(default=False)
    supports_tools = models.BooleanField(default=False)
    supports_multimodal = models.BooleanField(default=False)
    latency_tier = models.CharField(max_length=32, blank=True)
    quality_tier = models.CharField(max_length=32, blank=True)
    health_status = models.CharField(max_length=32, choices=HealthStatus.choices, default=HealthStatus.UNKNOWN, db_index=True)

    class Meta:
        db_table = 'icc_ai_models'
        ordering = ['provider__priority_order', 'model_name']
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'tenant_id', 'model_key'],
                condition=models.Q(is_deleted=False),
                name='uniq_icc_model_provider_tenant_key_active',
            ),
        ]

    def __str__(self):
        return f'{self.provider.provider_key}:{self.model_key}'


class ProviderConfig(BaseModel):
    class Environment(models.TextChoices):
        DEV = 'dev', 'Dev'
        STAGING = 'staging', 'Staging'
        PROD = 'prod', 'Prod'

    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, related_name='configs')
    environment = models.CharField(max_length=32, choices=Environment.choices, default=Environment.PROD)
    credential_ref = models.CharField(max_length=255)
    allowed_use_cases_json = models.JSONField(default=list, blank=True)
    rate_limit_per_minute = models.IntegerField(null=True, blank=True)
    cost_limit_daily = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'icc_provider_configs'
        ordering = ['provider__provider_name', 'environment']

    def __str__(self):
        return f'{self.provider.provider_name} [{self.environment}]'


class ModelRoutingRule(BaseModel):
    module_scope = models.CharField(max_length=64, db_index=True)
    use_case_key = models.CharField(max_length=64, db_index=True)
    primary_provider = models.ForeignKey(AIProvider, on_delete=models.PROTECT, related_name='primary_routing_rules')
    primary_model = models.ForeignKey(AIModel, on_delete=models.PROTECT, related_name='primary_routing_rules')
    fallback_chain_json = models.JSONField(default=list, blank=True)
    timeout_override_seconds = models.IntegerField(null=True, blank=True)
    retry_override_count = models.PositiveSmallIntegerField(null=True, blank=True)
    approval_mode = models.CharField(max_length=32, choices=ApprovalMode.choices, default=ApprovalMode.SUGGESTION_ONLY)
    status = models.CharField(max_length=32, choices=ProviderStatus.choices, default=ProviderStatus.ACTIVE, db_index=True)

    class Meta:
        db_table = 'icc_model_routing_rules'
        ordering = ['module_scope', 'use_case_key']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'module_scope', 'use_case_key'],
                condition=models.Q(is_deleted=False),
                name='uniq_icc_routing_rule_tenant_scope_use_case',
            ),
        ]

    def __str__(self):
        return f'{self.module_scope}:{self.use_case_key}'

