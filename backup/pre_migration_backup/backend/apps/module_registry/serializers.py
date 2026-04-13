from rest_framework import serializers

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


class ModuleStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleStatus
        fields = [
            'id', 'module', 'status', 'architecture_status', 'backend_status',
            'frontend_status', 'integration_status', 'qa_status',
            'dependency_status', 'blocker_status', 'architecture_approved',
            'implementation_ready', 'frontend_ready', 'backend_ready',
            'verification_required', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleDependency
        fields = [
            'id', 'module', 'depends_on', 'dependency_status',
            'is_hard_blocker', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleOwner
        fields = [
            'id', 'module', 'owner_tool', 'owner_name', 'responsibility',
            'is_primary', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleBlockerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleBlocker
        fields = [
            'id', 'module', 'title', 'blocker_status', 'priority_level',
            'severity', 'notes', 'resolved_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleAuditLog
        fields = ['id', 'module', 'event_type', 'actor_name', 'event_payload', 'created_at']
        read_only_fields = ['id', 'created_at']


class ModuleGapRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleGapRecord
        fields = [
            'id', 'module', 'backend_gap_status', 'frontend_gap_status',
            'integration_gap_status', 'architecture_gap_status', 'qa_gap_status',
            'blocker_reason', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleDependencyChainSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleDependencyChain
        fields = [
            'id', 'module', 'depends_on', 'dependency_chain_status',
            'sequence_order', 'is_hard_dependency', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleContinuationNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleContinuationNote
        fields = ['id', 'module', 'note', 'owner_tool', 'next_prompt_hint', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModulePriorityRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModulePriorityRecord
        fields = [
            'id', 'module', 'priority_score', 'product_criticality', 'dependency_weight',
            'user_journey_impact', 'frontend_gap_severity', 'backend_gap_severity',
            'blocker_severity', 'implementation_readiness', 'cross_system_impact',
            'near_term_usefulness', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RemainingModuleMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemainingModuleMap
        fields = [
            'id', 'module', 'classification_status', 'priority_score', 'mvp_status',
            'enterprise_status', 'backend_gap_status', 'frontend_gap_status',
            'dependency_chain_status', 'blocker_reason', 'recommended_next_action',
            'phase_bucket', 'sequence_order', 'owner_tool', 'notes', 'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleSequencePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleSequencePlan
        fields = [
            'id', 'module', 'sequence_order', 'phase_bucket', 'recommended_next_action',
            'owner_tool', 'is_parallel_safe', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NextModuleSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextModuleSelection
        fields = [
            'id', 'module', 'candidate_status', 'criticality_score', 'dependency_score',
            'journey_impact_score', 'frontend_gap_score', 'backend_gap_score',
            'readiness_score', 'ambiguity_score', 'delay_risk_score',
            'final_selection_score', 'selection_status', 'rejection_reason',
            'recommended_build_mode', 'recommended_owner_type',
            'recommended_next_step', 'sequence_rank', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NextModuleCandidateScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextModuleCandidateScore
        fields = [
            'id', 'module', 'candidate_status', 'criticality_score', 'dependency_score',
            'journey_impact_score', 'frontend_gap_score', 'backend_gap_score',
            'readiness_score', 'ambiguity_score', 'final_selection_score', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NextModuleDependencyPressureSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextModuleDependencyPressure
        fields = [
            'id', 'module', 'dependency_score', 'blocking_dependency_count',
            'downstream_modules_affected', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NextModuleDelayRiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextModuleDelayRisk
        fields = [
            'id', 'module', 'delay_risk_score', 'user_journey_risk',
            'dependency_risk', 'coordination_risk', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NextModuleReadinessRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextModuleReadinessRecord
        fields = [
            'id', 'module', 'readiness_score', 'ambiguity_score',
            'backend_first_recommended', 'frontend_first_recommended',
            'blocked_by_business_rule', 'can_codex_start_immediately',
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NextModuleRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextModuleRecommendation
        fields = [
            'id', 'module', 'selection_status', 'recommended_build_mode',
            'recommended_owner_type', 'recommended_next_step',
            'why_selected', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NextModuleRejectionReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextModuleRejectionReason
        fields = [
            'id', 'module', 'rejection_reason', 'rejected_due_to',
            'sequence_rank', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NextModuleSequencePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextModuleSequencePlan
        fields = [
            'id', 'module', 'sequence_rank', 'recommended_next_step',
            'recommended_build_mode', 'prerequisite_summary', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GeneratedPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedPrompt
        fields = [
            'id', 'prompt_id', 'module', 'prompt_title', 'prompt_scope',
            'prompt_dependencies', 'prompt_status', 'prompt_version',
            'generated_by', 'approved_by', 'prompt_body', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'prompt_id', 'created_at', 'updated_at']


class PromptContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptContext
        fields = ['id', 'prompt', 'module_key', 'context_payload', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PromptDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptDependency
        fields = ['id', 'prompt', 'depends_on', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PromptScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptScope
        fields = ['id', 'prompt', 'scope_type', 'scope_payload', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PromptHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptHistory
        fields = ['id', 'prompt', 'event_type', 'actor_name', 'event_payload', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PromptVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptVersion
        fields = ['id', 'prompt', 'prompt_version', 'version_snapshot', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleRegistrySerializer(serializers.ModelSerializer):
    status_record = ModuleStatusSerializer(read_only=True)
    dependencies = ModuleDependencySerializer(many=True, read_only=True)
    owners = ModuleOwnerSerializer(many=True, read_only=True)
    blockers = ModuleBlockerSerializer(many=True, read_only=True)

    class Meta:
        model = ModuleRegistry
        fields = [
            'id', 'tenant_id', 'module_key', 'module_name', 'module_domain', 'status',
            'architecture_status', 'backend_status', 'frontend_status',
            'integration_status', 'qa_status', 'dependency_status',
            'blocker_status', 'priority_level', 'implementation_order', 'notes',
            'status_record', 'dependencies', 'owners', 'blockers',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']
