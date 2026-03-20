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
