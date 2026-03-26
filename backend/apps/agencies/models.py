import uuid
from django.db import models
from django.utils import timezone


class AgencyClientRelationship(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    agency_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    company_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('terminated', 'Terminated'),
        ],
        default='pending'
    )
    tier = models.CharField(
        max_length=50,
        choices=[
            ('preferred', 'Preferred'),
            ('standard', 'Standard'),
            ('probation', 'Probation'),
            ('blacklisted', 'Blacklisted'),
        ],
        default='standard'
    )
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    sla_submission_hours = models.IntegerField(default=48)
    sla_feedback_hours = models.IntegerField(default=72)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    commission_type = models.CharField(
        max_length=50,
        choices=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed'),
            ('milestone', 'Milestone'),
        ],
        blank=True
    )
    notes = models.TextField(blank=True)
    retention_enabled = models.BooleanField(default=False)
    retention_days = models.PositiveIntegerField(default=90)
    retention_start_type = models.CharField(
        max_length=40,
        choices=[
            ('submission_date', 'Submission Date'),
            ('rejection_date', 'Rejection Date'),
            ('last_activity_date', 'Last Activity Date'),
        ],
        default='submission_date',
    )
    retention_scope = models.CharField(
        max_length=40,
        choices=[
            ('job_only', 'Job Only'),
            ('view_only', 'View Only'),
            ('limited_company_access', 'Limited Company Access'),
        ],
        default='job_only',
    )
    retention_post_expiry = models.CharField(
        max_length=40,
        choices=[
            ('shared', 'Shared Ownership'),
            ('company_use', 'Company Can Use Candidate'),
            ('consent_required', 'Require Candidate Consent'),
        ],
        default='shared',
    )
    replacement_guarantee_enabled = models.BooleanField(default=False)
    guarantee_period_days = models.PositiveIntegerField(default=30)
    guarantee_start_type = models.CharField(
        max_length=40,
        choices=[
            ('joining_date', 'Joining Date'),
            ('offer_acceptance_date', 'Offer Acceptance Date'),
            ('first_working_day', 'First Working Day'),
        ],
        default='joining_date',
    )
    guarantee_resolution_type = models.CharField(
        max_length=40,
        choices=[
            ('replacement_only', 'Replacement Only'),
            ('refund_only', 'Refund Only'),
            ('replacement_or_refund', 'Replacement or Refund'),
            ('no_guarantee', 'No Guarantee'),
        ],
        default='replacement_only',
    )
    refund_mode = models.CharField(
        max_length=40,
        choices=[
            ('full_refund', 'Full Refund'),
            ('partial_refund', 'Partial Refund'),
            ('pro_rated_refund', 'Pro-rated Refund'),
        ],
        blank=True,
    )
    refund_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    replacement_attempt_limit = models.CharField(
        max_length=20,
        choices=[
            ('1', '1'),
            ('2', '2'),
            ('unlimited', 'Unlimited'),
        ],
        default='1',
    )
    guarantee_notes = models.TextField(blank=True)

    # Contact details
    contact_person_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_country_code = models.CharField(max_length=10, blank=True, default='IN')
    contact_phone_number = models.CharField(max_length=20, blank=True)
    industry = models.CharField(max_length=100, blank=True)

    # Contract files (store URL, upload wired later)
    contract_file_url = models.TextField(blank=True)
    recruitment_policy_url = models.TextField(blank=True)

    # Payment terms — stored as JSON list of selected options
    payment_terms = models.JSONField(default=list, blank=True)

    # Structured payment schedule for automation
    # Stored as list of objects: [{trigger: 'joining', percentage: 50}, {trigger: 'days_after_joining', days: 90, percentage: 50}]
    payment_schedule = models.JSONField(default=list, blank=True)

    # Invite tracking
    invited_by = models.CharField(
        max_length=10,
        choices=[('company', 'Company'), ('agency', 'Agency')],
        blank=True
    )
    invited_via = models.CharField(max_length=255, blank=True)

    connection_type = models.CharField(
        max_length=20,
        choices=[
            ('full_full', 'Both Full Tenants'),
            ('agency_guest', 'Agency on Guest Portal'),
            ('client_guest', 'Client on Guest Portal'),
            ('email_tracking', 'Email Tracking Only'),
            ('offline', 'Offline Client'),
        ],
        default='full_full',
        blank=True
    )
    guest_portal_id = models.UUIDField(null=True, blank=True)         # FK to GuestPortal if applicable
    email_tracking_id = models.UUIDField(null=True, blank=True)       # FK to EmailTrackingConfig if applicable
    their_ats_url = models.CharField(max_length=500, blank=True)      # for offline clients with own ATS
    last_activity_at = models.DateTimeField(null=True, blank=True)    # last login / email / action

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
        return f"{self.agency_tenant_id} - {self.company_tenant_id}"

    class Meta:
        db_table = 'agencies_client_relationship'
        unique_together = ['agency_tenant_id', 'company_tenant_id']


class AgencyJobAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    requisition_id = models.UUIDField(db_index=True)
    agency_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    assigned_by = models.UUIDField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    max_submissions = models.IntegerField(null=True, blank=True)
    submission_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=50,
        choices=[
            ('active', 'Active'),
            ('paused', 'Paused'),
            ('closed', 'Closed'),
        ],
        default='active'
    )
    notes = models.TextField(blank=True)
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
        return f"{self.requisition_id} - {self.agency_tenant_id}"

    class Meta:
        db_table = 'agencies_job_assignment'
        unique_together = ['tenant_id', 'requisition_id', 'agency_tenant_id']


class AgencyPerformanceScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    agency_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    company_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    period_start = models.DateField()
    period_end = models.DateField()
    total_submissions = models.IntegerField(default=0)
    shortlisted_count = models.IntegerField(default=0)
    interviewed_count = models.IntegerField(default=0)
    offered_count = models.IntegerField(default=0)
    joined_count = models.IntegerField(default=0)
    shortlist_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    offer_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    join_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_submission_time_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.agency_tenant_id} - {self.period_start}"

    class Meta:
        db_table = 'agencies_performance_score'


import secrets

class GuestPortal(models.Model):
    PORTAL_TYPE_CHOICES = [
        ('agency_guest', 'Agency Guest Portal'),
        ('client_guest', 'Client Guest Portal'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Invite Pending'),
        ('active', 'Active'),
        ('expired', 'Invite Expired'),
        ('upgraded', 'Upgraded to Full Tenant'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portal_type = models.CharField(max_length=20, choices=PORTAL_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_country_code = models.CharField(max_length=10, blank=True, default='IN')
    contact_phone_number = models.CharField(max_length=20, blank=True)
    created_by_tenant_id = models.UUIDField(db_index=True)
    created_by_user_id = models.UUIDField(null=True, blank=True)
    invite_token = models.CharField(max_length=64, unique=True, blank=True)
    invite_sent_at = models.DateTimeField(null=True, blank=True)
    invite_expires_at = models.DateTimeField(null=True, blank=True)
    invite_accepted_at = models.DateTimeField(null=True, blank=True)
    invite_message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    upgraded_tenant_id = models.UUIDField(null=True, blank=True)
    upgraded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def generate_invite_token(self):
        self.invite_token = secrets.token_urlsafe(48)
        return self.invite_token

    def is_invite_expired(self):
        if not self.invite_expires_at:
            return False
        return timezone.now() > self.invite_expires_at

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.name} ({self.portal_type}) — {self.status}"

    class Meta:
        db_table = 'agencies_guest_portal'
        ordering = ['-created_at']


class EmailTrackingConfig(models.Model):
    """
    Stores which email domains to monitor for a given agency-client relationship.
    When agency adds client as "email tracking", we store the domain here.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency_tenant_id = models.UUIDField(db_index=True)
    client_name = models.CharField(max_length=255)
    email_domain = models.CharField(max_length=255)           # e.g. @acmecorp.com
    contact_email = models.EmailField(blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    their_ats_url = models.CharField(max_length=500, blank=True)
    receive_via_email = models.BooleanField(default=True)
    receive_via_portal = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('paused', 'Paused'),
        ],
        default='active'
    )
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
        return f"{self.client_name} — {self.email_domain}"

    class Meta:
        db_table = 'agencies_email_tracking'
        ordering = ['-created_at']
