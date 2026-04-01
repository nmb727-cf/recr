from django.contrib import admin

from apps.orchestration_center.models import (
    AIExecutionArtifact,
    AIExecutionRequest,
    AIExecutionResult,
    AIExecutionReview,
    AIModel,
    AIProvider,
    AISuggestion,
    AISuggestionConversion,
    ApprovalQueueItem,
    AutomationExecutionRun,
    AutomationRule,
    AutomationRuleAction,
    AutomationRuleCondition,
    AutomationRuleScope,
    AutomationScheduledAction,
    DeadLetterItem,
    ExecutionFailure,
    IntelligenceAuditLog,
    IntelligenceConnector,
    ModelRoutingRule,
    PromptScope,
    PromptTemplate,
    PromptTestRun,
    PromptVersion,
    ProviderConfig,
    TenantIntelligenceSettings,
)


class PromptVersionInline(admin.TabularInline):
    model = PromptVersion
    extra = 0


class PromptScopeInline(admin.TabularInline):
    model = PromptScope
    extra = 0


class RuleConditionInline(admin.TabularInline):
    model = AutomationRuleCondition
    extra = 0


class RuleActionInline(admin.TabularInline):
    model = AutomationRuleAction
    extra = 0


class RuleScopeInline(admin.TabularInline):
    model = AutomationRuleScope
    extra = 0


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ('provider_name', 'provider_key', 'provider_type', 'status', 'health_status', 'priority_order', 'tenant_id')
    list_filter = ('provider_type', 'status', 'health_status')
    search_fields = ('provider_name', 'provider_key')


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'model_key', 'provider', 'capability_type', 'status', 'health_status', 'tenant_id')
    list_filter = ('capability_type', 'status', 'health_status')
    search_fields = ('model_name', 'model_key')


@admin.register(ProviderConfig)
class ProviderConfigAdmin(admin.ModelAdmin):
    list_display = ('provider', 'environment', 'is_active', 'tenant_id')
    list_filter = ('environment', 'is_active')
    search_fields = ('provider__provider_name', 'credential_ref')


@admin.register(ModelRoutingRule)
class ModelRoutingRuleAdmin(admin.ModelAdmin):
    list_display = ('module_scope', 'use_case_key', 'primary_provider', 'primary_model', 'approval_mode', 'status', 'tenant_id')
    list_filter = ('module_scope', 'approval_mode', 'status')
    search_fields = ('module_scope', 'use_case_key')


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ('prompt_title', 'prompt_key', 'module_scope', 'use_case_key', 'status', 'tenant_id')
    list_filter = ('module_scope', 'status', 'tenant_override_allowed')
    search_fields = ('prompt_title', 'prompt_key', 'use_case_key')
    inlines = [PromptVersionInline, PromptScopeInline]


@admin.register(PromptVersion)
class PromptVersionAdmin(admin.ModelAdmin):
    list_display = ('prompt_template', 'version_number', 'status', 'approval_required', 'approved_at')
    list_filter = ('status', 'approval_required')
    search_fields = ('prompt_template__prompt_key',)


@admin.register(PromptScope)
class PromptScopeAdmin(admin.ModelAdmin):
    list_display = ('prompt_template', 'module_scope', 'use_case_key', 'priority_order', 'is_active', 'tenant_id')
    list_filter = ('module_scope', 'is_active')
    search_fields = ('prompt_template__prompt_key', 'use_case_key')


@admin.register(PromptTestRun)
class PromptTestRunAdmin(admin.ModelAdmin):
    list_display = ('prompt_version', 'validation_status', 'run_status', 'executed_by_id', 'created_at')
    list_filter = ('validation_status', 'run_status')
    search_fields = ('prompt_version__prompt_template__prompt_key',)


@admin.register(AIExecutionRequest)
class AIExecutionRequestAdmin(admin.ModelAdmin):
    list_display = ('module_scope', 'use_case_key', 'source_entity_type', 'source_entity_id', 'status', 'mode', 'tenant_id', 'created_at')
    list_filter = ('module_scope', 'status', 'mode')
    search_fields = ('use_case_key', 'source_entity_id', 'source_event')


@admin.register(AIExecutionResult)
class AIExecutionResultAdmin(admin.ModelAdmin):
    list_display = ('request', 'validation_status', 'confidence_score', 'execution_ms', 'created_at')
    list_filter = ('validation_status',)


@admin.register(AIExecutionArtifact)
class AIExecutionArtifactAdmin(admin.ModelAdmin):
    list_display = ('request', 'artifact_type', 'storage_ref', 'created_at')
    list_filter = ('artifact_type',)


@admin.register(AIExecutionReview)
class AIExecutionReviewAdmin(admin.ModelAdmin):
    list_display = ('request', 'review_status', 'application_status', 'reviewed_by_id', 'reviewed_at')
    list_filter = ('review_status', 'application_status')


@admin.register(AISuggestion)
class AISuggestionAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'status',
        'source_module',
        'source_entity_type',
        'source_entity_id',
        'confidence_band',
        'requires_approval',
        'tenant_id',
        'created_at',
    )
    list_filter = ('category', 'status', 'confidence_band', 'requires_approval', 'source_module')
    search_fields = ('title', 'summary', 'source_entity_id', 'suggestion_key', 'proposed_action_family')
    readonly_fields = (
        'reviewed_by_id',
        'reviewed_at',
        'approved_by_id',
        'approved_at',
        'rejected_by_id',
        'rejected_at',
        'converted_by_id',
        'converted_at',
    )


@admin.register(AISuggestionConversion)
class AISuggestionConversionAdmin(admin.ModelAdmin):
    list_display = ('suggestion', 'conversion_type', 'status', 'retry_safe', 'tenant_id', 'created_at')
    list_filter = ('conversion_type', 'status', 'retry_safe')
    search_fields = ('suggestion__title', 'idempotency_key', 'error_category')


@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = ('rule_title', 'rule_key', 'module_scope', 'trigger_event', 'mode', 'status', 'tenant_id')
    list_filter = ('module_scope', 'mode', 'status', 'is_builtin')
    search_fields = ('rule_title', 'rule_key', 'trigger_event')
    inlines = [RuleConditionInline, RuleActionInline, RuleScopeInline]


@admin.register(AutomationExecutionRun)
class AutomationExecutionRunAdmin(admin.ModelAdmin):
    list_display = ('rule', 'source_event', 'source_entity_type', 'source_entity_id', 'status', 'tenant_id', 'created_at')
    list_filter = ('status', 'source_event')
    search_fields = ('source_entity_id', 'source_event')


@admin.register(AutomationScheduledAction)
class AutomationScheduledActionAdmin(admin.ModelAdmin):
    list_display = ('run', 'action_type', 'status', 'execute_at', 'tenant_id')
    list_filter = ('status', 'action_type')


@admin.register(IntelligenceConnector)
class IntelligenceConnectorAdmin(admin.ModelAdmin):
    list_display = ('module_code', 'status', 'fallback_behavior', 'version_tag', 'tenant_id')
    list_filter = ('status', 'module_code')
    search_fields = ('module_code',)


@admin.register(TenantIntelligenceSettings)
class TenantIntelligenceSettingsAdmin(admin.ModelAdmin):
    list_display = ('tenant_id', 'ai_enabled', 'automation_enabled', 'default_approval_mode', 'updated_at')
    list_filter = ('ai_enabled', 'automation_enabled', 'default_approval_mode')
    search_fields = ('tenant_id',)


@admin.register(ExecutionFailure)
class ExecutionFailureAdmin(admin.ModelAdmin):
    list_display = ('category', 'failure_type', 'severity', 'status', 'retryable', 'tenant_id', 'created_at')
    list_filter = ('failure_type', 'severity', 'status', 'retryable')
    search_fields = ('category', 'last_error_message')


@admin.register(DeadLetterItem)
class DeadLetterItemAdmin(admin.ModelAdmin):
    list_display = ('item_type', 'reason_code', 'status', 'requeue_count', 'tenant_id', 'created_at')
    list_filter = ('item_type', 'status')
    search_fields = ('reason_code',)


@admin.register(ApprovalQueueItem)
class ApprovalQueueItemAdmin(admin.ModelAdmin):
    list_display = ('item_type', 'origin_type', 'requested_action', 'approver_role', 'status', 'tenant_id', 'created_at')
    list_filter = ('item_type', 'status', 'approver_role')
    search_fields = ('requested_action', 'approver_role')
    readonly_fields = ('decided_by_id', 'decided_at', 'applied_by_id', 'applied_at')


@admin.register(IntelligenceAuditLog)
class IntelligenceAuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'target_type', 'target_id', 'actor_type', 'tenant_id', 'created_at')
    list_filter = ('action_type', 'target_type', 'actor_type')
    search_fields = ('action_type', 'target_type')
