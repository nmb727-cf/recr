from rest_framework import serializers
from apps.prequalification.models import (
    PrequalForm, PrequalSection, PrequalQuestion, PrequalRule, PrequalResponse,
)


class PrequalRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrequalRule
        fields = [
            'id', 'condition_type', 'compare_value',
            'action_type', 'outcome_code',
            'target_question_id', 'target_section_id',
            'created_at', 'metadata',
        ]
        read_only_fields = ['id', 'created_at']


class PrequalQuestionSerializer(serializers.ModelSerializer):
    rules = PrequalRuleSerializer(many=True, read_only=True)

    class Meta:
        model = PrequalQuestion
        fields = [
            'id', 'section', 'question_text', 'question_type',
            'required', 'order', 'help_text', 'options_json',
            'score_weight', 'is_knockout',
            'rules', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PrequalSectionSerializer(serializers.ModelSerializer):
    questions = PrequalQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = PrequalSection
        fields = [
            'id', 'form', 'title', 'description', 'order',
            'questions', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PrequalFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrequalForm
        fields = [
            'id', 'name', 'description', 'is_active',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class PrequalFormDetailSerializer(serializers.ModelSerializer):
    sections = PrequalSectionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = PrequalForm
        fields = [
            'id', 'name', 'description', 'is_active',
            'sections', 'question_count',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_question_count(self, obj):
        return PrequalQuestion.objects.filter(section__form=obj).count()


class PrequalResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrequalResponse
        fields = [
            'id', 'form', 'candidate_id', 'question',
            'answer_text', 'answer_json',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
