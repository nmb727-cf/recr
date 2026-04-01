from rest_framework import serializers
from apps.jobs.models import JobRequisition, JobPosting, JobStage, JobHiringTeamMember


class JobStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobStage
        fields = [
            'id', 'tenant_id', 'requisition_id', 'name', 'stage_order',
            'stage_type', 'stage_zone', 'movement_restriction',
            'is_mandatory', 'is_critical_path', 
            'action_deadline_hours', 'sla_target_hours', 'auto_actions',
            'is_active', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'requisition_id', 'created_at', 'updated_at']


class JobHiringTeamMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = JobHiringTeamMember
        fields = ['id', 'user_id', 'user_name', 'role', 'metadata']

    def get_user_name(self, obj):
        from apps.accounts.models import CustomUser
        user = CustomUser.objects.filter(id=obj.user_id).first()
        if user:
            return f"{user.first_name} {user.last_name}".strip() or user.email
        return None


class JobRequisitionSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    job_owner_name = serializers.SerializerMethodField()
    hiring_manager_name = serializers.SerializerMethodField()
    recruiter_name = serializers.SerializerMethodField()
    backup_recruiter_name = serializers.SerializerMethodField()
    coordinator_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    hiring_team = JobHiringTeamMemberSerializer(many=True, read_only=True)

    class Meta:
        model = JobRequisition
        fields = [
            'id', 'job_ref_id', 'tenant_id', 'title', 'department_id', 'department_name',
            'location_id', 'location_name', 'job_category',
            'job_type', 'work_mode', 'experience_min', 'experience_max',
            'salary_min', 'salary_max', 'salary_currency', 'salary_visible',
            'headcount', 'priority', 'is_confidential',
            'job_owner_id', 'job_owner_name',
            'hiring_manager_id', 'hiring_manager_name',
            'recruiter_id', 'recruiter_name',
            'backup_recruiter_id', 'backup_recruiter_name',
            'coordinator_id', 'coordinator_name',
            'hiring_team',
            'sourcing_mode', 'agency_submission_governance', 'is_published_to_agencies',
            'description', 'requirements', 'responsibilities',
            'skills_required', 'status', 'approval_chain',
            'hiring_status', 'guarantee_watch_until',
            'current_approver_id', 'approved_at', 'approved_by',
            'target_date', 'closed_at', 'closed_reason',
            'source',
            'override_workflow_mode',
            'auto_match_candidates',
            'auto_assign_recruiter',
            'recruiter_assignment_policy',
            'auto_distribute_to_agencies',
            'agency_distribution_policy',
            'auto_schedule_interviews',
            'sla_automation_enabled',
            'auto_push_to_recruiter_queue',
            'auto_followup_after_source',
            'auto_nurture_unqualified_candidates',
            'budget_code',
            'offer_salary_default', 'offer_currency_default', 'auto_close_on_fulfillment',
            'agency_commission_model', 'agency_commission_percentage',
            'agency_commission_fixed_fee', 'agency_payment_terms_days',
            'created_at', 'updated_at', 'created_by', 'created_by_name', 'metadata',
        ]
        read_only_fields = [
            'id', 'job_ref_id', 'tenant_id', 'created_at', 'updated_at',
            'approved_at', 'approved_by', 'closed_at',
        ]

    def get_department_name(self, obj):
        if not obj.department_id: return None
        from apps.organisations.models import Department
        dept = Department.objects.filter(id=obj.department_id).values_list('name', flat=True).first()
        return dept

    def get_location_name(self, obj):
        if not obj.location_id: return None
        from apps.organisations.models import Location
        loc = Location.objects.filter(id=obj.location_id).values_list('name', flat=True).first()
        return loc

    def get_job_owner_name(self, obj):
        if not obj.job_owner_id: return None
        from apps.accounts.models import CustomUser
        user = CustomUser.objects.filter(id=obj.job_owner_id).first()
        if user:
            return f"{user.first_name} {user.last_name}".strip() or user.email
        return None

    def get_hiring_manager_name(self, obj):
        if not obj.hiring_manager_id: return None
        from apps.accounts.models import CustomUser
        user = CustomUser.objects.filter(id=obj.hiring_manager_id).first()
        if user:
            return f"{user.first_name} {user.last_name}".strip() or user.email
        return None

    def get_recruiter_name(self, obj):
        if not obj.recruiter_id: return None
        from apps.accounts.models import CustomUser
        user = CustomUser.objects.filter(id=obj.recruiter_id).first()
        if user:
            return f"{user.first_name} {user.last_name}".strip() or user.email
        return None

    def get_backup_recruiter_name(self, obj):
        if not obj.backup_recruiter_id: return None
        from apps.accounts.models import CustomUser
        user = CustomUser.objects.filter(id=obj.backup_recruiter_id).first()
        if user:
            return f"{user.first_name} {user.last_name}".strip() or user.email
        return None

    def get_coordinator_name(self, obj):
        if not obj.coordinator_id: return None
        from apps.accounts.models import CustomUser
        user = CustomUser.objects.filter(id=obj.coordinator_id).first()
        if user:
            return f"{user.first_name} {user.last_name}".strip() or user.email
        return None

    def get_created_by_name(self, obj):
        if not obj.created_by: return None
        from apps.accounts.models import CustomUser
        user = CustomUser.objects.filter(id=obj.created_by).first()
        if user:
            return f"{user.first_name} {user.last_name}".strip() or user.email
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Determine if the user is internal (staff/management)
        is_internal = False
        if request and request.user and request.user.is_authenticated:
            internal_roles = [
                'super_admin', 'tenant_admin', 'hr_manager', 
                'hiring_manager', 'recruiter', 'interviewer',
                'agency_owner', 'agency_admin', 'agency_recruiter'
            ]
            if request.user.role in internal_roles or request.user.is_staff:
                is_internal = True

        if not is_internal:
            # Redact Salary if not marked as visible
            if not instance.salary_visible:
                data['salary_min'] = None
                data['salary_max'] = None
            
            # Redact internal-only fields
            internal_only_fields = [
                'approval_chain', 'current_approver_id', 'approved_at', 
                'approved_by', 'source', 'budget_code', 'metadata', 
                'created_by', 'created_by_name', 'guarantee_watch_until', 'hiring_status',
                'headcount', 'auto_match_candidates', 
                'job_owner_id', 'job_owner_name',
                'hiring_manager_id', 'hiring_manager_name',
                'recruiter_id', 'recruiter_name',
                'backup_recruiter_id', 'backup_recruiter_name',
                'coordinator_id', 'coordinator_name',
                'hiring_team',
                'sourcing_mode', 'agency_submission_governance', 'is_published_to_agencies',
                'auto_match_candidates', 'auto_assign_recruiter', 'recruiter_assignment_policy',
                'auto_distribute_to_agencies', 'agency_distribution_policy',
                'auto_schedule_interviews', 'sla_automation_enabled',
                'auto_push_to_recruiter_queue', 'auto_followup_after_source',
                'auto_nurture_unqualified_candidates', 'override_workflow_mode',
                'offer_salary_default', 'offer_currency_default', 'auto_close_on_fulfillment',
                'agency_commission_model', 'agency_commission_percentage',
                'agency_commission_fixed_fee', 'agency_payment_terms_days'
            ]
            for field in internal_only_fields:
                if field in data:
                    data.pop(field)

            # Handle Confidentiality
            if instance.is_confidential:
                data['description'] = "Details for this confidential role will be shared during the interview process."
                data['requirements'] = "Redacted for confidentiality."
                data['responsibilities'] = "Redacted for confidentiality."
                data['skills_required'] = []
                
        return data


class JobPostingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPosting
        fields = [
            'id', 'tenant_id', 'requisition_id', 'title', 'slug',
            'description_html', 'requirements', 'responsibilities',
            'skills_required', 'external_description',
            'posted_at', 'expires_at', 'is_active',
            'views_count', 'applications_count',
            'posted_on', 'custom_application_form',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'requisition_id', 'slug',
            'views_count', 'applications_count',
            'posted_at', 'created_at', 'updated_at',
        ]
