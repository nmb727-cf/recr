from rest_framework import serializers
from apps.agency_candidates.models import (
    AgencyCandidatePipelineRegistry,
    AgencyCandidate,
    AgencyCandidateTag,
    AgencyCandidateNote,
    AgencyCandidateActivity,
    AgencyCandidateOwnership,
    AgencyCandidateHotlist,
    AgencyCandidateHotlistMember,
    AgencyCandidateResumeVersion,
    AgencyCandidateSubmission
)
from apps.candidates.serializers import CandidateSerializer


class AgencyCandidatePipelineRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyCandidatePipelineRegistry
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class AgencyCandidateTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyCandidateTag
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class AgencyCandidateNoteSerializer(serializers.ModelSerializer):
    creator_name = serializers.SerializerMethodField()

    class Meta:
        model = AgencyCandidateNote
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_creator_name(self, obj):
        # Assuming created_by is a UUID linking to a User
        # In a real scenario, you'd fetch the user name
        return "Recruiter" # Placeholder


class AgencyCandidateActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyCandidateActivity
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'actor_id']


class AgencyCandidateOwnershipSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = AgencyCandidateOwnership
        fields = '__all__'
        read_only_fields = ['id', 'started_at']

    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}".strip()


class AgencyCandidateResumeVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyCandidateResumeVersion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class AgencyCandidateSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyCandidateSubmission
        fields = '__all__'
        read_only_fields = ['id', 'submitted_at']


class AgencyCandidateSerializer(serializers.ModelSerializer):
    candidate_details = CandidateSerializer(source='candidate', read_only=True)
    pipeline_stage_label = serializers.CharField(source='pipeline_stage.stage_label', read_only=True)
    owner_name = serializers.SerializerMethodField()
    tags = AgencyCandidateTagSerializer(many=True, read_only=True)
    
    class Meta:
        model = AgencyCandidate
        fields = '__all__'
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def get_owner_name(self, obj):
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}".strip()
        return None


class AgencyCandidateHotlistSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = AgencyCandidateHotlist
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_member_count(self, obj):
        return obj.members.count()


class AgencyCandidateHotlistMemberSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='agency_candidate.candidate.full_name', read_only=True)

    class Meta:
        model = AgencyCandidateHotlistMember
        fields = '__all__'
        read_only_fields = ['id', 'added_at']
