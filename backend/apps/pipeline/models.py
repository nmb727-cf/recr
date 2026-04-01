import uuid
from django.db import models
from django.utils import timezone


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    candidate_id = models.UUIDField(db_index=True)
    requisition_id = models.UUIDField(db_index=True)
    current_stage_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('applied', 'Applied'),
            ('sourcing', 'Sourcing'),
            ('screening', 'Screening'),
            ('shortlisted', 'Shortlisted'),
            ('interview', 'Interview'),
            ('assessment', 'Assessment'),
            ('offer', 'Offer'),
            ('joined', 'Joined'),
            ('rejected', 'Rejected'),
            ('withdrawn', 'Withdrawn'),
            ('on_hold', 'On Hold'),
        ],
        default='applied'
    )
    source = models.CharField(max_length=100, blank=True)
    source_detail = models.TextField(blank=True)
    submitted_by = models.UUIDField(null=True, blank=True)
    submitted_by_tenant_id = models.UUIDField(null=True, blank=True)
    agency_id = models.UUIDField(null=True, blank=True)
    is_agency_submission = models.BooleanField(default=False)
    match_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    rejection_category = models.CharField(max_length=100, blank=True)
    withdrawn_reason = models.TextField(blank=True)
    offer_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    offer_currency = models.CharField(max_length=10, default='INR')
    offer_date = models.DateField(null=True, blank=True)
    offer_accepted_at = models.DateTimeField(null=True, blank=True)
    offer_rejected_at = models.DateTimeField(null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    application_form_data = models.JSONField(default=dict, blank=True)
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
        return f"{self.candidate_id} - {self.requisition_id}"

    class Meta:
        db_table = 'pipeline_application'
        ordering = ['-created_at']
        unique_together = ['tenant_id', 'candidate_id', 'requisition_id']


class ApplicationStageHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    application_id = models.UUIDField(db_index=True)
    from_stage_id = models.UUIDField(null=True, blank=True)
    to_stage_id = models.UUIDField(null=True, blank=True)
    from_status = models.CharField(max_length=50, blank=True)
    to_status = models.CharField(max_length=50, blank=True)
    moved_by = models.UUIDField(null=True, blank=True)
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    moved_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.application_id} — {self.from_status} to {self.to_status}"

    class Meta:
        db_table = 'pipeline_stage_history'
        ordering = ['-moved_at']


class ActionDeadline(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    entity_type = models.CharField(
        max_length=50,
        choices=[
            ('application', 'Application'),
            ('interview', 'Interview'),
            ('offer', 'Offer'),
            ('requisition', 'Requisition'),
        ]
    )
    entity_id = models.UUIDField()
    action_required = models.CharField(max_length=255)
    assigned_to = models.UUIDField(null=True, blank=True)
    escalate_to = models.UUIDField(null=True, blank=True)
    deadline_at = models.DateTimeField()
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('reminded', 'Reminded'),
            ('escalated', 'Escalated'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.status = 'cancelled'
        self.save()

    def __str__(self):
        return f"{self.action_required} — {self.deadline_at}"

    class Meta:
        db_table = 'pipeline_action_deadline'
        ordering = ['deadline_at']


class PlacementGuarantee(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('breached', 'Breached'),
        ('replacement_requested', 'Replacement Requested'),
        ('refund_requested', 'Refund Requested'),
        ('resolved', 'Resolved'),
        ('expired', 'Expired'),
        ('waived', 'Waived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application_id = models.UUIDField(db_index=True)
    candidate_id = models.UUIDField(db_index=True)
    requisition_id = models.UUIDField(db_index=True)
    agency_tenant_id = models.UUIDField(db_index=True)
    company_tenant_id = models.UUIDField(db_index=True)
    agency_relationship_id = models.UUIDField(db_index=True)
    guarantee_start_date = models.DateField()
    guarantee_end_date = models.DateField(db_index=True)
    guarantee_resolution_type = models.CharField(max_length=40, default='replacement_only')
    refund_mode = models.CharField(max_length=40, blank=True)
    refund_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    replacement_attempt_limit = models.CharField(max_length=20, default='1')
    current_attempt_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='active', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'pipeline_placement_guarantee'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company_tenant_id', 'status']),
            models.Index(fields=['requisition_id', 'status']),
        ]


# ── Commercial Closure Models ─────────────────────────────────────────────────

class Placement(models.Model):
    """
    One placement record per application that reaches the offer stage.
    Tracks the candidate's journey from offer → join → placement confirmed.
    Commercial state is separate from hiring state (application.status).
    """
    PLACEMENT_STATUS_CHOICES = [
        ('pending_offer', 'Pending Offer Response'),
        ('offer_accepted', 'Offer Accepted'),
        ('pending_join', 'Pending Join'),
        ('joined', 'Joined'),
        ('placement_confirmed', 'Placement Confirmed'),
        ('cancelled', 'Cancelled'),
        ('guarantee_active', 'Guarantee Active'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    application_id = models.UUIDField(unique=True, db_index=True)
    candidate_id = models.UUIDField(db_index=True)
    requisition_id = models.UUIDField(db_index=True)
    agency_id = models.UUIDField(null=True, blank=True, db_index=True)
    agency_relationship_id = models.UUIDField(null=True, blank=True)
    placement_status = models.CharField(
        max_length=30,
        choices=PLACEMENT_STATUS_CHOICES,
        default='pending_offer',
        db_index=True,
    )
    offer_accepted_at = models.DateTimeField(null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    placement_confirmed_at = models.DateTimeField(null=True, blank=True)
    credited_recruiter_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'pipeline_placement'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'placement_status']),
            models.Index(fields=['requisition_id', 'placement_status']),
        ]


class CommissionRecord(models.Model):
    """
    Commercial commission tracking for a placement.
    Holds expected amount, payment status, and due/paid dates.
    Decoupled from hiring state — commercial lifecycle runs in parallel.
    """
    COMMISSION_MODEL_CHOICES = [
        ('percentage', 'Percentage of Salary'),
        ('fixed', 'Fixed Fee'),
        ('milestone', 'Milestone Based'),
        ('custom', 'Custom'),
    ]
    BASIS_SOURCE_CHOICES = [
        ('inherited', 'Inherited from Agency Relationship'),
        ('custom_per_job', 'Custom per Job'),
        ('manual', 'Manually Set'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('pending_invoice', 'Pending Invoice'),
        ('invoice_expected', 'Invoice Expected'),
        ('payment_due', 'Payment Due'),
        ('reminder_sent', 'Reminder Sent'),
        ('overdue', 'Overdue'),
        ('paid', 'Paid'),
        ('disputed', 'Disputed'),
        ('waived', 'Waived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    placement_id = models.UUIDField(unique=True, db_index=True)
    application_id = models.UUIDField(db_index=True)
    requisition_id = models.UUIDField(db_index=True)
    company_tenant_id = models.UUIDField(db_index=True)
    agency_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    agency_relationship_id = models.UUIDField(null=True, blank=True)
    commission_applicable = models.BooleanField(default=True)
    commission_model = models.CharField(
        max_length=20, choices=COMMISSION_MODEL_CHOICES, default='percentage'
    )
    basis_source = models.CharField(
        max_length=30, choices=BASIS_SOURCE_CHOICES, default='manual'
    )
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='Percentage rate (e.g. 15.00 = 15%)',
    )
    commission_fixed_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    expected_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(max_length=10, default='INR')
    payment_status = models.CharField(
        max_length=30, choices=PAYMENT_STATUS_CHOICES, default='not_started', db_index=True
    )
    due_date = models.DateField(null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    payment_notes = models.TextField(blank=True)
    reminder_count = models.PositiveIntegerField(default=0)
    last_reminder_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'pipeline_commission_record'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company_tenant_id', 'payment_status']),
            models.Index(fields=['requisition_id', 'payment_status']),
        ]


class CommissionReminder(models.Model):
    """Log of every reminder action taken for a commission record."""
    REMINDER_TYPE_CHOICES = [
        ('initial_notice', 'Initial Notice'),
        ('follow_up', 'Follow Up'),
        ('final_notice', 'Final Notice'),
        ('manual', 'Manual'),
    ]
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('whatsapp', 'WhatsApp'),
        ('manual', 'Manual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commission_record_id = models.UUIDField(db_index=True)
    reminder_type = models.CharField(
        max_length=20, choices=REMINDER_TYPE_CHOICES, default='manual'
    )
    channel = models.CharField(
        max_length=20, choices=CHANNEL_CHOICES, default='manual'
    )
    sent_by = models.UUIDField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'pipeline_commission_reminder'
        ordering = ['-sent_at']
