from shared.models import BaseModel
from django.db import models
import uuid

class CustomFieldDefinition(BaseModel):
    entity_type = models.CharField(
        max_length=50,
        choices=[
            ('job', 'Job'), ('candidate', 'Candidate'), ('application', 'Application'),
            ('organisation', 'Organisation'), ('interview', 'Interview')
        ]
    )
    field_name = models.CharField(max_length=100)
    field_label = models.CharField(max_length=255)
    field_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'), ('number', 'Number'), ('boolean', 'Boolean'),
            ('date', 'Date'), ('dropdown', 'Dropdown'), ('multiselect', 'Multiselect'),
            ('url', 'URL'), ('email', 'Email')
        ]
    )
    field_options = models.JSONField(default=list, blank=True)
    is_required = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    placeholder = models.CharField(max_length=255, blank=True)
    help_text = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.field_label

    class Meta:
        db_table = 'custom_field_definitions'
        unique_together = ['tenant_id', 'entity_type', 'field_name']


class CustomFieldValue(BaseModel):
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField(db_index=True)
    field_name = models.CharField(max_length=100)
    field_value = models.TextField(blank=True)

    def __str__(self):
        return self.field_name

    class Meta:
        db_table = 'custom_field_values'
        unique_together = ['tenant_id', 'entity_type', 'entity_id', 'field_name']


class Job(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    job_type = models.CharField(
        max_length=50,
        choices=[
            ('full_time', 'Full Time'), ('part_time', 'Part Time'),
            ('contract', 'Contract'), ('internship', 'Internship'), ('freelance', 'Freelance')
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
    experience_min = models.IntegerField(default=0)
    experience_max = models.IntegerField(null=True, blank=True)
    salary_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='INR')
    salary_visible = models.BooleanField(default=False)
    headcount = models.IntegerField(default=1)
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')
        ],
        default='medium'
    )
    is_confidential = models.BooleanField(default=False)
    status = models.CharField(
        max_length=50,
        choices=[
            ('draft', 'Draft'), ('pending_approval', 'Pending Approval'),
            ('approved', 'Approved'), ('active', 'Active'), ('paused', 'Paused'),
            ('closed', 'Closed'), ('cancelled', 'Cancelled')
        ],
        default='draft'
    )
    skills_required = models.JSONField(default=list, blank=True)
    department_id = models.UUIDField(null=True, blank=True)
    location_id = models.UUIDField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_reason = models.CharField(max_length=255, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.UUIDField(null=True, blank=True)
    budget_code = models.CharField(max_length=100, blank=True)
    product = models.CharField(
        max_length=20,
        choices=[
            ('ats', 'ATS'), ('cafe', 'Cafe'), ('marketplace', 'Marketplace')
        ],
        default='ats'
    )

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'jobs_job'
        ordering = ['-created_at']


class JobStage(BaseModel):
    job_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=100)
    stage_order = models.IntegerField(default=0)
    stage_type = models.CharField(
        max_length=50,
        choices=[
            ('sourcing', 'Sourcing'), ('screening', 'Screening'),
            ('interview', 'Interview'), ('assessment', 'Assessment'),
            ('offer', 'Offer'), ('joined', 'Joined'), ('rejected', 'Rejected'),
            ('withdrawn', 'Withdrawn')
        ],
        default='screening'
    )
    action_deadline_hours = models.IntegerField(default=48)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'jobs_stage'
        ordering = ['stage_order']
