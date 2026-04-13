from django.db import models
from shared.models import BaseModel
from .workflow import AgencyWorkflowDefinition

class AgencyWorkflowProcessInstance(BaseModel):
    PROCESS_STATUS_CHOICES = [
        ('running', 'Running'),
        ('waiting_internal', 'Waiting Internal'),
        ('waiting_client', 'Waiting Client'),
        ('waiting_candidate', 'Waiting Candidate'),
        ('waiting_interview', 'Waiting Interview'),
        ('waiting_offer', 'Waiting Offer'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    workflow = models.ForeignKey(AgencyWorkflowDefinition, on_delete=models.CASCADE, related_name='process_instances')
    entity_type = models.CharField(max_length=64, db_index=True)
    entity_id = models.UUIDField(db_index=True)
    candidate_id = models.UUIDField(null=True, blank=True, db_index=True)
    client_id = models.UUIDField(null=True, blank=True, db_index=True)
    job_id = models.UUIDField(null=True, blank=True, db_index=True)
    assigned_recruiter_id = models.UUIDField(null=True, blank=True, db_index=True)
    process_status = models.CharField(max_length=32, choices=PROCESS_STATUS_CHOICES, default='running')
    current_stage = models.CharField(max_length=128, blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'agency_workflow_process_instances'
        ordering = ['-started_at']

class AgencyWorkflowStageExecution(BaseModel):
    STAGE_TYPE_CHOICES = [
        ('talent_pool_stage', 'Talent Pool Stage'),
        ('recruiter_review', 'Recruiter Review'),
        ('internal_approval', 'Internal Approval'),
        ('submission_stage', 'Submission Stage'),
        ('client_wait', 'Client Wait'),
        ('interview_coordination', 'Interview Coordination'),
        ('offer_stage', 'Offer Stage'),
        ('placement_stage', 'Placement Stage'),
        ('guarantee_stage', 'Guarantee Stage'),
        ('closure_stage', 'Closure Stage'),
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
    process_instance = models.ForeignKey(AgencyWorkflowProcessInstance, on_delete=models.CASCADE, related_name='stages')
    stage_key = models.CharField(max_length=128)
    stage_type = models.CharField(max_length=64, choices=STAGE_TYPE_CHOICES)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'agency_workflow_stage_executions'
        ordering = ['started_at']

class AgencyInternalApprovalCheckpoint(BaseModel):
    APPROVAL_TYPE_CHOICES = [
        ('recruiter_manager_review', 'Recruiter Manager Review'),
        ('submission_approval', 'Submission Approval'),
        ('salary_exception_approval', 'Salary Exception Approval'),
        ('client_escalation_approval', 'Client Escalation Approval'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    process_instance = models.ForeignKey(AgencyWorkflowProcessInstance, on_delete=models.CASCADE, related_name='internal_approvals')
    stage_execution = models.ForeignKey(AgencyWorkflowStageExecution, on_delete=models.CASCADE, related_name='internal_approvals')
    approval_type = models.CharField(max_length=64, choices=APPROVAL_TYPE_CHOICES)
    requested_from_user_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'agency_internal_approval_checkpoints'

class AgencyClientResponseCheckpoint(BaseModel):
    RESPONSE_TYPE_CHOICES = [
        ('submission_feedback', 'Submission Feedback'),
        ('shortlist_confirmation', 'Shortlist Confirmation'),
        ('interview_confirmation', 'Interview Confirmation'),
        ('offer_update', 'Offer Update'),
        ('joining_confirmation', 'Joining Confirmation'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reminded', 'Reminded'),
        ('overdue', 'Overdue'),
        ('escalated', 'Escalated'),
        ('responded', 'Responded'),
        ('expired', 'Expired'),
    ]
    process_instance = models.ForeignKey(AgencyWorkflowProcessInstance, on_delete=models.CASCADE, related_name='client_responses')
    stage_execution = models.ForeignKey(AgencyWorkflowStageExecution, on_delete=models.CASCADE, related_name='client_responses')
    response_type = models.CharField(max_length=64, choices=RESPONSE_TYPE_CHOICES)
    due_at = models.DateTimeField(null=True, blank=True)
    last_followup_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'agency_client_response_checkpoints'

class AgencyOfferProgressCheckpoint(BaseModel):
    OFFER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('discussing', 'Discussing'),
        ('countered', 'Countered'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('exhausted', 'Exhausted'),
        ('closed', 'Closed'),
    ]
    process_instance = models.ForeignKey(AgencyWorkflowProcessInstance, on_delete=models.CASCADE, related_name='offer_checkpoints')
    candidate_id = models.UUIDField(db_index=True)
    client_id = models.UUIDField(db_index=True)
    job_id = models.UUIDField(null=True, blank=True, db_index=True)
    offer_status = models.CharField(max_length=32, choices=OFFER_STATUS_CHOICES, default='pending')
    proposed_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    accepted_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    negotiation_round = models.IntegerField(default=1)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='active')

    class Meta:
        db_table = 'agency_offer_progress_checkpoints'

class AgencyPlacementGuaranteeRecord(BaseModel):
    PLACEMENT_STATUS_CHOICES = [
        ('joining_pending', 'Joining Pending'),
        ('joined', 'Joined'),
        ('dropped', 'Dropped'),
        ('closed', 'Closed'),
    ]
    GUARANTEE_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('active', 'Active'),
        ('breached', 'Breached'),
        ('completed', 'Completed'),
    ]
    process_instance = models.ForeignKey(AgencyWorkflowProcessInstance, on_delete=models.CASCADE, related_name='placement_guarantees')
    candidate_id = models.UUIDField(db_index=True)
    client_id = models.UUIDField(db_index=True)
    job_id = models.UUIDField(null=True, blank=True, db_index=True)
    placement_status = models.CharField(max_length=32, choices=PLACEMENT_STATUS_CHOICES, default='joining_pending')
    joined_at = models.DateTimeField(null=True, blank=True)
    guarantee_start_date = models.DateField(null=True, blank=True)
    guarantee_end_date = models.DateField(null=True, blank=True)
    guarantee_status = models.CharField(max_length=32, choices=GUARANTEE_STATUS_CHOICES, default='not_started')

    class Meta:
        db_table = 'agency_placement_guarantee_records'
