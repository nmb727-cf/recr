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
            'current_approver_id', 'approved_at', 'approved_by',
            'target_date', 'closed_at', 'closed_reason',
            'source', 'budget_code',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'created_at', 'updated_at',
            'approved_at', 'approved_by', 'closed_at',
        ]


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