from shared.models import BaseModel
from django.db import models


class AutomationRule(BaseModel):
    TRIGGER_EVENTS = [
        ('application.submitted', 'Application Submitted'),
        ('application.stage_changed', 'Application Stage Changed'),
        ('application.shortlisted', 'Application Shortlisted'),
        ('interview.completed', 'Interview Completed'),
        ('offer.sent', 'Offer Sent'),
        ('deadline.overdue', 'Deadline Overdue'),
        ('agency.submitted', 'Agency Submitted'),
        ('job.approved', 'Job Approved'),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    trigger_event = models.CharField(max_length=100, choices=TRIGGER_EVENTS)
    conditions = models.JSONField(default=dict, blank=True)
    actions = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    execution_count = models.IntegerField(default=0)
    last_executed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'automation_rules'
        ordering = ['-created_at']


class AutomationLog(BaseModel):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    rule_id = models.UUIDField(db_index=True)
    trigger_event = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    actions_taken = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trigger_event} - {self.status}"

    class Meta:
        db_table = 'automation_logs'
        ordering = ['-executed_at']
