from rest_framework import serializers
from apps.agencies.models import AgencyClientRelationship, AgencyJobAssignment, AgencyPerformanceScore
from apps.tenants.models import Client


class AgencyClientRelationshipSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    agency_name = serializers.SerializerMethodField()

    class Meta:
        model = AgencyClientRelationship
        fields = [
            'id', 'tenant_id', 'agency_tenant_id', 'company_tenant_id',
            'company_name', 'agency_name',
            'status', 'tier', 'contract_start_date', 'contract_end_date',
            'sla_submission_hours', 'sla_feedback_hours',
            'commission_percentage', 'commission_type', 'notes',
            'retention_enabled', 'retention_days', 'retention_start_type',
            'retention_scope', 'retention_post_expiry',
            'replacement_guarantee_enabled', 'guarantee_period_days',
            'guarantee_start_type', 'guarantee_resolution_type',
            'refund_mode', 'refund_percentage', 'replacement_attempt_limit',
            'guarantee_notes',
            'contact_person_name', 'contact_email', 'contact_phone',
            'contact_country_code', 'contact_phone_number',
            'industry', 'contract_file_url', 'recruitment_policy_url',
            'payment_terms', 'payment_schedule', 'connection_type',
            'guest_portal_id', 'email_tracking_id', 'their_ats_url',
            'invited_by', 'invited_via',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']

    def get_company_name(self, obj):
        try:
            from apps.organisations.models import Organisation
            org = Organisation.objects.filter(
                tenant_id=obj.company_tenant_id
            ).first()
            return org.name if org else 'Unknown Company'
        except Exception:
            return 'Unknown Company'

    def get_agency_name(self, obj):
        # For guest portals, agency_tenant_id is null
        # Return contact name or extract from metadata
        if not obj.agency_tenant_id:
            if obj.contact_person_name:
                return obj.contact_person_name
            meta_name = obj.metadata.get('agency_name') if obj.metadata else None
            if meta_name:
                return meta_name
            return obj.contact_email or 'Guest Portal'
        try:
            from apps.organisations.models import Organisation
            org = Organisation.objects.filter(
                tenant_id=obj.agency_tenant_id
            ).first()
            return org.name if org else 'Unknown Agency'
        except Exception:
            return 'Unknown Agency'


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
