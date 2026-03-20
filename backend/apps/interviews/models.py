import uuid
from django.db import models
from django.utils import timezone


class InterviewTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    interview_type = models.CharField(
        max_length=50,
        choices=[
            ('ai_screening', 'AI Screening'),
            ('one_way_video', 'One-Way Video'),
            ('live_video', 'Live Video'),
            ('panel', 'Panel'),
            ('technical', 'Technical'),
            ('group_discussion', 'Group Discussion'),
            ('psychometric', 'Psychometric'),
            ('case_study', 'Case Study'),
            ('mock', 'Mock'),
        ],
        default='ai_screening'
    )
    duration_minutes = models.IntegerField(default=30)
    instructions = models.TextField(blank=True)
    passing_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=60)
    auto_shortlist_above = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    auto_reject_below = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    anti_cheat_enabled = models.BooleanField(default=True)
    recording_enabled = models.BooleanField(default=True)
    questions = models.JSONField(default=list, blank=True)
    scoring_criteria = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
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
        return self.name

    class Meta:
        db_table = 'interviews_template'


class Interview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    application_id = models.UUIDField(db_index=True)
    candidate_id = models.UUIDField(db_index=True)
    requisition_id = models.UUIDField(db_index=True)
    template_id = models.UUIDField(null=True, blank=True)
    interview_type = models.CharField(
        max_length=50,
        choices=[
            ('ai_screening', 'AI Screening'),
            ('one_way_video', 'One-Way Video'),
            ('live_video', 'Live Video'),
            ('panel', 'Panel'),
            ('technical', 'Technical'),
            ('group_discussion', 'Group Discussion'),
            ('psychometric', 'Psychometric'),
            ('case_study', 'Case Study'),
            ('mock', 'Mock'),
        ],
        default='ai_screening'
    )
    interview_round = models.IntegerField(default=1)
    title = models.CharField(max_length=255, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('scheduled', 'Scheduled'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('no_show', 'No Show'),
            ('rescheduled', 'Rescheduled'),
        ],
        default='scheduled'
    )
    interview_link = models.TextField(blank=True)
    recording_url = models.TextField(blank=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    human_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    recommendation = models.CharField(
        max_length=50,
        choices=[
            ('strongly_recommend', 'Strongly Recommend'),
            ('recommend', 'Recommend'),
            ('neutral', 'Neutral'),
            ('not_recommend', 'Not Recommend'),
            ('reject', 'Reject'),
        ],
        blank=True
    )
    feedback_summary = models.TextField(blank=True)
    anti_cheat_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    anti_cheat_flags = models.JSONField(default=list, blank=True)
    is_cafe_interview = models.BooleanField(default=False)
    cafe_session_id = models.UUIDField(null=True, blank=True)
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
        return f"{self.interview_type} - {self.candidate_id}"

    class Meta:
        db_table = 'interviews_interview'
        ordering = ['-created_at']


class InterviewPanelist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    interview_id = models.UUIDField(db_index=True)
    interviewer_id = models.UUIDField(db_index=True)
    role = models.CharField(
        max_length=50,
        choices=[
            ('lead', 'Lead'),
            ('interviewer', 'Interviewer'),
            ('observer', 'Observer'),
        ],
        default='interviewer'
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    recommendation = models.CharField(max_length=50, blank=True)
    question_scores = models.JSONField(default=list, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    deadline_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return str(self.interviewer_id)

    class Meta:
        db_table = 'interviews_panelist'
        unique_together = ['interview_id', 'interviewer_id']


class InterviewQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    interview_id = models.UUIDField(db_index=True)
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=50,
        choices=[
            ('text', 'Text'),
            ('video', 'Video'),
            ('audio', 'Audio'),
            ('code', 'Code'),
            ('multiple_choice', 'Multiple Choice'),
            ('rating_scale', 'Rating Scale'),
        ],
        default='text'
    )
    options = models.JSONField(default=list, blank=True)
    expected_duration_seconds = models.IntegerField(null=True, blank=True)
    candidate_answer = models.TextField(blank=True)
    candidate_video_url = models.TextField(blank=True)
    ai_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_feedback = models.TextField(blank=True)
    human_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    human_feedback = models.TextField(blank=True)
    order_index = models.IntegerField(default=0)
    answered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.question_text[:50]

    class Meta:
        db_table = 'interviews_question'
        ordering = ['order_index']
