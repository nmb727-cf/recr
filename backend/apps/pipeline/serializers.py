from rest_framework import serializers
from apps.pipeline.models import Application, ApplicationStageHistory, ActionDeadline


class ApplicationStageHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStageHistory
        fields = [
            'id', 'application_id', 'from_stage_id', 'to_stage_id',
            'from_status', 'to_status', 'moved_by', 'reason', 'notes', 'moved_at',
        ]
        read_only_fields = ['id', 'moved_at']


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            'id', 'tenant_id', 'candidate_id', 'requisition_id',
            'current_stage_id', 'status', 'source', 'source_detail',
            'submitted_by', 'submitted_by_tenant_id',
            'agency_id', 'is_agency_submission', 'match_score',
            'rejection_reason', 'rejection_category', 'withdrawn_reason',
            'offer_amount', 'offer_currency', 'offer_date',
            'offer_accepted_at', 'offer_rejected_at',
            'joining_date', 'joined_at',
            'application_form_data',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'created_at', 'updated_at',
            'offer_accepted_at', 'offer_rejected_at', 'joined_at',
        ]


class ActionDeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionDeadline
        fields = [
            'id', 'tenant_id', 'entity_type', 'entity_id',
            'action_required', 'assigned_to', 'escalate_to',
            'deadline_at', 'reminder_sent_at', 'escalated_at',
            'completed_at', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'created_at', 'updated_at',
            'reminder_sent_at', 'escalated_at',
        ]
