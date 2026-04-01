from django.db import models

from shared.models import BaseModel
from apps.orchestration_center.constants.execution_statuses import ApprovalMode, ConnectorStatus


class IntelligenceConnector(BaseModel):
    module_code = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, choices=ConnectorStatus.choices, default=ConnectorStatus.ACTIVE, db_index=True)
    events_consumed_json = models.JSONField(default=list, blank=True)
    ai_actions_allowed_json = models.JSONField(default=list, blank=True)
    automation_actions_allowed_json = models.JSONField(default=list, blank=True)
    fallback_behavior = models.CharField(max_length=64, default='manual_continue')
    compatibility_notes = models.TextField(blank=True)
    version_tag = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = 'icc_intelligence_connectors'
        ordering = ['module_code']
        constraints = [
            models.UniqueConstraint(fields=['tenant_id', 'module_code'], name='uniq_icc_connector_tenant_module'),
        ]

    def __str__(self):
        return self.module_code


class TenantIntelligenceSettings(BaseModel):
    tenant_id = models.UUIDField(unique=True, db_index=True)
    ai_enabled = models.BooleanField(default=False)
    automation_enabled = models.BooleanField(default=False)
    default_approval_mode = models.CharField(max_length=32, choices=ApprovalMode.choices, default=ApprovalMode.SUGGESTION_ONLY)
    allowed_provider_ids_json = models.JSONField(default=list, blank=True)
    feature_flags_json = models.JSONField(default=dict, blank=True)
    notification_preferences_json = models.JSONField(default=dict, blank=True)
    retry_policy_overrides_json = models.JSONField(default=dict, blank=True)
    connector_enablement_json = models.JSONField(default=dict, blank=True)
    visibility_permissions_json = models.JSONField(default=dict, blank=True)
    updated_by_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'icc_tenant_intelligence_settings'
        ordering = ['-updated_at']

    def __str__(self):
        return f'Settings:{self.tenant_id}'

