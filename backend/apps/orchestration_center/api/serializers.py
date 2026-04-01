from rest_framework import serializers

from apps.orchestration_center.constants.execution_statuses import (
    ApprovalMode,
    ApprovalStatus,
    AutomationRuleStatus,
    ConfidenceBand,
    DeadLetterStatus,
    FailureStatus,
    PromptStatus,
    SuggestionCategory,
    SuggestionStatus,
)
from apps.orchestration_center.models import (
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
    DeadLetterItem,
    ExecutionFailure,
    IntelligenceConnector,
    ModelRoutingRule,
    PromptScope,
    PromptTemplate,
    PromptTestRun,
    PromptVersion,
    ProviderConfig,
    TenantIntelligenceSettings,
)


HIGH_RISK_ACTION_TYPES = {'move_stage', 'reject_candidate', 'send_rejection_email'}


class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')


class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')


class ProviderConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderConfig
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')


class ModelRoutingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelRoutingRule
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')


class PromptVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptVersion
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'approved_by_id', 'approved_at')

    def validate(self, attrs):
        template = attrs.get('prompt_template') or getattr(self.instance, 'prompt_template', None)
        status_value = attrs.get('status') or getattr(self.instance, 'status', PromptStatus.DRAFT)
        approval_required = attrs.get(
            'approval_required',
            getattr(self.instance, 'approval_required', getattr(template, 'approval_required', True)),
        )
        approved_by_id = attrs.get('approved_by_id', getattr(self.instance, 'approved_by_id', None))

        if status_value == PromptStatus.ACTIVE and not template:
            raise serializers.ValidationError('Prompt template is required before activation.')
        if status_value == PromptStatus.ACTIVE and approval_required and not approved_by_id:
            raise serializers.ValidationError('Approved prompt version is required before activation.')
        return attrs


class PromptVersionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptVersion
        exclude = ('tenant_id', 'created_by', 'updated_at', 'created_at', 'is_deleted', 'deleted_at', 'metadata')

    def validate(self, attrs):
        status_value = attrs.get('status', PromptStatus.DRAFT)
        if status_value == PromptStatus.ACTIVE:
            raise serializers.ValidationError({'status': 'Prompt versions cannot be created directly as active.'})
        return attrs


class PromptScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptScope
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'prompt_template')


class PromptTemplateSerializer(serializers.ModelSerializer):
    versions = PromptVersionSerializer(many=True, read_only=True)
    scopes = PromptScopeSerializer(many=True, read_only=True)

    class Meta:
        model = PromptTemplate
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'active_version_id')

    def validate(self, attrs):
        module_scope = attrs.get('module_scope') or getattr(self.instance, 'module_scope', '')
        use_case_key = attrs.get('use_case_key') or getattr(self.instance, 'use_case_key', '')
        prompt_key = attrs.get('prompt_key') or getattr(self.instance, 'prompt_key', '')
        if not prompt_key:
            raise serializers.ValidationError({'prompt_key': 'prompt_key is required.'})
        if not module_scope:
            raise serializers.ValidationError({'module_scope': 'module_scope is required.'})
        if not use_case_key:
            raise serializers.ValidationError({'use_case_key': 'use_case_key is required.'})
        return attrs


class PromptTemplateCreateSerializer(PromptTemplateSerializer):
    scopes = PromptScopeSerializer(many=True, required=False, write_only=True)
    initial_version = PromptVersionCreateSerializer(required=False, write_only=True)

    class Meta(PromptTemplateSerializer.Meta):
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'active_version_id', 'status')


class PromptTemplateUpdateSerializer(PromptTemplateSerializer):
    scopes = PromptScopeSerializer(many=True, required=False, write_only=True)


class PromptApproveRequestSerializer(serializers.Serializer):
    version_id = serializers.UUIDField()
    activate = serializers.BooleanField(default=True)


class PromptTestRequestSerializer(serializers.Serializer):
    version_id = serializers.UUIDField()
    test_input_json = serializers.JSONField(required=False)


class PromptTestRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTestRun
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')


class AIExecutionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIExecutionResult
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')


class AIExecutionReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIExecutionReview
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')


class AIExecutionRequestSerializer(serializers.ModelSerializer):
    result = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()

    class Meta:
        model = AIExecutionRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def get_result(self, obj):
        if hasattr(obj, 'result'):
            return AIExecutionResultSerializer(obj.result).data
        return None

    def get_review(self, obj):
        if hasattr(obj, 'review'):
            return AIExecutionReviewSerializer(obj.review).data
        return None


class AISuggestionConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AISuggestionConversion
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')


class AISuggestionSerializer(serializers.ModelSerializer):
    ai_request = serializers.SerializerMethodField()
    approval_item = serializers.SerializerMethodField()
    conversions = AISuggestionConversionSerializer(many=True, read_only=True)

    class Meta:
        model = AISuggestion
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def get_ai_request(self, obj):
        if obj.ai_request_id:
            return AIExecutionRequestSerializer(obj.ai_request).data
        return None

    def get_approval_item(self, obj):
        if obj.approval_item_id:
            return ApprovalQueueItemSerializer(obj.approval_item).data
        return None


class AISuggestionCreateSerializer(serializers.Serializer):
    suggestion_key = serializers.CharField(max_length=64)
    category = serializers.ChoiceField(choices=SuggestionCategory.choices)
    source_event = serializers.CharField(max_length=128, required=False, allow_blank=True)
    source_module = serializers.CharField(max_length=64)
    source_entity_type = serializers.CharField(max_length=64)
    source_entity_id = serializers.CharField(max_length=64)
    owner_module = serializers.CharField(max_length=64, required=False, allow_blank=True)
    proposed_action_family = serializers.CharField(max_length=64, required=False, allow_blank=True)
    title = serializers.CharField(max_length=255)
    summary = serializers.CharField(required=False, allow_blank=True)
    confidence_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    confidence_band = serializers.ChoiceField(choices=ConfidenceBand.choices, required=False)
    payload_json = serializers.JSONField(required=False)
    rationale_json = serializers.JSONField(required=False)
    audit_metadata_json = serializers.JSONField(required=False)
    requires_approval = serializers.BooleanField(required=False, default=False)
    manual_override_allowed = serializers.BooleanField(required=False, default=True)
    idempotency_key = serializers.CharField(max_length=255, required=False, allow_blank=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    ai_request_id = serializers.UUIDField(required=False)

    def validate_confidence_score(self, value):
        if value < 0 or value > 1:
            raise serializers.ValidationError('confidence_score must be between 0.00 and 1.00.')
        return value


class AISuggestionReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[SuggestionStatus.PENDING_REVIEW, SuggestionStatus.REJECTED])
    comment = serializers.CharField(required=False, allow_blank=True)


class AISuggestionApproveSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)


class AISuggestionConvertSerializer(serializers.Serializer):
    conversion_type = serializers.CharField(max_length=64, default='approval_queue_item')
    idempotency_key = serializers.CharField(max_length=255, required=False, allow_blank=True)
    override_payload_json = serializers.JSONField(required=False)


class AutomationRuleConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationRuleCondition
        fields = (
            'id',
            'condition_group',
            'field_path',
            'operator',
            'expected_value_json',
            'sequence_order',
            'is_negated',
        )
        read_only_fields = ('id',)


class AutomationRuleActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationRuleAction
        fields = (
            'id',
            'action_type',
            'action_config_json',
            'delay_seconds',
            'requires_approval',
            'sequence_order',
        )
        read_only_fields = ('id',)


class AutomationRuleScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationRuleScope
        fields = (
            'id',
            'entity_type',
            'stage_key',
            'role_scope',
            'source_scope',
            'working_hours_only',
            'is_active',
        )
        read_only_fields = ('id',)


class AutomationRuleSerializer(serializers.ModelSerializer):
    conditions = AutomationRuleConditionSerializer(many=True, required=False)
    actions = AutomationRuleActionSerializer(many=True, required=False)
    scopes = AutomationRuleScopeSerializer(many=True, required=False)

    class Meta:
        model = AutomationRule
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def validate(self, attrs):
        mode = attrs.get('mode') or getattr(self.instance, 'mode', ApprovalMode.SUGGESTION_ONLY)
        status_value = attrs.get('status') or getattr(self.instance, 'status', AutomationRuleStatus.DRAFT)
        trigger_event = attrs.get('trigger_event') or getattr(self.instance, 'trigger_event', '')
        actions = attrs.get('actions')
        current_actions = list(self.instance.actions.all()) if self.instance else []

        if not trigger_event:
            raise serializers.ValidationError({'trigger_event': 'trigger_event is required.'})
        if actions is not None and len(actions) == 0:
            raise serializers.ValidationError({'actions': 'At least one action is required.'})
        if status_value in {AutomationRuleStatus.ACTIVE, AutomationRuleStatus.TESTING} and actions is None and not current_actions:
            raise serializers.ValidationError({'actions': 'Active or testing automation rules must have at least one action.'})

        action_payloads = actions
        if action_payloads is None:
            action_payloads = [
                {
                    'action_type': item.action_type,
                    'action_config_json': item.action_config_json,
                    'delay_seconds': item.delay_seconds,
                    'requires_approval': item.requires_approval,
                    'sequence_order': item.sequence_order,
                }
                for item in current_actions
            ]

        action_types = {item.get('action_type') for item in action_payloads}
        if action_types.intersection(HIGH_RISK_ACTION_TYPES) and mode != ApprovalMode.APPROVAL_REQUIRED:
            raise serializers.ValidationError({'mode': 'High-risk automation rules must use approval_required mode.'})
        return attrs


class AutomationToggleSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            AutomationRuleStatus.ACTIVE,
            AutomationRuleStatus.PAUSED,
            AutomationRuleStatus.INACTIVE,
            AutomationRuleStatus.TESTING,
        ]
    )


class AutomationSimulationSerializer(serializers.Serializer):
    event_payload_json = serializers.JSONField(required=False)


class AutomationExecutionRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationExecutionRun
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')


class ExecutionFailureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionFailure
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'resolved_by_id', 'resolved_at')

    def validate(self, attrs):
        retryable = attrs.get('retryable', getattr(self.instance, 'retryable', True))
        status_value = attrs.get('status', getattr(self.instance, 'status', FailureStatus.NEW))
        if status_value == FailureStatus.RETRYING and not retryable:
            raise serializers.ValidationError({'status': 'Non-retryable failures cannot move to retrying.'})
        return attrs


class FailureResolveRequestSerializer(serializers.Serializer):
    resolution_note = serializers.CharField(required=False, allow_blank=True)


class DeadLetterItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeadLetterItem
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def validate(self, attrs):
        status_value = attrs.get('status', getattr(self.instance, 'status', DeadLetterStatus.OPEN))
        if self.instance and self.instance.status == DeadLetterStatus.RESOLVED and status_value == DeadLetterStatus.REQUEUED:
            raise serializers.ValidationError({'status': 'Resolved dead-letter items cannot be requeued.'})
        return attrs


class ApprovalQueueItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalQueueItem
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
            'created_by',
            'status',
            'decided_by_id',
            'decided_at',
            'applied_by_id',
            'applied_at',
        )


class ApprovalDecisionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)
    apply_now = serializers.BooleanField(default=True)


class TenantIntelligenceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantIntelligenceSettings
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def validate(self, attrs):
        approval_mode = attrs.get(
            'default_approval_mode',
            getattr(self.instance, 'default_approval_mode', ApprovalMode.SUGGESTION_ONLY),
        )
        if approval_mode not in ApprovalMode.values:
            raise serializers.ValidationError({'default_approval_mode': 'Invalid approval mode.'})

        allowed_provider_ids = attrs.get(
            'allowed_provider_ids_json',
            getattr(self.instance, 'allowed_provider_ids_json', []),
        )
        if not isinstance(allowed_provider_ids, list):
            raise serializers.ValidationError({'allowed_provider_ids_json': 'allowed_provider_ids_json must be a list.'})

        feature_flags = attrs.get('feature_flags_json', getattr(self.instance, 'feature_flags_json', {}))
        if not isinstance(feature_flags, dict):
            raise serializers.ValidationError({'feature_flags_json': 'feature_flags_json must be an object.'})

        connector_enablement = attrs.get(
            'connector_enablement_json',
            getattr(self.instance, 'connector_enablement_json', {}),
        )
        if not isinstance(connector_enablement, dict):
            raise serializers.ValidationError({'connector_enablement_json': 'connector_enablement_json must be an object.'})
        return attrs


class IntelligenceConnectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntelligenceConnector
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')
