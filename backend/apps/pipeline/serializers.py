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


class CandidateApplicationStageHistorySerializer(serializers.ModelSerializer):
    """Candidate-facing stage history — omits internal recruiter fields."""
    class Meta:
        model = ApplicationStageHistory
        fields = [
            'id', 'application_id', 'from_status', 'to_status', 'moved_at',
        ]
        read_only_fields = ['id', 'moved_at']


class ApplicationSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    candidate_email = serializers.SerializerMethodField()
    candidate_phone = serializers.SerializerMethodField()
    candidate_title = serializers.SerializerMethodField()
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
            'id', 'tenant_id', 'candidate_id', 'candidate_name', 'candidate_email',
            'candidate_phone', 'candidate_title', 'requisition_id',
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

    def get_candidate_name(self, obj):
        from apps.candidates.models import Candidate
        candidate = Candidate.objects.filter(id=obj.candidate_id).first()
        return candidate.full_name if candidate else None

    def get_candidate_email(self, obj):
        from apps.candidates.models import Candidate
        candidate = Candidate.objects.filter(id=obj.candidate_id).first()
        return candidate.email if candidate else None

    def get_candidate_phone(self, obj):
        from apps.candidates.models import Candidate
        candidate = Candidate.objects.filter(id=obj.candidate_id).first()
        return candidate.phone if candidate else None

    def get_candidate_title(self, obj):
        from apps.candidates.models import Candidate
        candidate = Candidate.objects.filter(id=obj.candidate_id).first()
        return candidate.current_title if candidate else None

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


class CandidateApplicationSerializer(serializers.ModelSerializer):
    """
    Candidate-facing application serializer.
    Exposes only candidate-appropriate fields — no internal recruiter data.
    """
    job_title = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    current_stage_name = serializers.SerializerMethodField()
    next_step_guidance = serializers.SerializerMethodField()
    expected_timeline = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'id', 'requisition_id', 'job_title', 'company_name',
            'current_stage_id', 'current_stage_name',
            'status', 'source',
            'offer_date', 'joining_date',
            'next_step_guidance', 'expected_timeline',
            'application_form_data',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_job_title(self, obj):
        from apps.jobs.models import JobRequisition
        req = JobRequisition.objects.filter(id=obj.requisition_id).first()
        return req.title if req else None

    def get_company_name(self, obj):
        from apps.organisations.models import Organisation
        org = Organisation.objects.filter(tenant_id=obj.tenant_id).first()
        return org.name if org else None

    def get_current_stage_name(self, obj):
        from apps.jobs.models import JobStage
        stage = JobStage.objects.filter(id=obj.current_stage_id).first()
        if stage:
            return stage.name
        return "Application Submitted"

    def get_next_step_guidance(self, obj):
        if obj.status == 'rejected':
            return "Application not proceeding at this time."
        if obj.status == 'joined':
            return "Hired! Welcome aboard."
        
        from apps.jobs.models import JobStage
        stage = JobStage.objects.filter(id=obj.current_stage_id).first()
        if not stage:
            return "Our team is reviewing your application."
            
        # Dynamic guidance based on stage type
        guidance_map = {
            'sourcing': "Your profile is being reviewed for alignment.",
            'screening': "A recruiter will contact you for a brief screening.",
            'interview': "Interview scheduling is in progress.",
            'assessment': "Please complete the assigned assessments.",
            'offer': "Your offer is being prepared.",
        }
        return guidance_map.get(stage.stage_type, "Wait for the next update from our hiring team.")

    def get_expected_timeline(self, obj):
        if obj.status in ('rejected', 'joined', 'withdrawn'):
            return "Process concluded."
            
        from apps.jobs.models import JobStage
        stage = JobStage.objects.filter(id=obj.current_stage_id).first()
        hours = stage.action_deadline_hours if stage else 48
        return f"Expect an update within {max(24, hours // 24 * 24)} hours."


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
