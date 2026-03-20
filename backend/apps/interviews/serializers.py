from rest_framework import serializers
from apps.interviews.models import InterviewTemplate, Interview, InterviewPanelist, InterviewQuestion


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


class InterviewTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewTemplate
        fields = [
            'id', 'tenant_id', 'name', 'description', 'interview_type',
            'duration_minutes', 'instructions', 'passing_threshold',
            'auto_shortlist_above', 'auto_reject_below',
            'anti_cheat_enabled', 'recording_enabled',
            'questions', 'scoring_criteria', 'is_active',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = [
            'id', 'tenant_id', 'application_id', 'candidate_id',
            'requisition_id', 'template_id', 'interview_type',
            'interview_round', 'title', 'scheduled_at',
            'started_at', 'completed_at', 'duration_minutes',
            'status', 'interview_link', 'recording_url',
            'overall_score', 'ai_score', 'human_score',
            'recommendation', 'feedback_summary',
            'anti_cheat_score', 'anti_cheat_flags',
            'is_cafe_interview', 'cafe_session_id',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'created_at', 'updated_at',
            'started_at', 'completed_at',
        ]
