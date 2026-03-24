from rest_framework import serializers
from apps.candidates.models import Candidate, CandidateProfile, CandidateNote


class CandidateNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateNote
        fields = [
            'id', 'tenant_id', 'candidate_id', 'note_text', 'note_type',
            'is_private', 'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'candidate_id', 'created_at', 'updated_at', 'created_by']


class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'candidate_id', 'summary', 'work_experience', 'education',
            'certifications', 'projects', 'publications', 'awards', 'references',
            'cv_url', 'cv_parsed_data', 'cv_uploaded_at',
            'portfolio_url', 'github_url', 'stackoverflow_url',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'candidate_id', 'created_at', 'updated_at']


class CandidateSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Candidate
        fields = [
            'id', 'tenant_id', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'whatsapp', 'linkedin_url',
            'current_title', 'current_company',
            'current_location_city', 'current_location_country',
            'experience_years', 'expected_salary_min', 'expected_salary_max',
            'salary_currency', 'notice_period_days', 'availability_date',
            'designation', 'relevant_experience_years',
            'current_ctc', 'current_ctc_currency',
            'offer_in_hand', 'offer_in_hand_amount', 'counter_offer',
            'availability_status', 'last_working_day', 'work_mode_preference',
            'fitment_score', 'profile_status', 'initial_entry_type',
            'account_status', 'invite_sent_at', 'claimed_at',
            'is_actively_looking', 'source', 'source_detail',
            'passport_id', 'is_duplicate', 'duplicate_of',
            'tags', 'skills', 'languages',
            'assigned_to', 'owner_user_id', 'owner_tenant_id',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'created_at', 'updated_at',
            'global_hash', 'is_duplicate', 'duplicate_of',
        ]


class CandidateDetailSerializer(CandidateSerializer):
    profile = serializers.SerializerMethodField()
    notes_count = serializers.SerializerMethodField()

    class Meta(CandidateSerializer.Meta):
        fields = CandidateSerializer.Meta.fields + ['profile', 'notes_count']

    def get_profile(self, obj):
        try:
            profile = CandidateProfile.objects.get(candidate_id=obj.id)
            return CandidateProfileSerializer(profile).data
        except CandidateProfile.DoesNotExist:
            return None

    def get_notes_count(self, obj):
        return CandidateNote.objects.filter(
            candidate_id=obj.id, is_deleted=False
        ).count()


from .models import CandidateWorkspace, CandidateEngagement, CandidateTimelineEvent


class CandidateWorkspaceSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = CandidateWorkspace
        fields = [
            'id', 'tenant_id', 'candidate', 'owner_user', 'owner_name',
            'priority', 'relationship_status', 'tags', 'local_rating',
            'source_for_tenant', 'talent_pool_ids', 'last_worked_at',
            'custom_fields', 'created_at', 'updated_at', 'metadata'
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']

    def get_owner_name(self, obj):
        if obj.owner_user:
            return f"{obj.owner_user.first_name} {obj.owner_user.last_name}".strip()
        return None


class CandidateEngagementSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
    is_follow_up_overdue = serializers.SerializerMethodField()

    class Meta:
        model = CandidateEngagement
        fields = [
            'id', 'tenant_id', 'candidate', 'candidate_name',
            'workspace', 'job', 'job_title',
            'engagement_type', 'stage', 'priority', 'is_active',
            'owner_user', 'owner_name', 'source_channel',
            'follow_up_at', 'is_follow_up_overdue',
            'last_activity_at', 'resurrected_from',
            'closure_reason', 'started_at', 'closed_at',
            'created_at', 'updated_at', 'metadata'
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at', 'started_at']

    def get_candidate_name(self, obj):
        return f"{obj.candidate.first_name} {obj.candidate.last_name}".strip()

    def get_owner_name(self, obj):
        if obj.owner_user:
            return f"{obj.owner_user.first_name} {obj.owner_user.last_name}".strip()
        return None

    def get_job_title(self, obj):
        if obj.job:
            return obj.job.title
        return None

    def get_is_follow_up_overdue(self, obj):
        if obj.follow_up_at:
            from django.utils import timezone
            return obj.follow_up_at < timezone.now()
        return False


class CandidateTimelineEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = CandidateTimelineEvent
        fields = [
            'id', 'tenant_id', 'candidate', 'engagement',
            'event_type', 'actor', 'actor_name',
            'payload', 'source', 'created_at'
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at']

    def get_actor_name(self, obj):
        if obj.actor:
            return f"{obj.actor.first_name} {obj.actor.last_name}".strip()
        return 'System'

