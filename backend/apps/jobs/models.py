import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class JobRequisition(models.Model):
    WORKFLOW_MODE_CHOICES = [
        ('manual', 'Manual'),
        ('semi_automated', 'Semi Automated'),
        ('fully_automated', 'Fully Automated'),
    ]
    HIRING_STATUS_CHOICES = [
        ('active_hiring', 'Active Hiring'),
        ('hiring_complete', 'Hiring Complete'),
        ('in_guarantee_period', 'In Guarantee Period'),
        ('replacement_required', 'Replacement Required'),
        ('fully_closed', 'Fully Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_ref_id = models.CharField(max_length=32, blank=True, null=True, unique=True, db_index=True)
    tenant_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=255)
    
    department = models.ForeignKey(
        'organisations.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requisitions'
    )
    location = models.ForeignKey(
        'organisations.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_requisitions'
    )
    
    job_type = models.CharField(
        max_length=50,
        choices=[
            ('full_time', 'Full Time'), ('part_time', 'Part Time'),
            ('contract', 'Contract'), ('internship', 'Internship'),
            ('freelance', 'Freelance')
        ],
        default='full_time'
    )
    work_mode = models.CharField(
        max_length=50,
        choices=[
            ('onsite', 'Onsite'), ('remote', 'Remote'), ('hybrid', 'Hybrid')
        ],
        default='onsite'
    )
    experience_min = models.IntegerField(null=True, blank=True)
    experience_max = models.IntegerField(null=True, blank=True)
    salary_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='INR')
    salary_visible = models.BooleanField(default=False)
    headcount = models.IntegerField(default=1)
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'), ('medium', 'Medium'),
            ('high', 'High'), ('urgent', 'Urgent')
        ],
        default='medium'
    )
    is_confidential = models.BooleanField(default=False)
    
    job_owner = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='owned_jobs'
    )
    hiring_manager = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_jobs'
    )
    recruiter = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_jobs'
    )
    backup_recruiter = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backup_assigned_jobs'
    )
    coordinator = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coordinated_jobs'
    )
    
    job_category = models.CharField(max_length=100, blank=True)
    sourcing_mode = models.CharField(
        max_length=30,
        choices=[
            ('internal_only', 'Internal Only'),
            ('external_only', 'External Only'),
            ('hybrid', 'Hybrid')
        ],
        default='internal_only'
    )
    agency_submission_governance = models.CharField(
        max_length=30,
        choices=[
            ('direct', 'Direct Submission'),
            ('approval_required', 'Approval Required'),
            ('draft_only', 'Draft Submission')
        ],
        default='direct'
    )
    is_published_to_agencies = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    skills_required = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('draft', 'Draft'),
            ('pending_approval', 'Pending Approval'),
            ('approved', 'Approved'),
            ('active', 'Active'),
            ('paused', 'Paused'),
            ('in_guarantee_period', 'In Guarantee Period'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft'
    )
    hiring_status = models.CharField(
        max_length=40,
        choices=HIRING_STATUS_CHOICES,
        default='active_hiring',
        db_index=True,
    )
    guarantee_watch_until = models.DateTimeField(null=True, blank=True, db_index=True)
    approval_chain = models.JSONField(default=list, blank=True)
    current_approver_id = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.UUIDField(null=True, blank=True)
    # Prequalification binding
    prequal_enabled = models.BooleanField(default=False)
    prequal_form_id = models.UUIDField(null=True, blank=True, db_index=True)
    prequal_threshold_override = models.IntegerField(
        null=True, blank=True,
        help_text="Override the form's default pass threshold (0-100). Null = use form default."
    )
    prequal_pass_action = models.CharField(
        max_length=50,
        default='advance',
        choices=[
            ('advance', 'Advance to Next Stage'),
            ('manual_review', 'Flag for Manual Review'),
        ]
    )
    prequal_fail_action = models.CharField(
        max_length=50,
        default='reject',
        choices=[
            ('reject', 'Auto-Reject'),
            ('hold', 'Hold — Awaiting Review'),
            ('manual_review', 'Flag for Manual Review'),
        ]
    )
    target_date = models.DateField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_reason = models.CharField(max_length=255, blank=True)
    source = models.CharField(
        max_length=50,
        choices=[
            ('internal', 'Internal'), ('agency', 'Agency'),
            ('direct', 'Direct'), ('referral', 'Referral')
        ],
        blank=True
    )
    override_workflow_mode = models.CharField(
        max_length=30, choices=WORKFLOW_MODE_CHOICES, blank=True
    )
    auto_match_candidates = models.BooleanField(default=False)
    auto_assign_recruiter = models.BooleanField(default=False)
    recruiter_assignment_policy = models.CharField(
        max_length=50,
        choices=[
            ('round_robin', 'Round Robin'),
            ('workload_balanced', 'Workload Balanced'),
            ('performance_based', 'Performance Based'),
            ('manual', 'Manual')
        ],
        default='manual'
    )
    auto_distribute_to_agencies = models.BooleanField(default=False)
    agency_distribution_policy = models.CharField(
        max_length=50,
        choices=[
            ('all', 'All Preferred Agencies'),
            ('performance_ranked', 'Performance Ranked'),
            ('manual', 'Manual')
        ],
        default='manual'
    )
    auto_schedule_interviews = models.BooleanField(default=False)
    sla_automation_enabled = models.BooleanField(default=True)
    auto_push_to_recruiter_queue = models.BooleanField(default=False)
    auto_followup_after_source = models.BooleanField(default=False)
    auto_nurture_unqualified_candidates = models.BooleanField(default=False)
    budget_code = models.CharField(max_length=100, blank=True)
    # Offer & Closure Defaults
    offer_salary_default = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    offer_currency_default = models.CharField(max_length=10, default='INR')
    auto_close_on_headcount_met = models.BooleanField(default=True)
    hiring_complete_action = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Manual Only'),
            ('auto_onboarding', 'Trigger Onboarding Flow'),
            ('archive', 'Archive Application'),
        ],
        default='auto_onboarding'
    )
    # Agency Commercial Defaults (per job)
    agency_commission_model = models.CharField(
        max_length=30,
        choices=[
            ('percentage', 'Percentage of Salary'),
            ('fixed', 'Fixed Fee'),
            ('inherited', 'Inherited from Agency Relationship')
        ],
        default='inherited'
    )
    agency_commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    agency_commission_fixed_fee = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    agency_payment_terms_days = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)

    # Workflow Master Binding
    workflow_id = models.UUIDField(null=True, blank=True, db_index=True)
    workflow_template_id = models.UUIDField(null=True, blank=True, db_index=True)
    workflow_enabled = models.BooleanField(default=False)
    is_workflow_controlled = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if self.pk:
            old_ref = JobRequisition.objects.filter(pk=self.pk).values_list('job_ref_id', flat=True).first()
            if old_ref and self.job_ref_id != old_ref:
                raise ValidationError("job_ref_id is immutable once generated.")

        if self._state.adding and not self.job_ref_id:
            from apps.tenants.reference_ids import build_reference, job_type_code

            self.job_ref_id = build_reference(
                tenant_id=self.tenant_id,
                entity_type=job_type_code(self),
                created_at=self.created_at,
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'jobs_requisition'
        ordering = ['-created_at']


class JobPosting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    requisition_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description_html = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    skills_required = models.JSONField(default=list, blank=True)
    external_description = models.TextField(blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    views_count = models.IntegerField(default=0)
    applications_count = models.IntegerField(default=0)
    posted_on = models.JSONField(default=list, blank=True)
    custom_application_form = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'jobs_posting'
        ordering = ['-created_at']


class JobStage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    requisition_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=100)
    stage_order = models.IntegerField(default=0)
    stage_type = models.CharField(
        max_length=50,
        choices=[
            ('sourcing', 'Sourcing'),
            ('shortlisted', 'Shortlisted'),
            ('screening', 'Screening'),
            ('interview', 'Interview'),
            ('assessment', 'Assessment'),
            ('offer', 'Offer'),
            ('joined', 'Joined'),
            ('rejected', 'Rejected'),
            ('withdrawn', 'Withdrawn'),
        ],
        default='screening'
    )
    stage_zone = models.CharField(
        max_length=50,
        choices=[
            ('pre_submission', 'Pre-Submission'),
            ('submitted', 'Submitted'),
            ('hiring_flow', 'Hiring Flow'),
            ('closed', 'Closed'),
        ],
        default='hiring_flow'
    )
    movement_restriction = models.CharField(
        max_length=30,
        choices=[
            ('open', 'Open'),
            ('job_owner_only', 'Job Owner Only'),
            ('recruiter_only', 'Recruiter Only'),
            ('automation_only', 'Automation Only'),
        ],
        default='open'
    )
    is_mandatory = models.BooleanField(default=False)
    is_critical_path = models.BooleanField(default=True)
    action_deadline_hours = models.IntegerField(default=48)
    sla_target_hours = models.IntegerField(default=24)
    responsible_user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_stages'
    )
    responsible_role = models.CharField(
        max_length=50,
        choices=[
            ('hiring_manager', 'Hiring Manager'),
            ('recruiter', 'Recruiter'),
            ('coordinator', 'Coordinator'),
            ('interviewer', 'Interviewer/Panel'),
            ('agency', 'Agency'),
            ('external', 'External Provider'),
        ],
        default='recruiter'
    )
    decision_authority = models.CharField(
        max_length=50,
        choices=[
            ('hiring_manager', 'Hiring Manager'),
            ('recruiter', 'Recruiter'),
            ('coordinator', 'Coordinator'),
            ('approver', 'Specific Approver'),
            ('admin', 'Admin/Owner'),
            ('any', 'Anyone in Team'),
        ],
        default='any'
    )
    trigger_type = models.CharField(
        max_length=50,
        choices=[
            ('none', 'None'),
            ('interview', 'Interview Round'),
            ('prequal', 'Prequalification'),
            ('assessment', 'External Assessment'),
            ('approval', 'Stage Approval'),
        ],
        default='none'
    )
    trigger_config = models.JSONField(default=dict, blank=True)
    auto_actions = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'jobs_stage'
        ordering = ['stage_order']


class JobHiringTeamMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    requisition = models.ForeignKey(JobRequisition, on_delete=models.CASCADE, related_name='hiring_team')
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='job_team_memberships',
        null=True,
        blank=True
    )
    role = models.CharField(
        max_length=50,
        choices=[
            ('interviewer', 'Interviewer'),
            ('approver', 'Approver'),
            ('stakeholder', 'Stakeholder/Viewer'),
            ('coordinator', 'Coordinator'),
            ('recruiter', 'Recruiter'),
            ('hiring_manager', 'Hiring Manager'),
        ],
        default='interviewer'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'jobs_hiring_team_member'
        unique_together = ['requisition', 'user', 'role']


class CustomFieldDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    entity_type = models.CharField(
        max_length=50,
        choices=[
            ('job', 'Job'), ('candidate', 'Candidate'),
            ('application', 'Application'), ('interview', 'Interview')
        ]
    )
    field_name = models.CharField(max_length=100)
    field_label = models.CharField(max_length=255)
    field_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'), ('number', 'Number'), ('boolean', 'Boolean'),
            ('date', 'Date'), ('dropdown', 'Dropdown'),
            ('multiselect', 'Multiselect'), ('url', 'URL'), ('email', 'Email')
        ]
    )
    field_options = models.JSONField(default=list, blank=True)
    is_required = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    placeholder = models.CharField(max_length=255, blank=True)
    help_text = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.field_label

    class Meta:
        db_table = 'jobs_custom_field_definition'
        unique_together = ['tenant_id', 'entity_type', 'field_name']


class JobDescriptionTemplate(models.Model):
    """
    Reusable job description template library.
    Stores pre-written JD content that can be applied when creating a job.
    """
    CATEGORY_CHOICES = [
        ('engineering', 'Engineering'),
        ('product', 'Product'),
        ('design', 'Design'),
        ('sales', 'Sales'),
        ('marketing', 'Marketing'),
        ('operations', 'Operations'),
        ('finance', 'Finance'),
        ('hr', 'HR'),
        ('legal', 'Legal'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', db_index=True)
    job_type = models.CharField(
        max_length=50,
        choices=[
            ('full_time', 'Full Time'), ('part_time', 'Part Time'),
            ('contract', 'Contract'), ('internship', 'Internship'),
            ('freelance', 'Freelance')
        ],
        blank=True
    )
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    skills_suggested = models.JSONField(default=list, blank=True)
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'jobs_jd_template'
        ordering = ['-usage_count', '-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'is_active']),
            models.Index(fields=['tenant_id', 'category']),
        ]


class JobLocation(models.Model):
    """
    Many-to-many junction: one job can be open in multiple locations.
    The legacy location_id on JobRequisition remains for primary/default location.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    requisition = models.ForeignKey(
        JobRequisition, on_delete=models.CASCADE, related_name='locations'
    )
    location = models.ForeignKey(
        'organisations.Location',
        on_delete=models.CASCADE,
        related_name='job_locations',
        null=True,
        blank=True
    )
    location_name = models.CharField(max_length=200, blank=True)  # denormalized for display speed
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'jobs_location'
        unique_together = ['requisition', 'location']
        indexes = [
            models.Index(fields=['tenant_id', 'requisition_id']),
        ]


class CustomFieldValue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField(db_index=True)
    field_name = models.CharField(max_length=100)
    field_value = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.field_name

    class Meta:
        db_table = 'jobs_custom_field_value'
        unique_together = ['tenant_id', 'entity_type', 'entity_id', 'field_name']
