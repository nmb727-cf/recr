from shared.models import BaseModel
from django.db import models
import uuid

class AgencyClientRelationship(BaseModel):
    agency_tenant_id = models.UUIDField(db_index=True)
    company_tenant_id = models.UUIDField(db_index=True)
    status = models.CharField(
        max_length=50,
        choices=[('pending', 'Pending'), ('active', 'Active'), ('suspended', 'Suspended'), ('terminated', 'Terminated')],
        default='pending'
    )
    tier = models.CharField(
        max_length=50,
        choices=[('preferred', 'Preferred'), ('standard', 'Standard'), ('probation', 'Probation'), ('blacklisted', 'Blacklisted')],
        default='standard'
    )
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    sla_submission_hours = models.IntegerField(default=48)
    sla_feedback_hours = models.IntegerField(default=72)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    commission_type = models.CharField(
        max_length=50,
        choices=[('percentage', 'Percentage'), ('fixed', 'Fixed'), ('milestone', 'Milestone')],
        blank=True
    )
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.agency_tenant_id} - {self.company_tenant_id}"

    class Meta:
        db_table = 'agencies_client_relationship'
        unique_together = ['agency_tenant_id', 'company_tenant_id']


class AgencyJobAssignment(BaseModel):
    requisition_id = models.UUIDField(db_index=True)
    agency_tenant_id = models.UUIDField(db_index=True)
    assigned_by = models.UUIDField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    max_submissions = models.IntegerField(null=True, blank=True)
    submission_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=50,
        choices=[('active', 'Active'), ('paused', 'Paused'), ('closed', 'Closed')],
        default='active'
    )
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.requisition_id} - {self.agency_tenant_id}"

    class Meta:
        db_table = 'agencies_job_assignment'
        unique_together = ['tenant_id', 'requisition_id', 'agency_tenant_id']


class AgencyPerformanceScore(BaseModel):
    agency_tenant_id = models.UUIDField(db_index=True)
    company_tenant_id = models.UUIDField(db_index=True)
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

    def __str__(self):
        return f"{self.agency_tenant_id} - {self.period_start}"

    class Meta:
        db_table = 'agencies_performance_score'
