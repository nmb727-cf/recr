from shared.models import BaseModel
from django.db import models
import uuid

class Application(BaseModel):
    candidate_id = models.UUIDField(db_index=True)
    job_id = models.UUIDField(db_index=True)
    current_stage_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('applied', 'Applied'), ('screening', 'Screening'),
            ('shortlisted', 'Shortlisted'), ('interview', 'Interview'),
            ('assessment', 'Assessment'), ('offer', 'Offer'),
            ('joined', 'Joined'), ('rejected', 'Rejected'),
            ('withdrawn', 'Withdrawn'), ('on_hold', 'On Hold')
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
    joining_date = models.DateField(null=True, blank=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    application_form_data = models.JSONField(default=dict, blank=True)
    product = models.CharField(
        max_length=20,
        choices=[
            ('ats', 'ATS'), ('cafe', 'Cafe'), ('marketplace', 'Marketplace')
        ],
        default='ats'
    )

    def __str__(self):
        return f"{self.candidate_id} - {self.job_id}"

    class Meta:
        db_table = 'pipeline_application'
        ordering = ['-created_at']
        unique_together = ['tenant_id', 'candidate_id', 'job_id']


class ApplicationStageHistory(BaseModel):
    application_id = models.UUIDField(db_index=True)
    from_stage_id = models.UUIDField(null=True, blank=True)
    to_stage_id = models.UUIDField(null=True, blank=True)
    from_status = models.CharField(max_length=50, blank=True)
    to_status = models.CharField(max_length=50, blank=True)
    changed_by = models.UUIDField(null=True, blank=True)
    changed_by_tenant_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"{self.application_id} - {self.from_stage_id} to {self.to_stage_id}"

    class Meta:
        db_table = 'pipeline_application_stage_history'
