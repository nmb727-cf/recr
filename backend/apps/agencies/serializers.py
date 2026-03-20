from rest_framework import serializers
from apps.agencies.models import AgencyClientRelationship, AgencyJobAssignment, AgencyPerformanceScore


class AgencyClientRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyClientRelationship
        fields = [
            'id', 'tenant_id', 'agency_tenant_id', 'company_tenant_id',
            'status', 'tier', 'contract_start_date', 'contract_end_date',
            'sla_submission_hours', 'sla_feedback_hours',
            'commission_percentage', 'commission_type', 'notes',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class AgencyJobAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyJobAssignment
        fields = [
            'id', 'tenant_id', 'requisition_id', 'agency_tenant_id',
            'assigned_by', 'deadline', 'max_submissions', 'submission_count',
            'status', 'notes', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at', 'submission_count']


class AgencyPerformanceScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyPerformanceScore
        fields = [
            'id', 'tenant_id', 'agency_tenant_id', 'company_tenant_id',
            'period_start', 'period_end',
            'total_submissions', 'shortlisted_count', 'interviewed_count',
            'offered_count', 'joined_count',
            'shortlist_rate', 'offer_rate', 'join_rate',
            'avg_submission_time_hours', 'overall_score',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']
