from shared.models import BaseModel
from django.db import models
import uuid

class InterviewTemplate(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    interview_type = models.CharField(
        max_length=50,
        choices=[
            ('ai_screening', 'AI Screening'), ('one_way_video', 'One-Way Video'),
            ('live_video', 'Live Video'), ('panel', 'Panel'), ('technical', 'Technical'),
            ('group_discussion', 'Group Discussion'), ('psychometric', 'Psychometric'),
            ('case_study', 'Case Study'), ('mock', 'Mock')
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

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'interviews_template'


class Interview(BaseModel):
    application_id = models.UUIDField(db_index=True)
    candidate_id = models.UUIDField(db_index=True)
    job_id = models.UUIDField(db_index=True)
    template_id = models.UUIDField(null=True, blank=True)
    interview_type = models.CharField(
        max_length=50,
        choices=[
            ('ai_screening', 'AI Screening'), ('one_way_video', 'One-Way Video'),
            ('live_video', 'Live Video'), ('panel', 'Panel'), ('technical', 'Technical'),
            ('group_discussion', 'Group Discussion'), ('psychometric', 'Psychometric'),
            ('case_study', 'Case Study'), ('mock', 'Mock')
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
            ('scheduled', 'Scheduled'), ('in_progress', 'In Progress'),
            ('completed', 'Completed'), ('cancelled', 'Cancelled'),
            ('no_show', 'No Show'), ('rescheduled', 'Rescheduled')
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
            ('strongly_recommend', 'Strongly Recommend'), ('recommend', 'Recommend'),
            ('neutral', 'Neutral'), ('not_recommend', 'Not Recommend'), ('reject', 'Reject')
        ],
        blank=True
    )
    feedback_summary = models.TextField(blank=True)
    anti_cheat_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    anti_cheat_flags = models.JSONField(default=list, blank=True)
    is_cafe_interview = models.BooleanField(default=False)
    cafe_session_id = models.UUIDField(null=True, blank=True)
    product = models.CharField(
        max_length=20,
        choices=[
            ('ats', 'ATS'), ('cafe', 'Cafe'), ('marketplace', 'Marketplace')
        ],
        default='ats'
    )

    def __str__(self):
        return f"{self.interview_type} - {self.candidate_id}"

    class Meta:
        db_table = 'interviews_interview'
        ordering = ['-created_at']


class InterviewPanelist(BaseModel):
    interview_id = models.UUIDField(db_index=True)
    interviewer_id = models.UUIDField(db_index=True)
    role = models.CharField(
        max_length=50,
        choices=[
            ('lead', 'Lead'), ('interviewer', 'Interviewer'), ('observer', 'Observer')
        ],
        default='interviewer'
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    recommendation = models.CharField(max_length=50, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    deadline_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.interviewer_id)

    class Meta:
        db_table = 'interviews_panelist'


class InterviewQuestion(BaseModel):
    interview_id = models.UUIDField(db_index=True)
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=50,
        choices=[
            ('text', 'Text'), ('video', 'Video'), ('audio', 'Audio'),
            ('code', 'Code'), ('multiple_choice', 'Multiple Choice'),
            ('rating_scale', 'Rating Scale')
        ],
        default='text'
    )
    expected_duration_seconds = models.IntegerField(null=True, blank=True)
    candidate_answer = models.TextField(blank=True)
    candidate_video_url = models.TextField(blank=True)
    ai_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_feedback = models.TextField(blank=True)
    human_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    human_feedback = models.TextField(blank=True)
    order_index = models.IntegerField(default=0)

    def __str__(self):
        return self.question_text[:50]

    class Meta:
        db_table = 'interviews_question'
        ordering = ['order_index']
