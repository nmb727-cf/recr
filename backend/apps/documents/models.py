import uuid
from django.db import models
from django.utils import timezone


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    entity_type = models.CharField(
        max_length=50,
        choices=[
            ('candidate', 'Candidate'), ('application', 'Application'),
            ('job', 'Job'), ('organisation', 'Organisation'), ('offer', 'Offer'),
        ]
    )
    entity_id = models.UUIDField(db_index=True)
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('cv', 'CV'), ('cover_letter', 'Cover Letter'),
            ('offer_letter', 'Offer Letter'), ('contract', 'Contract'),
            ('id_proof', 'ID Proof'), ('education_certificate', 'Education Certificate'),
            ('experience_letter', 'Experience Letter'),
            ('background_check', 'Background Check'), ('other', 'Other'),
        ],
        default='other'
    )
    title = models.CharField(max_length=255)
    file_url = models.TextField()
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    version = models.IntegerField(default=1)
    is_current = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.UUIDField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    uploaded_by = models.UUIDField(null=True, blank=True)
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
        db_table = 'documents_document'
        ordering = ['-created_at']


class OfferLetter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    application_id = models.UUIDField(db_index=True)
    candidate_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=255)
    joining_date = models.DateField(null=True, blank=True)
    offered_salary = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='INR')
    compensation_details = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('draft', 'Draft'), ('pending_approval', 'Pending Approval'),
            ('approved', 'Approved'), ('sent', 'Sent'),
            ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('revoked', 'Revoked'),
        ],
        default='draft'
    )
    document_url = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_reason = models.TextField(blank=True)
    approved_by = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
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
        db_table = 'documents_offer_letter'
        ordering = ['-created_at']
