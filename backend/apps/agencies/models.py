import uuid
from django.db import models
from django.utils import timezone


class AgencyClientRelationship(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)  # The Agency's tenant_id

    # The linked Company
    company_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    agency_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Mirror fields from Client to avoid extra joins
    client_name = models.CharField(max_length=255, null=True, blank=True)
    email_domain = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending Invite'),
            ('active', 'Active Partnership'),
            ('suspended', 'Suspended'),
            ('declined', 'Declined'),
            ('archived', 'Archived'),
        ],
        default='pending'
    )
    
    # Commercials
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    commission_type = models.CharField(
        max_length=20,
        choices=[('percentage', 'Percentage of CTC'), ('fixed', 'Fixed Fee')],
        default='percentage'
    )
    
    # SLAs
    sla_submission_hours = models.IntegerField(default=48)
    sla_feedback_hours = models.IntegerField(default=72)
    
    # Protections
    retention_days = models.IntegerField(default=90, help_text="How many days agency owns candidate after submission")
    guarantee_period_days = models.IntegerField(default=90, help_text="Replacement guarantee period")
    
    # Refund/Replacement logic
    refund_type = models.CharField(
        max_length=50,
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

    # Contract files
    contract_file_url = models.TextField(blank=True)
    recruitment_policy_url = models.TextField(blank=True)

    # Payment terms
    payment_terms = models.JSONField(default=list, blank=True)
    payment_schedule = models.JSONField(default=list, blank=True)

    # ERP Allocation Logic
    auto_accept_jobs = models.BooleanField(default=False, help_text="Automatically accept job assignments from this client")
    allocated_team = models.ForeignKey(
        'organisations.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='allocated_client_relationships'
    )
    allocated_user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='allocated_client_relationships'
    )

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
    guest_portal_id = models.UUIDField(null=True, blank=True)
    email_tracking_id = models.UUIDField(null=True, blank=True)
    their_ats_url = models.CharField(max_length=500, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)

    contract_snapshot = models.JSONField(null=True, blank=True, help_text="Snapshot of terms at the moment of acceptance")

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
        return f"{self.client_name} ({self.company_tenant_id})"

    class Meta:
        db_table = 'agencies_client_relationship'
        unique_together = ['agency_tenant_id', 'company_tenant_id']


class AgencyJobAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    requisition_id = models.UUIDField(db_index=True)
    agency_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    internal_recruiter_id = models.UUIDField(null=True, blank=True, db_index=True)
    assigned_by = models.UUIDField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    max_submissions = models.IntegerField(null=True, blank=True)
    submission_count = models.IntegerField(default=0)
    
    # ERP Acceptance Logic
    status = models.CharField(
        max_length=50,
        choices=[
            ('pending_acceptance', 'Pending Acceptance'),
            ('active', 'Active'),
            ('declined', 'Declined'),
            ('paused', 'Paused'),
            ('closed', 'Closed'),
        ],
        default='pending_acceptance'
    )
    acceptance_mode = models.CharField(
        max_length=20,
        choices=[('manual', 'Manual'), ('automatic', 'Automatic')],
        default='manual'
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_assignments'
    )
    
    # Internal Allocation
    assigned_team = models.ForeignKey(
        'organisations.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_agency_jobs'
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


class AgencyMembership(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('recruiter', 'Recruiter'),
        ('sourcer', 'Sourcer'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency_tenant_id = models.UUIDField(db_index=True)
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='agency_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='recruiter')
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agencies_membership'
        unique_together = ['agency_tenant_id', 'user']


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
    avg_submission_time_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shortlist_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    offer_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    join_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'agencies_performance_score'


class EmailTrackingConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    client_name = models.CharField(max_length=255)
    email_domain = models.CharField(max_length=255)
    tracking_email = models.EmailField(unique=True)
    forward_to_email = models.EmailField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
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


class AgencyBillingTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    relationship = models.ForeignKey(AgencyClientRelationship, on_delete=models.PROTECT, related_name='billing_transactions')
    application_id = models.UUIDField(db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=5, default='INR')
    transaction_type = models.CharField(max_length=50, choices=[('commission', 'Commission'), ('refund', 'Refund')])
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('invoiced', 'Invoiced'), ('paid', 'Paid'), ('cancelled', 'Cancelled')], default='pending')
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'agencies_billing_transaction'


class GuestPortal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    portal_type = models.CharField(max_length=50, choices=[('agency_guest', 'Agency Guest'), ('client_guest', 'Client Guest')])
    contact_email = models.EmailField()
    invite_token = models.CharField(max_length=100, unique=True)
    invite_expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('active', 'Active'), ('expired', 'Expired')], default='pending')
    created_by_tenant_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'agencies_guest_portal'
