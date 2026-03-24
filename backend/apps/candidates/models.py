import uuid
import hashlib
from django.db import models
from django.utils import timezone


class Candidate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # tenant_id is nullable — null means self-registered candidate
    # not null means added by agency or company
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    phone_country_code = models.CharField(max_length=10, blank=True, default='IN')
    phone_number = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    linkedin_url = models.TextField(blank=True)
    current_title = models.CharField(max_length=255, blank=True)
    current_company = models.CharField(max_length=255, blank=True)
    current_location_city = models.CharField(max_length=100, blank=True)
    current_location_country = models.CharField(max_length=100, blank=True)
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    # Professional details
    designation = models.CharField(max_length=255, blank=True)
    relevant_experience_years = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )

    # Compensation
    current_ctc = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    current_ctc_currency = models.CharField(
        max_length=10, default='INR', blank=True
    )
    offer_in_hand = models.BooleanField(default=False)
    offer_in_hand_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    counter_offer = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )

    # Availability
    availability_status = models.CharField(
        max_length=50,
        choices=[
            ('available_now', 'Available Now'),
            ('notice_period', 'Serving Notice Period'),
            ('not_looking', 'Not Looking'),
            ('open_to_offers', 'Open to Offers'),
        ],
        blank=True
    )
    last_working_day = models.DateField(null=True, blank=True)
    work_mode_preference = models.CharField(
        max_length=20,
        choices=[
            ('any', 'Any'),
            ('remote', 'Remote Only'),
            ('hybrid', 'Hybrid'),
            ('onsite', 'On-site Only'),
        ],
        default='any',
        blank=True
    )

    # Scoring
    fitment_score = models.IntegerField(null=True, blank=True)

    # Profile lifecycle
    profile_status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('partial', 'Partial'),
            ('complete', 'Complete'),
            ('claimed', 'Claimed'),
        ],
        default='partial'
    )
    initial_entry_type = models.CharField(
        max_length=20,
        choices=[
            ('self', 'Self Registered'),
            ('invite', 'Invite Link'),
            ('manual', 'Manual Add'),
            ('passport_import', 'Passport Import'),
            ('agency_submission', 'Agency Submission'),
        ],
        blank=True
    )
    claim_token = models.CharField(max_length=100, blank=True, db_index=True)
    claim_token_expires_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    account_status = models.CharField(
        max_length=20,
        choices=[
            ('none', 'No Account'),
            ('invited', 'Invite Sent'),
            ('claimed', 'Account Claimed'),
            ('active', 'Active User'),
        ],
        default='none'
    )
    invite_sent_at = models.DateTimeField(null=True, blank=True)
    expected_salary_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    expected_salary_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='INR')
    notice_period_days = models.IntegerField(null=True, blank=True)
    availability_date = models.DateField(null=True, blank=True)
    is_actively_looking = models.BooleanField(default=True)
    
    # New fields
    nationality = models.CharField(max_length=100, blank=True)
    work_authorization = models.CharField(max_length=100, blank=True)
    highest_education = models.CharField(max_length=100, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    relocation_willing = models.CharField(max_length=50, blank=True)
    preferred_locations = models.JSONField(default=list, blank=True)
    resume_url = models.TextField(blank=True)

    source = models.CharField(
        max_length=100,
        choices=[
            ('self', 'Self Registered'),
            ('agency', 'Agency'),
            ('company', 'Company'),
            ('linkedin', 'LinkedIn'),
            ('referral', 'Referral'),
            ('job_board', 'Job Board'),
            ('passport', 'Talent Passport'),
            ('cafe', 'Interview Cafe'),
            ('other', 'Other'),
        ],
        blank=True
    )
    source_detail = models.TextField(blank=True)
    passport_id = models.UUIDField(null=True, blank=True)
    duplicate_of = models.UUIDField(null=True, blank=True)
    is_duplicate = models.BooleanField(default=False)
    # global_hash links same person across tenants
    global_hash = models.CharField(max_length=64, blank=True, db_index=True)
    tags = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    languages = models.JSONField(default=list, blank=True)
    assigned_to = models.UUIDField(null=True, blank=True)
    # who originally sourced this candidate
    owner_user_id = models.UUIDField(null=True, blank=True)
    owner_tenant_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if self.email or self.phone:
            hash_input = f"{self.email.lower().strip()}{self.phone.strip()}".encode()
            self.global_hash = hashlib.sha256(hash_input).hexdigest()
        super().save(*args, **kwargs)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = 'candidates_candidate'
        ordering = ['-created_at']


class CandidateProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    candidate_id = models.UUIDField(unique=True, db_index=True)
    summary = models.TextField(blank=True)
    work_experience = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    projects = models.JSONField(default=list, blank=True)
    publications = models.JSONField(default=list, blank=True)
    awards = models.JSONField(default=list, blank=True)
    references = models.JSONField(default=list, blank=True)
    cv_url = models.TextField(blank=True)
    cv_parsed_data = models.JSONField(default=dict, blank=True)
    cv_uploaded_at = models.DateTimeField(null=True, blank=True)
    portfolio_url = models.TextField(blank=True)
    github_url = models.TextField(blank=True)
    stackoverflow_url = models.TextField(blank=True)
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
        return str(self.candidate_id)

    class Meta:
        db_table = 'candidates_profile'


class CandidateNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    candidate_id = models.UUIDField(db_index=True)
    note_text = models.TextField()
    note_type = models.CharField(
        max_length=50,
        choices=[
            ('general', 'General'),
            ('call_log', 'Call Log'),
            ('email_log', 'Email Log'),
            ('interview_note', 'Interview Note'),
            ('warning', 'Warning'),
            ('positive', 'Positive'),
        ],
        default='general'
    )
    is_private = models.BooleanField(default=False)
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
        return self.note_text[:50]

    class Meta:
        db_table = 'candidates_note'
        ordering = ['-created_at']


class CandidateInviteLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    created_by = models.UUIDField(null=True, blank=True)
    token = models.CharField(max_length=100, unique=True)
    form_config = models.JSONField(default=dict, blank=True)
    job_id = models.UUIDField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.IntegerField(null=True, blank=True)
    use_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[('active','Active'),('expired','Expired'),('disabled','Disabled')],
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.token:
            import secrets
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'candidates_invite_link'


class CandidateFormSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invite_link_id = models.UUIDField(db_index=True)
    tenant_id = models.UUIDField(db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    cv_url = models.TextField(blank=True)
    cv_filename = models.CharField(max_length=255, blank=True)
    form_data = models.JSONField(default=dict, blank=True)
    candidate_id = models.UUIDField(null=True, blank=True)
    user_id = models.UUIDField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('submitted','Submitted'),('processed','Processed'),('converted','Converted')],
        default='submitted'
    )
    wants_account = models.BooleanField(default=False)
    account_created = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'candidates_form_submission'


class Skill(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(
        max_length=100, blank=True)  # e.g. Programming, Design, etc
    aliases = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'candidates_skill'
        ordering = ['-usage_count', 'name']

    def __str__(self):
        return self.name
