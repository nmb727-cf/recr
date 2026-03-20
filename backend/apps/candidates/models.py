from shared.models import BaseModel
from django.db import models
import uuid

class Candidate(BaseModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    linkedin_url = models.TextField(blank=True)
    current_title = models.CharField(max_length=255, blank=True)
    current_company = models.CharField(max_length=255, blank=True)
    current_city = models.CharField(max_length=100, blank=True)
    current_country = models.CharField(max_length=100, blank=True)
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    expected_salary_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    expected_salary_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='INR')
    notice_period_days = models.IntegerField(null=True, blank=True)
    availability_date = models.DateField(null=True, blank=True)
    is_actively_looking = models.BooleanField(default=True)
    source = models.CharField(max_length=100, blank=True)
    source_detail = models.TextField(blank=True)
    passport_id = models.UUIDField(null=True, blank=True)
    global_hash = models.CharField(max_length=64, blank=True, db_index=True)  # for deduplication
    is_duplicate = models.BooleanField(default=False)
    duplicate_of = models.UUIDField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    languages = models.JSONField(default=list, blank=True)
    assigned_to = models.UUIDField(null=True, blank=True)
    owner_user_id = models.UUIDField(null=True, blank=True)
    owner_tenant_id = models.UUIDField(null=True, blank=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = 'candidates_candidate'
        ordering = ['-created_at']


class CandidateProfile(BaseModel):
    candidate_id = models.UUIDField(unique=True, db_index=True)
    summary = models.TextField(blank=True)
    work_experience = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    projects = models.JSONField(default=list, blank=True)
    awards = models.JSONField(default=list, blank=True)
    cv_url = models.TextField(blank=True)
    cv_parsed_data = models.JSONField(default=dict, blank=True)
    cv_uploaded_at = models.DateTimeField(null=True, blank=True)
    portfolio_url = models.TextField(blank=True)
    github_url = models.TextField(blank=True)

    def __str__(self):
        return str(self.candidate_id)

    class Meta:
        db_table = 'candidates_profile'


class CandidateNote(BaseModel):
    candidate_id = models.UUIDField(db_index=True)
    note_text = models.TextField()
    note_type = models.CharField(
        max_length=50,
        choices=[
            ('general', 'General'), ('call_log', 'Call Log'),
            ('email_log', 'Email Log'), ('interview_note', 'Interview Note'),
            ('warning', 'Warning'), ('positive', 'Positive')
        ],
        default='general'
    )
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.note_text[:50]

    class Meta:
        db_table = 'candidates_note'
        ordering = ['-created_at']
