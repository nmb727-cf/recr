import uuid
from django.db import models
from shared.models import BaseModel

class WorkflowProcessInstance(BaseModel):
    PROCESS_STATUS_CHOICES = [
        ('running', 'Running'),
        ('waiting_human', 'Waiting Human'),
        ('waiting_approval', 'Waiting Approval'),
        ('waiting_schedule', 'Waiting Schedule'),
        ('waiting_candidate', 'Waiting Candidate'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    workflow_id = models.UUIDField(db_index=True) # References Workflow model id
    entity_type = models.CharField(max_length=64, db_index=True) # e.g., 'candidate', 'job_application'
    entity_id = models.UUIDField(db_index=True)
    process_status = models.CharField(max_length=32, choices=PROCESS_STATUS_CHOICES, default='running', db_index=True)
    current_stage = models.CharField(max_length=128, blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'workflow_process_instances'
        ordering = ['-started_at']

class WorkflowStageExecution(BaseModel):
    STAGE_TYPE_CHOICES = [
        ('process_stage', 'Process Stage'),
        ('interview_round', 'Interview Round'),
        ('approval_gate', 'Approval Gate'),
        ('wait_state', 'Wait State'),
        ('scheduler', 'Scheduler'),
        ('negotiation', 'Negotiation'),
        ('handoff', 'Handoff'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('waiting', 'Waiting'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    process_instance = models.ForeignKey(WorkflowProcessInstance, on_delete=models.CASCADE, related_name='stages')
    stage_key = models.CharField(max_length=128) # e.g., 'agency_submission', 'interview_round_1'
    stage_type = models.CharField(max_length=32, choices=STAGE_TYPE_CHOICES)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'workflow_stage_executions'
        ordering = ['started_at']

class WorkflowApprovalCheckpoint(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    process_instance = models.ForeignKey(WorkflowProcessInstance, on_delete=models.CASCADE, related_name='approvals')
    stage_execution = models.ForeignKey(WorkflowStageExecution, on_delete=models.CASCADE, related_name='approvals')
    approval_type = models.CharField(max_length=128) # e.g., 'compensation_approval'
    requested_from_user_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'workflow_approval_checkpoints'

class WorkflowSchedulerCheckpoint(BaseModel):
    SCHEDULING_TYPE_CHOICES = [
        ('interviewer', 'Interviewer'),
        ('panel', 'Panel'),
        ('personal_interview', 'Personal Interview'),
        ('manager_meeting', 'Manager Meeting'),
    ]
    TARGET_MODE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('hybrid', 'Hybrid'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('availability_checked', 'Availability Checked'),
        ('slot_found', 'Slot Found'),
        ('booked', 'Booked'),
        ('failed', 'Failed'),
        ('reschedule_required', 'Reschedule Required'),
    ]
    process_instance = models.ForeignKey(WorkflowProcessInstance, on_delete=models.CASCADE, related_name='scheduling_checkpoints')
    stage_execution = models.ForeignKey(WorkflowStageExecution, on_delete=models.CASCADE, related_name='scheduling_checkpoints')
    scheduling_type = models.CharField(max_length=32, choices=SCHEDULING_TYPE_CHOICES)
    target_user_ids = models.JSONField(default=list) # List of UUIDs
    target_mode = models.CharField(max_length=32, choices=TARGET_MODE_CHOICES, default='online')
    availability_payload = models.JSONField(default=dict, blank=True)
    selected_slot = models.JSONField(null=True, blank=True) # {start: ..., end: ...}
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'workflow_scheduler_checkpoints'

class WorkflowNegotiationCheckpoint(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('within_band', 'Within Band'),
        ('approval_required', 'Approval Required'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('exhausted', 'Exhausted'),
    ]
    process_instance = models.ForeignKey(WorkflowProcessInstance, on_delete=models.CASCADE, related_name='negotiations')
    offer_id = models.UUIDField(db_index=True)
    negotiation_round = models.IntegerField(default=1)
    proposed_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    allowed_band_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    allowed_band_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')
    approved_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'workflow_negotiation_checkpoints'

class WorkflowHandoffRecord(BaseModel):
    HANDOFF_TYPE_CHOICES = [
        ('onboarding', 'Onboarding'),
        ('hrms', 'HRMS'),
        ('closure', 'Closure'),
        ('external_webhook', 'External Webhook'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('failed', 'Failed'),
    ]
    process_instance = models.ForeignKey(WorkflowProcessInstance, on_delete=models.CASCADE, related_name='handoffs')
    handoff_type = models.CharField(max_length=32, choices=HANDOFF_TYPE_CHOICES)
    payload = models.JSONField(default=dict)
    destination_system = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'workflow_handoff_records'
