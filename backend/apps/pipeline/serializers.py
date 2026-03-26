from rest_framework import serializers
from apps.candidates.protection import protection_badge_payload
from apps.pipeline.models import (
    Application, ApplicationStageHistory, ActionDeadline, PlacementGuarantee,
    Placement, CommissionRecord, CommissionReminder,
)


class ApplicationStageHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStageHistory
        fields = [
            'id', 'application_id', 'from_stage_id', 'to_stage_id',
            'from_status', 'to_status', 'moved_by', 'reason', 'notes', 'moved_at',
        ]
        read_only_fields = ['id', 'moved_at']


class ApplicationSerializer(serializers.ModelSerializer):
    is_under_guarantee = serializers.SerializerMethodField()
    guarantee_end_date = serializers.SerializerMethodField()
    guarantee_start_date = serializers.SerializerMethodField()
    guarantee_status = serializers.SerializerMethodField()
    guarantee_resolution_type = serializers.SerializerMethodField()
    refund_mode = serializers.SerializerMethodField()
    refund_percentage = serializers.SerializerMethodField()
    replacement_attempt_limit = serializers.SerializerMethodField()
    is_agency_protected = serializers.SerializerMethodField()
    protected_until = serializers.SerializerMethodField()
    protection_scope = serializers.SerializerMethodField()

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
            'is_under_guarantee', 'guarantee_end_date', 'guarantee_start_date',
            'guarantee_status', 'guarantee_resolution_type', 'refund_mode',
            'refund_percentage', 'replacement_attempt_limit',
            'is_agency_protected', 'protected_until', 'protection_scope',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'created_at', 'updated_at',
            'offer_accepted_at', 'offer_rejected_at', 'joined_at',
        ]

    def get_is_under_guarantee(self, obj):
        return PlacementGuarantee.objects.filter(
            application_id=obj.id,
            status__in=['active', 'breached', 'replacement_requested', 'refund_requested'],
        ).exists()

    def _latest_guarantee(self, obj):
        return PlacementGuarantee.objects.filter(application_id=obj.id).order_by('-created_at').first()

    def get_guarantee_end_date(self, obj):
        guarantee = self._latest_guarantee(obj)
        return guarantee.guarantee_end_date if guarantee else None

    def get_guarantee_start_date(self, obj):
        guarantee = self._latest_guarantee(obj)
        return guarantee.guarantee_start_date if guarantee else None

    def get_guarantee_status(self, obj):
        guarantee = self._latest_guarantee(obj)
        return guarantee.status if guarantee else None

    def get_guarantee_resolution_type(self, obj):
        guarantee = self._latest_guarantee(obj)
        return guarantee.guarantee_resolution_type if guarantee else None

    def get_refund_mode(self, obj):
        guarantee = self._latest_guarantee(obj)
        return guarantee.refund_mode if guarantee else None

    def get_refund_percentage(self, obj):
        guarantee = self._latest_guarantee(obj)
        return guarantee.refund_percentage if guarantee else None

    def get_replacement_attempt_limit(self, obj):
        guarantee = self._latest_guarantee(obj)
        return guarantee.replacement_attempt_limit if guarantee else None

    def get_is_agency_protected(self, obj):
        return protection_badge_payload(
            candidate_id=obj.candidate_id,
            target_tenant_id=obj.tenant_id,
        ).get('is_agency_protected', False)

    def get_protected_until(self, obj):
        return protection_badge_payload(
            candidate_id=obj.candidate_id,
            target_tenant_id=obj.tenant_id,
        ).get('protected_until')

    def get_protection_scope(self, obj):
        return protection_badge_payload(
            candidate_id=obj.candidate_id,
            target_tenant_id=obj.tenant_id,
        ).get('protection_scope')


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


class PlacementGuaranteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlacementGuarantee
        fields = [
            'id', 'application_id', 'candidate_id', 'requisition_id',
            'agency_tenant_id', 'company_tenant_id', 'agency_relationship_id',
            'guarantee_start_date', 'guarantee_end_date',
            'guarantee_resolution_type', 'refund_mode', 'refund_percentage',
            'replacement_attempt_limit', 'current_attempt_count',
            'status', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Placement
        fields = [
            'id', 'tenant_id', 'application_id', 'candidate_id', 'requisition_id',
            'agency_id', 'agency_relationship_id',
            'placement_status',
            'offer_accepted_at', 'joining_date', 'joined_at', 'placement_confirmed_at',
            'credited_recruiter_id', 'notes',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'application_id', 'candidate_id', 'requisition_id',
            'agency_id', 'agency_relationship_id', 'created_at', 'updated_at',
        ]


class CommissionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionRecord
        fields = [
            'id', 'placement_id', 'application_id', 'requisition_id',
            'company_tenant_id', 'agency_tenant_id', 'agency_relationship_id',
            'commission_applicable', 'commission_model', 'basis_source',
            'commission_rate', 'commission_fixed_amount', 'expected_amount', 'currency',
            'payment_status', 'due_date', 'paid_date', 'paid_amount', 'payment_notes',
            'reminder_count', 'last_reminder_at',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = [
            'id', 'placement_id', 'application_id', 'requisition_id',
            'company_tenant_id', 'agency_tenant_id', 'agency_relationship_id',
            'reminder_count', 'last_reminder_at', 'created_at', 'updated_at',
        ]


class CommissionReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionReminder
        fields = [
            'id', 'commission_record_id', 'reminder_type', 'channel',
            'sent_by', 'sent_at', 'note', 'outcome', 'metadata',
        ]
        read_only_fields = ['id', 'sent_at', 'sent_by']
