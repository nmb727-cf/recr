import uuid
from django.db import models
from django.conf import settings
from shared.models import BaseModel


class AgencyCandidatePipelineRegistry(BaseModel):
    """
    Registry for agency candidate pipeline stages.
    Registry-driven, tenant-specific or system-wide.
    """
    stage_key = models.CharField(max_length=50, db_index=True)
    stage_label = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'agency_candidate_pipeline_registry'
        unique_together = ['tenant_id', 'stage_key']
        ordering = ['order']

    def __str__(self):
        return f"{self.stage_label} ({self.stage_key})"


class AgencyCandidate(BaseModel):
    """
    The main overlay entity for an agency candidate.
    Links to the global Candidate entity.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('dormant', 'Dormant'),
        ('placed', 'Placed'),
        ('blacklisted', 'Blacklisted'),
        ('archived', 'Archived'),
    ]

    AVAILABILITY_CHOICES = [
        ('immediate', 'Immediate'),
        ('15_days', '15 Days'),
        ('30_days', '30 Days'),
        ('60_days', '60 Days'),
        ('not_available', 'Not Available'),
    ]

    SOURCE_CHOICES = [
        ('linkedin', 'LinkedIn'),
        ('job_portal', 'Job Portal'),
        ('referral', 'Referral'),
        ('internal_database', 'Internal Database'),
        ('bulk_import', 'Bulk Import'),
        ('manual', 'Manual'),
        ('other', 'Other'),
    ]

    candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='agency_overlays'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='owned_agency_candidates'
    )
    pipeline_stage = models.ForeignKey(
        AgencyCandidatePipelineRegistry,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='candidates'
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    availability = models.CharField(
        max_length=30,
        choices=AVAILABILITY_CHOICES,
        default='immediate',
        db_index=True
    )
    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default='manual',
        db_index=True
    )
    source_details = models.TextField(blank=True)
    
    expected_salary_min = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    expected_salary_max = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(max_length=10, default='INR')
    
    last_contacted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    tags_list = models.JSONField(default=list, blank=True) # For quick access
    is_hotlisted = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'agency_candidates'
        unique_together = ['tenant_id', 'candidate']
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'owner']),
            models.Index(fields=['tenant_id', 'pipeline_stage']),
        ]

    def __str__(self):
        return f"Agency Overlay: {self.candidate.full_name} ({self.tenant_id})"


class AgencyCandidateTag(BaseModel):
    """
    Structured tags for agency candidates.
    """
    agency_candidate = models.ForeignKey(
        AgencyCandidate,
        on_delete=models.CASCADE,
        related_name='tags'
    )
    tag_name = models.CharField(max_length=100, db_index=True)

    class Meta:
        db_table = 'agency_candidate_tags'
        unique_together = ['tenant_id', 'agency_candidate', 'tag_name']

    def __str__(self):
        return self.tag_name


class AgencyCandidateNote(BaseModel):
    """
    Nurture notes and activity logs for candidates.
    """
    NOTE_TYPE_CHOICES = [
        ('general', 'General'),
        ('call_log', 'Call Log'),
        ('interview_feedback', 'Interview Feedback'),
        ('submission_note', 'Submission Note'),
        ('follow_up', 'Follow-up'),
        ('internal', 'Internal Only'),
    ]

    agency_candidate = models.ForeignKey(
        AgencyCandidate,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    note_text = models.TextField()
    note_type = models.CharField(
        max_length=50,
        choices=NOTE_TYPE_CHOICES,
        default='general'
    )

    class Meta:
        db_table = 'agency_candidate_notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.agency_candidate}"


class AgencyCandidateActivity(BaseModel):
    """
    Audit log for agency-specific candidate activities.
    """
    ACTIVITY_TYPE_CHOICES = [
        ('created', 'Candidate Created'),
        ('status_changed', 'Status Changed'),
        ('pipeline_stage_changed', 'Pipeline Stage Changed'),
        ('owner_assigned', 'Owner Assigned'),
        ('owner_transferred', 'Owner Transferred'),
        ('submitted_to_client', 'Submitted to Client'),
        ('resume_updated', 'Resume Updated'),
        ('note_added', 'Note Added'),
        ('hotlisted', 'Added to Hotlist'),
    ]

    agency_candidate = models.ForeignKey(
        AgencyCandidate,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(max_length=100, choices=ACTIVITY_TYPE_CHOICES)
    actor_id = models.UUIDField(null=True, blank=True) # User ID who performed the action
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'agency_candidate_activity'
        ordering = ['-created_at']


class AgencyCandidateOwnership(BaseModel):
    """
    Tracks history of recruiter ownership.
    """
    agency_candidate = models.ForeignKey(
        AgencyCandidate,
        on_delete=models.CASCADE,
        related_name='ownership_history'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agency_candidate_ownerships'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True, db_index=True)
    ownership_period_days = models.IntegerField(null=True, blank=True) # For expiration logic

    class Meta:
        db_table = 'agency_candidate_ownership'


class AgencyCandidateHotlist(BaseModel):
    """
    Group candidates into custom hotlists.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_private = models.BooleanField(default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hotlists'
    )

    class Meta:
        db_table = 'agency_candidate_hotlists'

    def __str__(self):
        return self.name


class AgencyCandidateHotlistMember(models.Model):
    """
    Many-to-many relationship for hotlists.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotlist = models.ForeignKey(
        AgencyCandidateHotlist,
        on_delete=models.CASCADE,
        related_name='members'
    )
    agency_candidate = models.ForeignKey(
        AgencyCandidate,
        on_delete=models.CASCADE,
        related_name='hotlist_memberships'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agency_candidate_hotlist_members'
        unique_together = ['hotlist', 'agency_candidate']


class AgencyCandidateResumeVersion(BaseModel):
    """
    Resume management for agency candidates.
    Supports versions and formatted resumes.
    """
    agency_candidate = models.ForeignKey(
        AgencyCandidate,
        on_delete=models.CASCADE,
        related_name='resumes'
    )
    resume_url = models.TextField()
    version_name = models.CharField(max_length=255, blank=True)
    is_formatted = models.BooleanField(default=False) # Formatted by recruiter
    recruiter_summary = models.TextField(blank=True) # Summary added by recruiter for client

    class Meta:
        db_table = 'agency_candidate_resume_versions'


class AgencyCandidateSubmission(BaseModel):
    """
    Tracks candidate submissions to clients.
    """
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('client_review', 'Client Review'),
        ('shortlisted', 'Shortlisted'),
        ('interviewing', 'Interviewing'),
        ('rejected', 'Rejected'),
        ('offered', 'Offered'),
        ('placed', 'Placed'),
        ('withdrawn', 'Withdrawn'),
    ]

    agency_candidate = models.ForeignKey(
        AgencyCandidate,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    client_tenant_id = models.UUIDField(db_index=True)
    job_id = models.UUIDField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='submitted',
        db_index=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    feedback_from_client = models.TextField(blank=True)

    class Meta:
        db_table = 'agency_candidate_submissions'
