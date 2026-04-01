from rest_framework import serializers
from apps.interviews.models import (
    InterviewType,
    InterviewTemplate,
    InterviewFlow,
    Interview,
    InterviewPanelist,
    InterviewFeedback,
    InterviewDecision,
    InterviewDecisionHistory,
    InterviewQuestion,
    InterviewScorecardTemplate,
    InterviewScorecardAttribute,
    InterviewAvailabilityProfile,
    InterviewAvailabilityBlock,
    InterviewSchedulingLink,
    InterviewCalendarConnection,
    InterviewIntegrationProvider,
    InterviewTenantProviderConnection,
    InterviewExecutionMapping,
    InterviewQuestionBank,
    InterviewQuestionAttachment,
    InterviewQuestionGroup,
    InterviewQuestionGroupItem,
    InterviewPackage,
    InterviewPackageBinding,
)


class InterviewTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewType
        fields = [
            'id', 'name', 'code', 'description',
            'execution_mode', 'configurable', 'type_configuration',
            'is_active', 'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InterviewTemplateSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()

    class Meta:
        model = InterviewTemplate
        fields = [
            'id', 'tenant_id', 'name', 'description',
            'interview_type', 'type', 'type_name',
            'duration_minutes', 'instructions', 'scoring_type',
            'passing_threshold', 'auto_shortlist_above', 'auto_reject_below',
            'anti_cheat_enabled', 'recording_enabled',
            'questions', 'scoring_criteria',
            'is_active', 'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']

    def get_type_name(self, obj):
        return obj.type.name if obj.type_id else None


class InterviewScorecardAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewScorecardAttribute
        fields = [
            'id', 'tenant_id', 'scorecard', 'attribute_name',
            'weight', 'rating_type', 'required', 'custom_scale',
            'order_index', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'scorecard', 'created_at', 'updated_at']


class InterviewScorecardTemplateSerializer(serializers.ModelSerializer):
    attributes = InterviewScorecardAttributeSerializer(many=True)

    class Meta:
        model = InterviewScorecardTemplate
        fields = [
            'id', 'tenant_id', 'name', 'description', 'interview_type',
            'attributes', 'is_active', 'created_at', 'updated_at',
            'created_by', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at', 'created_by']

    def create(self, validated_data):
        attrs = validated_data.pop('attributes', [])
        template = InterviewScorecardTemplate.objects.create(**validated_data)
        for index, attr in enumerate(attrs):
            order_index = attr.pop('order_index', index)
            InterviewScorecardAttribute.objects.create(
                tenant_id=template.tenant_id,
                scorecard=template,
                order_index=order_index,
                **attr,
            )
        return template

    def update(self, instance, validated_data):
        attrs = validated_data.pop('attributes', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if attrs is not None:
            instance.attributes.all().delete()
            for index, attr in enumerate(attrs):
                order_index = attr.pop('order_index', index)
                InterviewScorecardAttribute.objects.create(
                    tenant_id=instance.tenant_id,
                    scorecard=instance,
                    order_index=order_index,
                    **attr,
                )
        return instance


class InterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestion
        fields = [
            'id', 'tenant_id', 'interview_id', 'question_text', 'question_type',
            'options', 'expected_duration_seconds', 'candidate_answer',
            'candidate_video_url', 'ai_score', 'ai_feedback',
            'human_score', 'human_feedback', 'order_index',
            'answered_at', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'interview_id', 'created_at', 'updated_at']


class InterviewPanelistSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewPanelist
        fields = [
            'id', 'tenant_id', 'interview_id', 'interviewer_id', 'role',
            'score', 'feedback', 'recommendation', 'question_scores',
            'submitted_at', 'deadline_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'interview_id', 'created_at', 'updated_at']


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewFeedback
        fields = [
            'id', 'tenant_id', 'interview_id', 'panelist_id',
            'score', 'notes', 'recommendation', 'criteria_scores', 'scorecard_ratings',
            'submitted_at', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'interview_id', 'panelist_id', 'submitted_at', 'created_at', 'updated_at']

    def validate_recommendation(self, value):
        if value:
            valid = {'hire', 'reject', 'hold', 'next_round', 'manual_review', 'assignment', 'panel_required', 'escalate'}
            if value not in valid:
                raise serializers.ValidationError(
                    f"Must be one of: {', '.join(sorted(valid))}."
                )
        return value


class InterviewDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewDecision
        fields = [
            'id', 'tenant_id', 'interview_id',
            'decision', 'decision_source', 'decision_mode',
            'notes', 'previous_decision',
            'is_override', 'overridden_by', 'override_reason',
            'decided_by', 'decided_at',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'interview_id', 'decided_by', 'decided_at', 'created_at', 'updated_at']

    def validate_decision(self, value):
        valid = {'hire', 'reject', 'hold', 'next_round', 'manual_review', 'assignment', 'panel_required', 'escalate'}
        if value not in valid:
            raise serializers.ValidationError(
                f"Must be one of: {', '.join(sorted(valid))}."
            )
        return value


class InterviewDecisionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewDecisionHistory
        fields = [
            'id', 'tenant_id', 'interview_id', 'decision_id',
            'previous_decision', 'new_decision', 'changed_by',
            'change_source', 'is_override', 'override_reason',
            'metadata', 'changed_at',
        ]
        read_only_fields = fields


class InterviewFlowSerializer(serializers.ModelSerializer):
    stage_count = serializers.SerializerMethodField()

    class Meta:
        model = InterviewFlow
        fields = [
            'id', 'name', 'description', 'stages', 'stage_count',
            'is_active', 'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_stage_count(self, obj):
        return len(obj.stages) if isinstance(obj.stages, list) else 0


class InterviewSerializer(serializers.ModelSerializer):
    decision = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = [
            'id', 'tenant_id', 'application_id', 'candidate_id',
            'requisition_id', 'template_id', 'scorecard_template_id', 'interview_type',
            'interview_round', 'title', 'scheduled_at',
            'started_at', 'completed_at', 'duration_minutes',
            'status', 'execution_mode', 'execution_provider_code',
            'interview_link', 'meeting_link', 'meeting_provider_code', 'external_interview_link', 'recording_url',
            'overall_score', 'ai_score', 'human_score',
            'recommendation', 'feedback_summary',
            'anti_cheat_score', 'anti_cheat_flags',
            'is_cafe_interview', 'cafe_session_id',
            'decision',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'created_at', 'updated_at',
            'started_at', 'completed_at',
        ]

    def get_decision(self, obj):
        decision = InterviewDecision.objects.filter(interview_id=obj.id).first()
        return InterviewDecisionSerializer(decision).data if decision else None


class InterviewDetailSerializer(InterviewSerializer):
    """Extended serializer that embeds panelists, feedback, and questions inline."""
    panelists = serializers.SerializerMethodField()
    feedback  = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()

    class Meta(InterviewSerializer.Meta):
        fields = InterviewSerializer.Meta.fields + ['panelists', 'feedback', 'questions']

    def get_panelists(self, obj):
        qs = InterviewPanelist.objects.filter(interview_id=obj.id)
        return InterviewPanelistSerializer(qs, many=True).data

    def get_feedback(self, obj):
        qs = InterviewFeedback.objects.filter(interview_id=obj.id, is_deleted=False)
        return InterviewFeedbackSerializer(qs, many=True).data

    def get_questions(self, obj):
        qs = InterviewQuestion.objects.filter(interview_id=obj.id).order_by('order_index')
        return InterviewQuestionSerializer(qs, many=True).data


class InterviewAvailabilityProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewAvailabilityProfile
        fields = [
            'id', 'tenant_id', 'interviewer_id', 'mode', 'timezone', 'working_hours',
            'default_duration_minutes', 'default_buffer_minutes', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'interviewer_id', 'created_at', 'updated_at']


class InterviewAvailabilityBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewAvailabilityBlock
        fields = [
            'id', 'tenant_id', 'interviewer_id', 'starts_at', 'ends_at', 'reason',
            'source', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'interviewer_id', 'created_by', 'created_at', 'updated_at']


class InterviewSchedulingLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewSchedulingLink
        fields = [
            'id', 'tenant_id', 'interview_id', 'token', 'timezone', 'expires_at',
            'max_bookings', 'booking_count', 'is_active', 'last_selected_slot',
            'metadata', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'token', 'booking_count', 'last_selected_slot', 'created_by', 'created_at', 'updated_at']


class InterviewPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewPackage
        fields = [
            'id', 'tenant_id', 'title', 'description', 'is_active',
            'rounds', 'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at', 'created_by']


class InterviewPackageBindingSerializer(serializers.ModelSerializer):
    package_title = serializers.CharField(source='package.title', read_only=True)
    rounds_summary = serializers.JSONField(source='package.rounds', read_only=True)

    class Meta:
        model = InterviewPackageBinding
        fields = [
            'id', 'tenant_id', 'job_id', 'package', 'package_title',
            'rounds_summary', 'automation_enabled', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class InterviewCalendarConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewCalendarConnection
        fields = [
            'id', 'tenant_id', 'interviewer_id', 'provider', 'external_calendar_id',
            'account_email', 'is_active', 'sync_enabled', 'last_synced_at',
            'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'interviewer_id', 'last_synced_at', 'created_at', 'updated_at']


class InterviewIntegrationProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewIntegrationProvider
        fields = [
            'id', 'name', 'code', 'provider_type', 'is_active',
            'tenant_configurable', 'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InterviewTenantProviderConnectionSerializer(serializers.ModelSerializer):
    provider = InterviewIntegrationProviderSerializer(read_only=True)
    provider_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = InterviewTenantProviderConnection
        fields = [
            'id', 'tenant_id', 'provider', 'provider_id',
            'auth_data', 'config_data', 'is_enabled',
            'connection_status', 'last_validated_at',
            'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'last_validated_at', 'created_at', 'updated_at']


class InterviewExecutionMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewExecutionMapping
        fields = [
            'id', 'tenant_id', 'interview_type', 'stage_code',
            'execution_mode', 'provider_code', 'is_active',
            'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class InterviewQuestionBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestionBank
        fields = [
            'id', 'tenant_id', 'scope', 'question_title', 'description', 'question_type',
            'difficulty', 'tags', 'skills', 'options_json', 'expected_answer',
            'scoring_weight', 'is_active', 'created_by', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_by', 'created_at', 'updated_at']


class InterviewQuestionAttachmentSerializer(serializers.ModelSerializer):
    question = InterviewQuestionBankSerializer(read_only=True)
    question_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = InterviewQuestionAttachment
        fields = [
            'id', 'tenant_id', 'question', 'question_id', 'attach_type',
            'template_id', 'interview_type', 'assessment_ref',
            'is_active', 'order_index', 'created_by', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_by', 'created_at', 'updated_at']
        extra_kwargs = {
            'template_id': {'required': False, 'allow_null': True},
            'interview_type': {'required': False, 'allow_blank': True},
            'assessment_ref': {'required': False, 'allow_blank': True},
        }


class InterviewQuestionGroupItemSerializer(serializers.ModelSerializer):
    question = InterviewQuestionBankSerializer(read_only=True)
    question_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = InterviewQuestionGroupItem
        fields = [
            'id', 'group', 'question', 'question_id',
            'order_index', 'required', 'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'group', 'created_at', 'updated_at']


class InterviewQuestionGroupSerializer(serializers.ModelSerializer):
    items = InterviewQuestionGroupItemSerializer(many=True, required=False)

    class Meta:
        model = InterviewQuestionGroup
        fields = [
            'id', 'tenant_id', 'scope', 'name', 'description', 'section_name',
            'target_type', 'target_ref', 'order_index', 'is_active',
            'items', 'created_by', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        items = validated_data.pop('items', [])
        group = InterviewQuestionGroup.objects.create(**validated_data)
        for index, item in enumerate(items):
            qid = item.pop('question_id')
            question = InterviewQuestionBank.objects.filter(id=qid, is_deleted=False).first()
            if not question:
                continue
            InterviewQuestionGroupItem.objects.create(
                group=group,
                question=question,
                order_index=item.get('order_index', index),
                required=item.get('required', True),
                metadata=item.get('metadata', {}),
            )
        return group

    def update(self, instance, validated_data):
        items = validated_data.pop('items', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if items is not None:
            instance.items.all().delete()
            for index, item in enumerate(items):
                qid = item.pop('question_id')
                question = InterviewQuestionBank.objects.filter(id=qid, is_deleted=False).first()
                if not question:
                    continue
                InterviewQuestionGroupItem.objects.create(
                    group=instance,
                    question=question,
                    order_index=item.get('order_index', index),
                    required=item.get('required', True),
                    metadata=item.get('metadata', {}),
                )
        return instance
