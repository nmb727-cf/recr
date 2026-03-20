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
