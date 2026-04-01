from django.contrib import admin

from apps.module_registry.models import (
    GeneratedPrompt,
    ModuleAuditLog,
    ModuleBlocker,
    ModuleBuildRecommendation,
    ModuleClassification,
    ModuleContinuationNote,
    ModuleDependency,
    ModuleDependencyChain,
    ModuleGapRecord,
    NextModuleCandidateScore,
    NextModuleDecisionAudit,
    NextModuleDelayRisk,
    NextModuleDependencyPressure,
    NextModuleReadinessRecord,
    NextModuleRecommendation,
    NextModuleRejectionReason,
    NextModuleSelection,
    NextModuleSequencePlan,
    PromptContext,
    PromptDependency,
    PromptHistory,
    PromptScope,
    PromptVersion,
    ModuleOwner,
    ModulePhaseMapping,
    ModulePlanningAuditLog,
    ModulePriorityRecord,
    ModuleRegistry,
    ModuleSequencePlan,
    ModuleStatus,
    RemainingModuleMap,
)


class ModuleDependencyInline(admin.TabularInline):
    model = ModuleDependency
    fk_name = 'module'
    extra = 0
    autocomplete_fields = ['depends_on']


class ModuleOwnerInline(admin.TabularInline):
    model = ModuleOwner
    extra = 0


class ModuleBlockerInline(admin.TabularInline):
    model = ModuleBlocker
    extra = 0


class ModuleGapRecordInline(admin.TabularInline):
    model = ModuleGapRecord
    extra = 0


class ModuleDependencyChainInline(admin.TabularInline):
    model = ModuleDependencyChain
    fk_name = 'module'
    extra = 0
    autocomplete_fields = ['depends_on']


class ModuleContinuationNoteInline(admin.TabularInline):
    model = ModuleContinuationNote
    extra = 0


class NextModuleCandidateScoreInline(admin.TabularInline):
    model = NextModuleCandidateScore
    extra = 0


class NextModuleRejectionReasonInline(admin.TabularInline):
    model = NextModuleRejectionReason
    extra = 0


class NextModuleSequencePlanInline(admin.TabularInline):
    model = NextModuleSequencePlan
    extra = 0


class PromptHistoryInline(admin.TabularInline):
    model = PromptHistory
    extra = 0


class PromptDependencyInline(admin.TabularInline):
    model = PromptDependency
    extra = 0
    autocomplete_fields = ['depends_on']


class PromptScopeInline(admin.TabularInline):
    model = PromptScope
    extra = 0


class RemainingModuleMapInline(admin.StackedInline):
    model = RemainingModuleMap
    extra = 0


@admin.register(ModuleRegistry)
class ModuleRegistryAdmin(admin.ModelAdmin):
    list_display = (
        'module_key',
        'module_name',
        'module_domain',
        'status',
        'architecture_status',
        'backend_status',
        'frontend_status',
        'integration_status',
        'qa_status',
        'priority_level',
        'implementation_order',
    )
    list_filter = (
        'module_domain',
        'status',
        'architecture_status',
        'backend_status',
        'frontend_status',
        'integration_status',
        'qa_status',
        'priority_level',
        'dependency_status',
        'blocker_status',
    )
    search_fields = ('module_key', 'module_name', 'notes')
    ordering = ('implementation_order', 'priority_level', 'module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [
        RemainingModuleMapInline,
        ModuleDependencyInline,
        ModuleOwnerInline,
        ModuleBlockerInline,
        ModuleGapRecordInline,
        ModuleDependencyChainInline,
        ModuleContinuationNoteInline,
        NextModuleCandidateScoreInline,
        NextModuleRejectionReasonInline,
        NextModuleSequencePlanInline,
    ]


@admin.register(ModuleStatus)
class ModuleStatusAdmin(admin.ModelAdmin):
    list_display = (
        'module',
        'status',
        'architecture_status',
        'backend_status',
        'frontend_status',
        'integration_status',
        'qa_status',
        'implementation_ready',
    )
    list_filter = (
        'status',
        'architecture_status',
        'backend_status',
        'frontend_status',
        'integration_status',
        'qa_status',
        'implementation_ready',
        'verification_required',
    )
    search_fields = ('module__module_key', 'module__module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(ModuleDependency)
class ModuleDependencyAdmin(admin.ModelAdmin):
    list_display = ('module', 'depends_on', 'dependency_status', 'is_hard_blocker')
    list_filter = ('dependency_status', 'is_hard_blocker')
    search_fields = ('module__module_key', 'depends_on__module_key', 'notes')
    ordering = ('module__implementation_order', 'module__module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module', 'depends_on']


@admin.register(ModuleOwner)
class ModuleOwnerAdmin(admin.ModelAdmin):
    list_display = ('module', 'owner_tool', 'owner_name', 'responsibility', 'is_primary')
    list_filter = ('owner_tool', 'is_primary')
    search_fields = ('module__module_key', 'module__module_name', 'owner_tool', 'owner_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(ModuleBlocker)
class ModuleBlockerAdmin(admin.ModelAdmin):
    list_display = ('module', 'title', 'blocker_status', 'severity', 'priority_level', 'resolved_at')
    list_filter = ('blocker_status', 'severity', 'priority_level')
    search_fields = ('module__module_key', 'module__module_name', 'title', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(ModuleAuditLog)
class ModuleAuditLogAdmin(admin.ModelAdmin):
    list_display = ('module', 'event_type', 'actor_name', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('module__module_key', 'module__module_name', 'actor_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(RemainingModuleMap)
class RemainingModuleMapAdmin(admin.ModelAdmin):
    list_display = (
        'module',
        'classification_status',
        'priority_score',
        'phase_bucket',
        'backend_gap_status',
        'frontend_gap_status',
        'dependency_chain_status',
        'sequence_order',
        'owner_tool',
    )
    list_filter = (
        'classification_status',
        'phase_bucket',
        'backend_gap_status',
        'frontend_gap_status',
        'dependency_chain_status',
    )
    search_fields = ('module__module_key', 'module__module_name', 'recommended_next_action', 'blocker_reason', 'notes')
    ordering = ('-priority_score', 'sequence_order', 'module__module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(ModulePriorityRecord)
class ModulePriorityRecordAdmin(admin.ModelAdmin):
    list_display = ('module', 'priority_score', 'product_criticality', 'dependency_weight', 'cross_system_impact')
    list_filter = ('priority_score',)
    search_fields = ('module__module_key', 'module__module_name', 'notes')
    ordering = ('-priority_score', 'module__module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(ModuleGapRecord)
class ModuleGapRecordAdmin(admin.ModelAdmin):
    list_display = (
        'module',
        'backend_gap_status',
        'frontend_gap_status',
        'integration_gap_status',
        'architecture_gap_status',
        'qa_gap_status',
    )
    list_filter = (
        'backend_gap_status',
        'frontend_gap_status',
        'integration_gap_status',
        'architecture_gap_status',
        'qa_gap_status',
    )
    search_fields = ('module__module_key', 'module__module_name', 'blocker_reason', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(ModuleClassification)
class ModuleClassificationAdmin(admin.ModelAdmin):
    list_display = (
        'module',
        'classification_status',
        'phase_bucket',
        'is_parallel_safe',
        'is_backend_first',
        'is_frontend_blocked',
        'is_architecture_only',
    )
    list_filter = (
        'classification_status',
        'phase_bucket',
        'is_parallel_safe',
        'is_backend_first',
        'is_frontend_blocked',
        'is_architecture_only',
    )
    search_fields = ('module__module_key', 'module__module_name', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(ModuleSequencePlan)
class ModuleSequencePlanAdmin(admin.ModelAdmin):
    list_display = ('module', 'sequence_order', 'phase_bucket', 'is_parallel_safe', 'owner_tool')
    list_filter = ('phase_bucket', 'is_parallel_safe')
    search_fields = ('module__module_key', 'module__module_name', 'recommended_next_action', 'notes')
    ordering = ('sequence_order', '-module__priority_level')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(ModuleDependencyChain)
class ModuleDependencyChainAdmin(admin.ModelAdmin):
    list_display = ('module', 'depends_on', 'dependency_chain_status', 'sequence_order', 'is_hard_dependency')
    list_filter = ('dependency_chain_status', 'is_hard_dependency')
    search_fields = ('module__module_key', 'depends_on__module_key', 'notes')
    ordering = ('sequence_order', 'module__module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module', 'depends_on']


@admin.register(ModuleBuildRecommendation)
class ModuleBuildRecommendationAdmin(admin.ModelAdmin):
    list_display = ('module', 'planning_responsibility', 'owner_tool', 'created_at')
    list_filter = ('planning_responsibility', 'owner_tool')
    search_fields = ('module__module_key', 'module__module_name', 'recommended_next_action', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(ModulePhaseMapping)
class ModulePhaseMappingAdmin(admin.ModelAdmin):
    list_display = ('module', 'phase_bucket', 'mvp_status', 'enterprise_status')
    list_filter = ('phase_bucket', 'mvp_status', 'enterprise_status')
    search_fields = ('module__module_key', 'module__module_name', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(ModuleContinuationNote)
class ModuleContinuationNoteAdmin(admin.ModelAdmin):
    list_display = ('module', 'owner_tool', 'next_prompt_hint', 'created_at')
    list_filter = ('owner_tool',)
    search_fields = ('module__module_key', 'module__module_name', 'note', 'next_prompt_hint')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(ModulePlanningAuditLog)
class ModulePlanningAuditLogAdmin(admin.ModelAdmin):
    list_display = ('module', 'event_type', 'actor_name', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('module__module_key', 'module__module_name', 'actor_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(NextModuleSelection)
class NextModuleSelectionAdmin(admin.ModelAdmin):
    list_display = (
        'module',
        'candidate_status',
        'final_selection_score',
        'selection_status',
        'recommended_build_mode',
        'sequence_rank',
        'recommended_owner_type',
    )
    list_filter = ('candidate_status', 'selection_status', 'recommended_build_mode')
    search_fields = ('module__module_key', 'module__module_name', 'recommended_next_step', 'rejection_reason', 'notes')
    ordering = ('-final_selection_score', 'sequence_rank', 'module__module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(NextModuleCandidateScore)
class NextModuleCandidateScoreAdmin(admin.ModelAdmin):
    list_display = ('module', 'candidate_status', 'criticality_score', 'dependency_score', 'readiness_score', 'final_selection_score')
    list_filter = ('candidate_status',)
    search_fields = ('module__module_key', 'module__module_name', 'notes')
    ordering = ('-final_selection_score', 'module__module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(NextModuleDependencyPressure)
class NextModuleDependencyPressureAdmin(admin.ModelAdmin):
    list_display = ('module', 'dependency_score', 'blocking_dependency_count', 'downstream_modules_affected')
    list_filter = ('dependency_score',)
    search_fields = ('module__module_key', 'module__module_name', 'notes')
    ordering = ('-dependency_score', 'module__module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(NextModuleDelayRisk)
class NextModuleDelayRiskAdmin(admin.ModelAdmin):
    list_display = ('module', 'delay_risk_score', 'user_journey_risk', 'dependency_risk', 'coordination_risk')
    list_filter = ('delay_risk_score',)
    search_fields = ('module__module_key', 'module__module_name', 'notes')
    ordering = ('-delay_risk_score', 'module__module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(NextModuleReadinessRecord)
class NextModuleReadinessRecordAdmin(admin.ModelAdmin):
    list_display = (
        'module',
        'readiness_score',
        'ambiguity_score',
        'backend_first_recommended',
        'frontend_first_recommended',
        'blocked_by_business_rule',
        'can_codex_start_immediately',
    )
    list_filter = (
        'backend_first_recommended',
        'frontend_first_recommended',
        'blocked_by_business_rule',
        'can_codex_start_immediately',
    )
    search_fields = ('module__module_key', 'module__module_name', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(NextModuleRecommendation)
class NextModuleRecommendationAdmin(admin.ModelAdmin):
    list_display = ('module', 'selection_status', 'recommended_build_mode', 'recommended_owner_type', 'created_at')
    list_filter = ('selection_status', 'recommended_build_mode', 'recommended_owner_type')
    search_fields = ('module__module_key', 'module__module_name', 'why_selected', 'recommended_next_step', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(NextModuleRejectionReason)
class NextModuleRejectionReasonAdmin(admin.ModelAdmin):
    list_display = ('module', 'rejected_due_to', 'sequence_rank', 'created_at')
    list_filter = ('rejected_due_to',)
    search_fields = ('module__module_key', 'module__module_name', 'rejection_reason')
    ordering = ('sequence_rank', 'module__module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(NextModuleSequencePlan)
class NextModuleSequencePlanAdmin(admin.ModelAdmin):
    list_display = ('module', 'sequence_rank', 'recommended_build_mode', 'created_at')
    list_filter = ('recommended_build_mode',)
    search_fields = ('module__module_key', 'module__module_name', 'recommended_next_step', 'prerequisite_summary', 'notes')
    ordering = ('sequence_rank', 'module__module_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(NextModuleDecisionAudit)
class NextModuleDecisionAuditAdmin(admin.ModelAdmin):
    list_display = ('module', 'event_type', 'actor_name', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('module__module_key', 'module__module_name', 'actor_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']


@admin.register(GeneratedPrompt)
class GeneratedPromptAdmin(admin.ModelAdmin):
    list_display = ('prompt_id', 'module', 'prompt_title', 'prompt_status', 'prompt_version', 'generated_by', 'approved_by', 'created_at')
    list_filter = ('prompt_status', 'prompt_version', 'generated_by', 'approved_by')
    search_fields = ('module__module_key', 'module__module_name', 'prompt_title', 'prompt_body')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'prompt_id', 'created_at', 'updated_at')
    autocomplete_fields = ['module']
    inlines = [PromptDependencyInline, PromptScopeInline, PromptHistoryInline]


@admin.register(PromptContext)
class PromptContextAdmin(admin.ModelAdmin):
    list_display = ('prompt', 'module_key', 'created_at')
    list_filter = ('module_key',)
    search_fields = ('prompt__module__module_key', 'module_key')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['prompt']


@admin.register(PromptDependency)
class PromptDependencyAdmin(admin.ModelAdmin):
    list_display = ('prompt', 'depends_on', 'created_at')
    search_fields = ('prompt__module__module_key', 'depends_on__module_key', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['prompt', 'depends_on']


@admin.register(PromptScope)
class PromptScopeAdmin(admin.ModelAdmin):
    list_display = ('prompt', 'scope_type', 'created_at')
    list_filter = ('scope_type',)
    search_fields = ('prompt__module__module_key', 'scope_type')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['prompt']


@admin.register(PromptHistory)
class PromptHistoryAdmin(admin.ModelAdmin):
    list_display = ('prompt', 'event_type', 'actor_name', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('prompt__module__module_key', 'actor_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['prompt']


@admin.register(PromptVersion)
class PromptVersionAdmin(admin.ModelAdmin):
    list_display = ('prompt', 'prompt_version', 'created_at')
    list_filter = ('prompt_version',)
    search_fields = ('prompt__module__module_key',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['prompt']
