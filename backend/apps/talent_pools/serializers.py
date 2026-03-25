from rest_framework import serializers
from .models import TalentPool, CandidateTalentPoolMembership
from apps.candidates.models import Candidate

class CandidateBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone', 
            'current_title', 'current_location_city', 'experience_years'
        ]

class TalentPoolSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = TalentPool
        fields = [
            'id', 'tenant_id', 'tenant_type', 'name', 'slug', 'description',
            'pool_type', 'color', 'is_active', 'created_by', 'created_at',
            'updated_at', 'filters_json', 'metadata', 'member_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'member_count']

    def create(self, validated_data):
        if not validated_data.get('slug'):
            from django.utils.text import slugify
            validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)

class CandidateTalentPoolMembershipSerializer(serializers.ModelSerializer):
    candidate_details = CandidateBriefSerializer(source='candidate', read_only=True)
    
    class Meta:
        model = CandidateTalentPoolMembership
        fields = [
            'id', 'tenant_id', 'talent_pool', 'candidate', 'candidate_details',
            'added_by', 'added_at', 'source', 'note'
        ]
        read_only_fields = ['id', 'added_at', 'candidate_details']

class BulkAddCandidateSerializer(serializers.Serializer):
    candidate_ids = serializers.ListField(child=serializers.UUIDField())
    note = serializers.CharField(required=False, allow_blank=True)
    source = serializers.ChoiceField(choices=CandidateTalentPoolMembership.SOURCE_CHOICES, default='manual')
