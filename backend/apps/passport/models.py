import uuid
import secrets
from django.db import models
from django.utils import timezone


class TalentPassport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True, db_index=True)
    candidate_id = models.UUIDField(null=True, blank=True, db_index=True)
    passport_number = models.CharField(max_length=50, unique=True)
    share_link_token = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    # Profile
    headline = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    profile_photo_url = models.TextField(blank=True)
    cover_image_url = models.TextField(blank=True)
    video_intro_url = models.TextField(blank=True)

    # Professional
    current_title = models.CharField(max_length=255, blank=True)
    current_company = models.CharField(max_length=255, blank=True)
    current_location_city = models.CharField(max_length=100, blank=True)
    current_location_country = models.CharField(max_length=100, blank=True)
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, default=0)

    # CV
    current_cv_url = models.TextField(blank=True)
    current_cv_filename = models.CharField(max_length=255, blank=True)
    current_cv_uploaded_at = models.DateTimeField(null=True, blank=True)
    cv_parsed_data = models.JSONField(default=dict, blank=True)

    # Profile sections
    work_history = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    projects = models.JSONField(default=list, blank=True)
    publications = models.JSONField(default=list, blank=True)
    awards = models.JSONField(default=list, blank=True)
    volunteer_work = models.JSONField(default=list, blank=True)
    test_scores = models.JSONField(default=list, blank=True)
    featured_media = models.JSONField(default=list, blank=True)
    languages = models.JSONField(default=list, blank=True)
    references = models.JSONField(default=list, blank=True)

    # Social
    linkedin_url = models.TextField(blank=True)
    github_url = models.TextField(blank=True)
    portfolio_url = models.TextField(blank=True)
    twitter_url = models.TextField(blank=True)
    behance_url = models.TextField(blank=True)
    dribbble_url = models.TextField(blank=True)
    other_social_urls = models.JSONField(default=dict, blank=True)

    # Job preferences
    preferred_locations = models.JSONField(default=list, blank=True)
    preferred_work_mode = models.CharField(
        max_length=50, blank=True,
        choices=[('onsite', 'Onsite'), ('remote', 'Remote'), ('hybrid', 'Hybrid'), ('any', 'Any')]
    )
    preferred_job_types = models.JSONField(default=list, blank=True)
    preferred_industries = models.JSONField(default=list, blank=True)
    expected_salary_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    expected_salary_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='INR')
    notice_period_days = models.IntegerField(null=True, blank=True)
    availability_date = models.DateField(null=True, blank=True)
    is_actively_looking = models.BooleanField(default=True)
    open_to_work = models.BooleanField(default=True)

    # Verification
    identity_verified = models.BooleanField(default=False)
    identity_verified_at = models.DateTimeField(null=True, blank=True)
    background_verified = models.BooleanField(default=False)
    employment_verified = models.BooleanField(default=False)
    education_verified = models.BooleanField(default=False)

    # Scores
    interview_scores = models.JSONField(default=list, blank=True)
    assessment_results = models.JSONField(default=list, blank=True)
    heat_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    completeness_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    market_demand_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Privacy
    visibility_settings = models.JSONField(default=dict, blank=True)
    view_count = models.IntegerField(default=0)
    last_viewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.passport_number:
            self.passport_number = f"TP{secrets.token_hex(6).upper()}"
        if not self.share_link_token:
            self.share_link_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.passport_number

    class Meta:
        db_table = 'passport_talent_passport'


class ResumeVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passport_id = models.UUIDField(db_index=True)
    version_number = models.IntegerField(default=1)
    file_url = models.TextField()
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, default='application/pdf')
    parsed_data = models.JSONField(default=dict, blank=True)
    is_current = models.BooleanField(default=False)
    label = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.filename} - Version {self.version_number}"

    class Meta:
        db_table = 'passport_resume_version'
        ordering = ['-version_number']


class PassportAccessLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passport_id = models.UUIDField(db_index=True)
    accessed_by_user_id = models.UUIDField(null=True, blank=True)
    accessed_by_tenant_id = models.UUIDField(null=True, blank=True)
    access_type = models.CharField(
        max_length=50,
        choices=[
            ('view', 'View'), ('import', 'Import'),
            ('share', 'Share'), ('export', 'Export')
        ],
        default='view'
    )
    ip_address = models.CharField(max_length=45, blank=True)
    fields_accessed = models.JSONField(default=list, blank=True)
    imported_to_system = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.UUIDField(null=True, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.passport_id} - {self.access_type}"

    class Meta:
        db_table = 'passport_access_log'
        ordering = ['-accessed_at']


class PassportRevocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passport_id = models.UUIDField(db_index=True)
    revoked_from_tenant_id = models.UUIDField(null=True, blank=True)
    revoked_from_user_id = models.UUIDField(null=True, blank=True)
    reason = models.TextField(blank=True)
    revoked_at = models.DateTimeField(auto_now_add=True)
    revoked_by = models.UUIDField()
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return str(self.passport_id)

    class Meta:
        db_table = 'passport_revocation'
        ordering = ['-revoked_at']
