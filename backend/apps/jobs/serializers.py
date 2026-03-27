from rest_framework import serializers
from apps.jobs.models import JobRequisition, JobPosting, JobStage


class JobStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobStage
        fields = [
            'id', 'tenant_id', 'requisition_id', 'name', 'stage_order',
            'stage_type', 'action_deadline_hours', 'auto_actions',
            'is_active', 'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'requisition_id', 'created_at', 'updated_at']


class JobRequisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRequisition
        fields = [
            'id', 'tenant_id', 'title', 'department_id', 'location_id',
            'job_type', 'work_mode', 'experience_min', 'experience_max',
            'salary_min', 'salary_max', 'salary_currency', 'salary_visible',
            'headcount', 'priority', 'is_confidential',
            'description', 'requirements', 'responsibilities',
            'skills_required', 'status', 'approval_chain',
            'hiring_status', 'guarantee_watch_until',
            'current_approver_id', 'approved_at', 'approved_by',
            'target_date', 'closed_at', 'closed_reason',
            'source',
            'override_workflow_mode',
            'auto_match_candidates',
            'auto_push_to_recruiter_queue',
            'auto_followup_after_source',
            'auto_nurture_unqualified_candidates',
            'budget_code',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'created_at', 'updated_at',
            'approved_at', 'approved_by', 'closed_at',
        ]

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
                'created_by', 'guarantee_watch_until', 'hiring_status',
                'headcount', 'auto_match_candidates', 
                'auto_push_to_recruiter_queue', 'auto_followup_after_source',
                'auto_nurture_unqualified_candidates', 'override_workflow_mode'
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
            'description_html', 'external_description',
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
