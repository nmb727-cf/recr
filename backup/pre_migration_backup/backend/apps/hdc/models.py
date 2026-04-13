import uuid
from django.db import models
from shared.models import BaseModel

# ─── Hiring Committee ─────────────────────────────────────────────────────────

class HiringCommittee(BaseModel):
    name = models.CharField(max_length=255)
    requisition_id = models.UUIDField(db_index=True)
    candidate_id = models.UUIDField(db_index=True)
    application_id = models.UUIDField(db_index=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('voting', 'Voting'),
            ('split', 'Split'),
            ('escalated', 'Escalated'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft'
    )
    mode = models.CharField(max_length=50, default='Standard')
    quorum_required = models.IntegerField(default=1)
    result = models.CharField(max_length=50, blank=True)
    decision_trail = models.TextField(blank=True)

    class Meta:
        db_table = 'hdc_hiring_committee'

class CommitteeMember(BaseModel):
    committee = models.ForeignKey(HiringCommittee, on_delete=models.CASCADE, related_name='members')
    user_id = models.UUIDField(db_index=True)
    role = models.CharField(max_length=50, default='Reviewer')
    has_voted = models.BooleanField(default=False)
    vote = models.CharField(max_length=50, blank=True)
    review_notes = models.TextField(blank=True)
    voted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'hdc_committee_member'

# ─── Candidate Comparison ─────────────────────────────────────────────────────

class ComparisonSet(BaseModel):
    name = models.CharField(max_length=255)
    requisition_id = models.UUIDField(db_index=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('active', 'Active'),
            ('frozen', 'Frozen'),
            ('archived', 'Archived'),
        ],
        default='active'
    )
    weights_enabled = models.BooleanField(default=False)
    weights_config = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'hdc_comparison_set'

class ComparisonCandidate(BaseModel):
    comparison_set = models.ForeignKey(ComparisonSet, on_delete=models.CASCADE, related_name='candidates')
    candidate_id = models.UUIDField(db_index=True)
    application_id = models.UUIDField(db_index=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    risk_flag = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'hdc_comparison_candidate'

# ─── Decision Approval ────────────────────────────────────────────────────────

class DecisionApproval(BaseModel):
    application_id = models.UUIDField(db_index=True, unique=True)
    requisition_id = models.UUIDField(db_index=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('revoked', 'Revoked'),
        ],
        default='pending'
    )
    approver_id = models.UUIDField(db_index=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)
    is_final = models.BooleanField(default=False)

    class Meta:
        db_table = 'hdc_decision_approval'

# ─── Offer Intelligence & Compensation ────────────────────────────────────────

class OfferRecommendation(BaseModel):
    application_id = models.UUIDField(db_index=True, unique=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('draft', 'Draft'),
            ('scenario_modeling', 'Scenario Modeling'),
            ('recommended', 'Recommended'),
            ('locked', 'Locked'),
        ],
        default='draft'
    )
    selected_scenario_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'hdc_offer_recommendation'

class OfferScenario(BaseModel):
    recommendation = models.ForeignKey(OfferRecommendation, on_delete=models.CASCADE, related_name='scenarios')
    name = models.CharField(max_length=255)
    ctc_amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    market_position = models.CharField(max_length=100, blank=True)
    risk_level = models.CharField(max_length=50, default='Low')
    readiness = models.CharField(max_length=50, default='Draft')
    is_exception = models.BooleanField(default=False)
    components = models.JSONField(default=dict, blank=True) # {base: X, variable: Y, bonus: Z}

    class Meta:
        db_table = 'hdc_offer_scenario'

# ─── Negotiation ──────────────────────────────────────────────────────────────

class NegotiationCase(BaseModel):
    application_id = models.UUIDField(db_index=True, unique=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('active', 'Active'),
            ('agreed', 'Agreed'),
            ('failed', 'Failed'),
            ('paused', 'Paused'),
            ('handed_off', 'Handed Off'),
            ('closed', 'Closed'),
        ],
        default='active'
    )
    current_round = models.IntegerField(default=0)
    candidate_ask = models.TextField(blank=True)
    company_counter = models.TextField(blank=True)

    class Meta:
        db_table = 'hdc_negotiation_case'

class NegotiationRound(BaseModel):
    negotiation_case = models.ForeignKey(NegotiationCase, on_delete=models.CASCADE, related_name='rounds')
    round_number = models.IntegerField()
    candidate_ask_payload = models.JSONField(default=dict, blank=True)
    company_counter_payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=50, default='open')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'hdc_negotiation_round'

# ─── Final Offer Release ──────────────────────────────────────────────────────

class OfferReleasePacket(BaseModel):
    application_id = models.UUIDField(db_index=True, unique=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('draft', 'Draft'),
            ('assembled', 'Assembled'),
            ('frozen', 'Frozen'),
            ('released', 'Released'),
            ('accepted', 'Accepted'),
            ('declined', 'Declined'),
            ('query', 'Query Raised'),
            ('scheduled', 'Scheduled'),
            ('recalled', 'Recalled'),
            ('rework', 'Rework'),
        ],
        default='draft'
    )
    packet_data = models.JSONField(default=dict, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    released_by = models.UUIDField(null=True, blank=True)
    candidate_response = models.CharField(max_length=50, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'hdc_offer_release_packet'

# ─── Joining Tracking ─────────────────────────────────────────────────────────

class JoiningCase(BaseModel):
    ONBOARDING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('documents_pending', 'Documents Pending'),
        ('completed', 'Completed'),
        ('handed_off', 'Handed Off'),
        # Legacy statuses kept for backward compatibility.
        ('joined', 'Joined'),
        ('postponed', 'Postponed'),
        ('withdrawn', 'Offer Withdrawn'),
        ('no_show', 'No Show'),
    ]

    application_id = models.UUIDField(db_index=True, unique=True)
    candidate_id = models.UUIDField(db_index=True, null=True, blank=True)
    job_id = models.UUIDField(db_index=True, null=True, blank=True)
    offer_id = models.UUIDField(db_index=True, null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=ONBOARDING_STATUS_CHOICES,
        default='pending'
    )
    joining_date = models.DateField(null=True, blank=True)
    actual_joining_date = models.DateField(null=True, blank=True)
    assigned_hr_id = models.UUIDField(db_index=True, null=True, blank=True)
    handoff_notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'hdc_joining_case'

# ─── Audit / History ─────────────────────────────────────────────────────────

class HDCAuditLog(BaseModel):
    application_id = models.UUIDField(db_index=True)
    requisition_id = models.UUIDField(db_index=True)
    action_type = models.CharField(max_length=100)  # e.g., 'approve_for_offer', 'reject_candidate'
    previous_status = models.CharField(max_length=50, blank=True)
    new_status = models.CharField(max_length=50, blank=True)
    performed_by_id = models.UUIDField(db_index=True)
    comments = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'hdc_audit_log'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action_type} - {self.application_id}"
