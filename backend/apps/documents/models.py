from shared.models import BaseModel
from django.db import models


class Document(BaseModel):
    ENTITY_TYPES = [
        ('candidate', 'Candidate'),
        ('application', 'Application'),
        ('job', 'Job'),
        ('organisation', 'Organisation'),
        ('offer', 'Offer'),
    ]
    DOC_TYPES = [
        ('cv', 'CV'),
        ('cover_letter', 'Cover Letter'),
        ('offer_letter', 'Offer Letter'),
        ('contract', 'Contract'),
        ('id_proof', 'ID Proof'),
        ('education_certificate', 'Education Certificate'),
        ('experience_letter', 'Experience Letter'),
        ('background_check', 'Background Check'),
        ('other', 'Other'),
    ]
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPES)
    entity_id = models.UUIDField(db_index=True)
    document_type = models.CharField(max_length=50, choices=DOC_TYPES, default='other')
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

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'documents_document'
        ordering = ['-created_at']
