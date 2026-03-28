import uuid
from django.db import models
from django.utils import timezone


# ─── Choices ──────────────────────────────────────────────────────────────────

INTERVIEW_STATUS = [
    ('scheduled',   'Scheduled'),
    ('in_progress', 'In Progress'),
    ('completed',   'Completed'),
    ('cancelled',   'Cancelled'),
    ('no_show',     'No Show'),
    ('rescheduled', 'Rescheduled'),
]

DECISION_CHOICES = [
    ('hire',       'Hire'),
    ('reject',     'Reject'),
    ('hold',       'Hold'),
    ('next_round', 'Next Round'),
    ('manual_review', 'Manual Review'),
    ('assignment', 'Assignment'),
    ('panel_required', 'Panel Required'),
    ('escalate', 'Escalate'),
]

DECISION_SOURCE_CHOICES = [
    ('manual', 'Manual'),
    ('scorecard', 'Scorecard'),
    ('interviewer_feedback', 'Interviewer Feedback'),
    ('prequalification', 'Prequalification'),
    ('skill_matching', 'Skill Matching'),
    ('automation_rules', 'Automation Rules'),
]

DECISION_MODE_CHOICES = [
    ('manual', 'Manual'),
    ('auto', 'Auto'),
    ('conditional', 'Conditional'),
]

SCORING_TYPES = [
    ('numeric',   'Numeric (0–100)'),
    ('pass_fail', 'Pass / Fail'),
    ('criteria',  'Criteria-Based'),
]

SCORECARD_RATING_TYPES = [
    ('scale_1_5',   '1-5 Scale'),
    ('yes_no',      'Yes / No'),
    ('pass_fail',   'Pass / Fail'),
    ('custom_scale','Custom Scale'),
]

QUESTION_BANK_TYPES = [
    ('text', 'Text Question'),
    ('multiple_choice', 'Multiple Choice'),
    ('multi_select', 'Multi Select'),
    ('coding', 'Coding Question (Shell)'),
    ('file_upload', 'File Upload'),
    ('video', 'Video Question (Shell)'),
    ('rating', 'Rating Question'),
    ('yes_no', 'Yes / No'),
]

QUESTION_DIFFICULTY = [
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
]

QUESTION_BANK_SCOPE = [
    ('global', 'Global'),
    ('tenant', 'Tenant'),
    ('template', 'Template'),
]

QUESTION_ATTACH_TYPES = [
    ('template', 'Template'),
    ('interview_type', 'Interview Type'),
    ('assessment', 'Assessment'),
]

PANELIST_ROLES = [
    ('lead',        'Lead'),
    ('panelist',    'Panelist'),
    ('observer',    'Observer'),
    ('note_taker',  'Note Taker'),
]

RECOMMENDATION_CHOICES = [
    ('strongly_recommend', 'Strongly Recommend'),
    ('recommend',          'Recommend'),
    ('neutral',            'Neutral'),
    ('not_recommend',      'Not Recommend'),
    ('reject',             'Reject'),
]

INTERVIEW_EXECUTION_MODES = [
    ('native', 'Native'),
    ('third_party', 'Third Party'),
    ('external', 'External'),
    ('manual', 'Manual'),
    ('async', 'Async'),
]

INTERVIEW_INTEGRATION_EXECUTION_MODES = [
    ('native', 'Native'),
    ('third_party', 'Third Party'),
    ('external_manual', 'External Manual'),
]

INTEGRATION_PROVIDER_TYPES = [
    ('meeting', 'Meeting'),
    ('calendar', 'Calendar'),
    ('external', 'External'),
]

INTEGRATION_PROVIDER_CODES = [
    ('google_meet', 'Google Meet'),
    ('zoom', 'Zoom'),
    ('microsoft_teams', 'Microsoft Teams'),
    ('google_calendar', 'Google Calendar'),
    ('outlook_calendar', 'Outlook Calendar'),
    ('apple_calendar', 'Apple Calendar'),
    ('ics_external', 'ICS External'),
]

INTERVIEW_TYPE_REGISTRY_DEFAULTS = [
    {'code': 'recruiter_screening', 'name': 'Recruiter Screening', 'description': 'Initial recruiter-driven qualification round.', 'execution_mode': 'manual'},
    {'code': 'ai_screening', 'name': 'AI Screening', 'description': 'Automated AI-based screening flow.', 'execution_mode': 'native'},
    {'code': 'one_way_video', 'name': 'One Way Video', 'description': 'Candidate submits prerecorded responses.', 'execution_mode': 'native'},
    {'code': 'phone_interview', 'name': 'Phone Interview', 'description': 'Phone-based interview round.', 'execution_mode': 'manual'},
    {'code': 'async_text', 'name': 'Async Text', 'description': 'Asynchronous text-based Q&A interview.', 'execution_mode': 'async'},
    {'code': 'technical_interview', 'name': 'Technical Interview', 'description': 'General technical depth assessment.', 'execution_mode': 'manual'},
    {'code': 'coding_interview', 'name': 'Coding Interview', 'description': 'Hands-on coding evaluation.', 'execution_mode': 'native'},
    {'code': 'system_design', 'name': 'System Design', 'description': 'Architecture and design interview.', 'execution_mode': 'manual'},
    {'code': 'take_home_assignment', 'name': 'Take Home Assignment', 'description': 'Offline assignment based evaluation.', 'execution_mode': 'async'},
    {'code': 'debugging_interview', 'name': 'Debugging Interview', 'description': 'Candidate debugging capability test.', 'execution_mode': 'manual'},
    {'code': 'whiteboard', 'name': 'Whiteboard Interview', 'description': 'Whiteboard problem-solving round.', 'execution_mode': 'manual'},
    {'code': 'technical_panel', 'name': 'Technical Panel', 'description': 'Panel interview with technical stakeholders.', 'execution_mode': 'manual'},
    {'code': 'behavioral', 'name': 'Behavioral Interview', 'description': 'Behavior and competency assessment.', 'execution_mode': 'manual'},
    {'code': 'culture_fit', 'name': 'Culture Fit', 'description': 'Values and culture alignment check.', 'execution_mode': 'manual'},
    {'code': 'hr_interview', 'name': 'HR Interview', 'description': 'HR process and policy discussion round.', 'execution_mode': 'manual'},
    {'code': 'leadership', 'name': 'Leadership Interview', 'description': 'Leadership capability evaluation.', 'execution_mode': 'manual'},
    {'code': 'executive', 'name': 'Executive Interview', 'description': 'Executive leadership round.', 'execution_mode': 'manual'},
    {'code': 'hiring_manager', 'name': 'Hiring Manager Interview', 'description': 'Role and team fit with hiring manager.', 'execution_mode': 'manual'},
    {'code': 'panel', 'name': 'Panel Interview', 'description': 'Multi-interviewer panel evaluation.', 'execution_mode': 'manual'},
    {'code': 'sequential', 'name': 'Sequential Interview', 'description': 'Back-to-back interview sequence.', 'execution_mode': 'manual'},
    {'code': 'stakeholder', 'name': 'Stakeholder Interview', 'description': 'Cross-functional stakeholder round.', 'execution_mode': 'manual'},
    {'code': 'bar_raiser', 'name': 'Bar Raiser', 'description': 'Independent quality benchmark interview.', 'execution_mode': 'manual'},
    {'code': 'final_round', 'name': 'Final Round', 'description': 'Final decision-making interview round.', 'execution_mode': 'manual'},
    {'code': 'mcq_assessment', 'name': 'MCQ Assessment', 'description': 'Multiple-choice assessment.', 'execution_mode': 'native'},
    {'code': 'aptitude', 'name': 'Aptitude Assessment', 'description': 'Aptitude test round.', 'execution_mode': 'native'},
    {'code': 'psychometric', 'name': 'Psychometric Assessment', 'description': 'Psychometric fit evaluation.', 'execution_mode': 'third_party'},
    {'code': 'cognitive', 'name': 'Cognitive Assessment', 'description': 'Cognitive skills measurement.', 'execution_mode': 'third_party'},
    {'code': 'language', 'name': 'Language Assessment', 'description': 'Language proficiency evaluation.', 'execution_mode': 'native'},
    {'code': 'case_study', 'name': 'Case Study', 'description': 'Case-solving interview format.', 'execution_mode': 'manual'},
    {'code': 'role_play', 'name': 'Role Play', 'description': 'Scenario-based role play assessment.', 'execution_mode': 'manual'},
    {'code': 'work_sample', 'name': 'Work Sample', 'description': 'Real-work sample based assessment.', 'execution_mode': 'external'},
    {'code': 'presentation', 'name': 'Presentation Round', 'description': 'Presentation and communication round.', 'execution_mode': 'manual'},
    {'code': 'portfolio_review', 'name': 'Portfolio Review', 'description': 'Portfolio and project review round.', 'execution_mode': 'manual'},
    {'code': 'group_discussion', 'name': 'Group Discussion', 'description': 'Group dynamics and communication round.', 'execution_mode': 'manual'},
    {'code': 'assessment_center', 'name': 'Assessment Center', 'description': 'Composite multi-exercise assessment.', 'execution_mode': 'third_party'},
    {'code': 'mock', 'name': 'Mock Interview', 'description': 'Practice/mock interview session.', 'execution_mode': 'manual'},
    {'code': 'campus', 'name': 'Campus Interview', 'description': 'Campus hiring interview format.', 'execution_mode': 'manual'},
    {'code': 'walkin', 'name': 'Walk-in Interview', 'description': 'Walk-in hiring interview flow.', 'execution_mode': 'manual'},
    {'code': 'interview_cafe', 'name': 'Interview Cafe', 'description': 'Interview cafe style execution.', 'execution_mode': 'native'},
    {'code': 'live_video', 'name': 'Live Video Interview', 'description': 'Synchronous live video interview.', 'execution_mode': 'native'},
]

INTERVIEW_TYPE_CODES = [
    ('technical', 'Technical'),
    *[(row['code'], row['name']) for row in INTERVIEW_TYPE_REGISTRY_DEFAULTS],
]

AVAILABILITY_MODES = [
    ('system', 'System Availability'),
    ('calendar', 'Calendar Based Availability'),
    ('manual', 'Manual Scheduling'),
    ('candidate_self', 'Candidate Self Scheduling'),
]

CALENDAR_PROVIDERS = [
    ('google', 'Google Calendar'),
    ('outlook', 'Outlook Calendar'),
    ('apple', 'Apple Calendar'),
    ('ics', 'ICS Feed'),
]


def default_working_hours():
    return {
        'mon': {'enabled': True, 'start': '09:00', 'end': '18:00'},
        'tue': {'enabled': True, 'start': '09:00', 'end': '18:00'},
        'wed': {'enabled': True, 'start': '09:00', 'end': '18:00'},
        'thu': {'enabled': True, 'start': '09:00', 'end': '18:00'},
        'fri': {'enabled': True, 'start': '09:00', 'end': '18:00'},
        'sat': {'enabled': False, 'start': '09:00', 'end': '18:00'},
        'sun': {'enabled': False, 'start': '09:00', 'end': '18:00'},
    }


# ─── InterviewType ─────────────────────────────────────────────────────────────

class InterviewType(models.Model):
    """
    Catalog of interview formats (AI Screening, Panel, Technical, etc.).
    System-level: no tenant_id — shared across all tenants.
    Tenants may activate/deactivate types via InterviewTemplate.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=255)
    code        = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    execution_mode = models.CharField(max_length=20, choices=INTERVIEW_EXECUTION_MODES, default='native')
    configurable = models.BooleanField(default=True)
    type_configuration = models.JSONField(default=dict, blank=True)
    is_active   = models.BooleanField(default=True, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    created_by  = models.UUIDField(null=True, blank=True)
    is_deleted  = models.BooleanField(default=False, db_index=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)
    metadata    = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'interviews_type'
        ordering = ['name']


# ─── InterviewTemplate ─────────────────────────────────────────────────────────

class InterviewTemplate(models.Model):
    """
    Reusable interview configuration owned by a tenant.
    Defines duration, scoring approach, anti-cheat settings, and the question bank.
    """
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id           = models.UUIDField(db_index=True)
    name                = models.CharField(max_length=255)
    description         = models.TextField(blank=True)
    # Legacy CharField kept for backward compat; prefer type FK for new code.
    interview_type      = models.CharField(max_length=50, choices=INTERVIEW_TYPE_CODES, default='ai_screening')
    # FK to the InterviewType catalog (nullable for templates predating the catalog).
    type                = models.ForeignKey(
        InterviewType,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='templates',
        db_column='type_id',
    )
    duration_minutes    = models.IntegerField(default=30)
    instructions        = models.TextField(blank=True)
    scoring_type        = models.CharField(max_length=20, choices=SCORING_TYPES, default='numeric')
    passing_threshold   = models.DecimalField(max_digits=5, decimal_places=2, default=60)
    auto_shortlist_above = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    auto_reject_below   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    anti_cheat_enabled  = models.BooleanField(default=True)
    recording_enabled   = models.BooleanField(default=True)
    questions           = models.JSONField(default=list, blank=True)
    scoring_criteria    = models.JSONField(default=dict, blank=True)
    is_active           = models.BooleanField(default=True, db_index=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)
    created_by          = models.UUIDField(null=True, blank=True)
    is_deleted          = models.BooleanField(default=False, db_index=True)
    deleted_at          = models.DateTimeField(null=True, blank=True)
    metadata            = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'interviews_template'


# ─── InterviewScorecardTemplate ───────────────────────────────────────────────

class InterviewScorecardTemplate(models.Model):
    """
    Tenant-owned scorecard template mapped to an interview type.
    Attributes are stored as child rows in InterviewScorecardAttribute.
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id      = models.UUIDField(db_index=True)
    name           = models.CharField(max_length=255)
    description    = models.TextField(blank=True)
    interview_type = models.CharField(max_length=50, choices=INTERVIEW_TYPE_CODES, default='ai_screening')
    is_active      = models.BooleanField(default=True, db_index=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    created_by     = models.UUIDField(null=True, blank=True)
    is_deleted     = models.BooleanField(default=False, db_index=True)
    deleted_at     = models.DateTimeField(null=True, blank=True)
    metadata       = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'interviews_scorecard_template'
        ordering = ['-created_at']


class InterviewScorecardAttribute(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id       = models.UUIDField(db_index=True)
    scorecard       = models.ForeignKey(
        InterviewScorecardTemplate,
        on_delete=models.CASCADE,
        related_name='attributes',
    )
    attribute_name  = models.CharField(max_length=255)
    weight          = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    rating_type     = models.CharField(max_length=20, choices=SCORECARD_RATING_TYPES, default='scale_1_5')
    required        = models.BooleanField(default=True)
    custom_scale    = models.JSONField(default=list, blank=True)
    order_index     = models.IntegerField(default=0)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'interviews_scorecard_attribute'
        ordering = ['order_index', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['scorecard', 'attribute_name'],
                name='uniq_scorecard_attribute_name',
            ),
        ]

    def __str__(self):
        return f"{self.attribute_name} ({self.scorecard_id})"


# ─── Interview ─────────────────────────────────────────────────────────────────

class Interview(models.Model):
    """
    A single interview session tied to a candidate application.
    Supports human-panel, AI-screening, and hybrid flows.
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id       = models.UUIDField(db_index=True)
    application_id  = models.UUIDField(db_index=True)
    candidate_id    = models.UUIDField(db_index=True)
    requisition_id  = models.UUIDField(db_index=True)
    template_id     = models.UUIDField(null=True, blank=True)
    scorecard_template_id = models.UUIDField(null=True, blank=True, db_index=True)
    interview_type  = models.CharField(max_length=50, choices=INTERVIEW_TYPE_CODES, default='ai_screening')
    interview_round = models.IntegerField(default=1)
    title           = models.CharField(max_length=255, blank=True)
    scheduled_at    = models.DateTimeField(null=True, blank=True)
    started_at      = models.DateTimeField(null=True, blank=True)
    completed_at    = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    status          = models.CharField(max_length=50, choices=INTERVIEW_STATUS, default='scheduled', db_index=True)
    execution_mode  = models.CharField(
        max_length=30,
        choices=INTERVIEW_INTEGRATION_EXECUTION_MODES,
        default='native',
        db_index=True,
    )
    execution_provider_code = models.CharField(max_length=64, blank=True, db_index=True)
    interview_link  = models.TextField(blank=True)
    meeting_link    = models.TextField(blank=True)
    meeting_provider_code = models.CharField(max_length=64, blank=True)
    external_interview_link = models.TextField(blank=True)
    recording_url   = models.TextField(blank=True)
    overall_score   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_score        = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    human_score     = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    recommendation  = models.CharField(max_length=50, choices=RECOMMENDATION_CHOICES, blank=True)
    feedback_summary = models.TextField(blank=True)
    anti_cheat_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    anti_cheat_flags = models.JSONField(default=list, blank=True)
    is_cafe_interview = models.BooleanField(default=False)
    cafe_session_id  = models.UUIDField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    created_by      = models.UUIDField(null=True, blank=True)
    is_deleted      = models.BooleanField(default=False, db_index=True)
    deleted_at      = models.DateTimeField(null=True, blank=True)
    metadata        = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.interview_type} – {self.candidate_id}"

    class Meta:
        db_table = 'interviews_interview'
        ordering = ['-created_at']


# ─── InterviewPanelist ─────────────────────────────────────────────────────────

class InterviewPanelist(models.Model):
    """
    Links a user (interviewer) to an Interview session with a defined role.
    Stores per-panelist scoring and inline feedback (quick entry path).
    For the formal structured feedback record, see InterviewFeedback.
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id      = models.UUIDField(db_index=True)
    interview_id   = models.UUIDField(db_index=True)
    interviewer_id = models.UUIDField(db_index=True)
    role           = models.CharField(max_length=50, choices=PANELIST_ROLES, default='panelist')
    score          = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback       = models.TextField(blank=True)
    recommendation = models.CharField(max_length=50, blank=True)
    question_scores = models.JSONField(default=list, blank=True)
    submitted_at   = models.DateTimeField(null=True, blank=True)
    deadline_at    = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    metadata       = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return str(self.interviewer_id)

    class Meta:
        db_table = 'interviews_panelist'
        unique_together = ['interview_id', 'interviewer_id']


# ─── InterviewFeedback ─────────────────────────────────────────────────────────

class InterviewFeedback(models.Model):
    """
    Structured post-interview feedback submitted by a panelist.
    Supports numeric, pass/fail, and criteria-based scoring modes.
    One record per (interview, panelist) — unique_together enforced.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id    = models.UUIDField(db_index=True)
    interview_id = models.UUIDField(db_index=True)
    panelist_id  = models.UUIDField(db_index=True)   # CustomUser.id of the reviewer
    score        = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes        = models.TextField(blank=True)
    recommendation = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        blank=True,
    )
    criteria_scores = models.JSONField(default=dict, blank=True)  # {criterion: score}
    scorecard_ratings = models.JSONField(default=dict, blank=True)  # {attribute_name: rating}
    submitted_at    = models.DateTimeField(auto_now_add=True)
    created_at      = models.DateTimeField(default=timezone.now)
    updated_at      = models.DateTimeField(auto_now=True)
    is_deleted      = models.BooleanField(default=False, db_index=True)
    deleted_at      = models.DateTimeField(null=True, blank=True)
    metadata        = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Feedback: {self.panelist_id} → {self.interview_id}"

    class Meta:
        db_table = 'interviews_feedback'
        unique_together = ['interview_id', 'panelist_id']


# ─── InterviewDecision ─────────────────────────────────────────────────────────

class InterviewDecision(models.Model):
    """
    The final hiring decision recorded for an interview.
    One decision per interview (unique on interview_id).
    Fires events.interview.decision_recorded when created/updated.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id    = models.UUIDField(db_index=True)
    interview_id = models.UUIDField(unique=True, db_index=True)
    decision     = models.CharField(max_length=20, choices=DECISION_CHOICES)
    decision_source = models.CharField(max_length=30, choices=DECISION_SOURCE_CHOICES, default='manual')
    decision_mode = models.CharField(max_length=20, choices=DECISION_MODE_CHOICES, default='manual')
    notes        = models.TextField(blank=True)
    previous_decision = models.CharField(max_length=20, choices=DECISION_CHOICES, blank=True)
    is_override = models.BooleanField(default=False)
    overridden_by = models.UUIDField(null=True, blank=True)
    override_reason = models.TextField(blank=True)
    decided_by   = models.UUIDField()               # CustomUser.id
    decided_at   = models.DateTimeField(auto_now_add=True)
    created_at   = models.DateTimeField(default=timezone.now)
    updated_at   = models.DateTimeField(auto_now=True)
    metadata     = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.decision} – {self.interview_id}"

    class Meta:
        db_table = 'interviews_decision'


class InterviewDecisionHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    interview_id = models.UUIDField(db_index=True)
    decision_id = models.UUIDField(db_index=True)
    previous_decision = models.CharField(max_length=20, choices=DECISION_CHOICES, blank=True)
    new_decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    changed_by = models.UUIDField()
    change_source = models.CharField(max_length=30, choices=DECISION_SOURCE_CHOICES, default='manual')
    is_override = models.BooleanField(default=False)
    override_reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'interviews_decision_history'
        ordering = ['-changed_at']


# ─── InterviewFlow ─────────────────────────────────────────────────────────────

class InterviewFlow(models.Model):
    """
    A reusable end-to-end interview pipeline owned by a tenant.
    Defines an ordered sequence of interview stages; each stage references
    an interview type and an execution mode.

    stages JSON structure:
    [
        {
            "id": "<uuid>",
            "name": "Stage 1 – Recruiter Screen",
            "type_code": "recruiter_screening",
            "mode": "native",          # native | third_party | external_manual
            "order": 1,
            "template_id": null        # optional template binding
        },
        ...
    ]
    """
    EXECUTION_MODES = [
        ('native',          'Native (TOS)'),
        ('third_party',     'Third-Party Integration'),
        ('external_manual', 'External / Manual'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id   = models.UUIDField(db_index=True)
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    stages      = models.JSONField(default=list, blank=True)
    is_active   = models.BooleanField(default=True, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    created_by  = models.UUIDField(null=True, blank=True)
    is_deleted  = models.BooleanField(default=False, db_index=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)
    metadata    = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'interviews_flow'
        ordering = ['-created_at']


# ─── InterviewQuestion ─────────────────────────────────────────────────────────

class InterviewQuestion(models.Model):
    """
    Individual question within an interview, with candidate answer capture
    and dual AI / human scoring slots.
    """
    id                       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id                = models.UUIDField(db_index=True)
    interview_id             = models.UUIDField(db_index=True)
    question_text            = models.TextField()
    question_type            = models.CharField(
        max_length=50,
        choices=[
            ('text',            'Text'),
            ('video',           'Video'),
            ('audio',           'Audio'),
            ('code',            'Code'),
            ('multiple_choice', 'Multiple Choice'),
            ('rating_scale',    'Rating Scale'),
        ],
        default='text',
    )
    options                  = models.JSONField(default=list, blank=True)
    expected_duration_seconds = models.IntegerField(null=True, blank=True)
    candidate_answer         = models.TextField(blank=True)
    candidate_video_url      = models.TextField(blank=True)
    ai_score                 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_feedback              = models.TextField(blank=True)
    human_score              = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    human_feedback           = models.TextField(blank=True)
    order_index              = models.IntegerField(default=0)
    answered_at              = models.DateTimeField(null=True, blank=True)
    created_at               = models.DateTimeField(auto_now_add=True)
    updated_at               = models.DateTimeField(auto_now=True)
    metadata                 = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.question_text[:50]

    class Meta:
        db_table = 'interviews_question'
        ordering = ['order_index']


class InterviewQuestionBank(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    scope = models.CharField(max_length=20, choices=QUESTION_BANK_SCOPE, default='tenant', db_index=True)
    question_title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    question_type = models.CharField(max_length=30, choices=QUESTION_BANK_TYPES, default='text')
    difficulty = models.CharField(max_length=20, choices=QUESTION_DIFFICULTY, default='medium')
    tags = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    options_json = models.JSONField(default=list, blank=True)
    expected_answer = models.TextField(blank=True)
    scoring_weight = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'interviews_question_bank'
        ordering = ['-created_at']


class InterviewQuestionAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    question = models.ForeignKey(
        InterviewQuestionBank,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    attach_type = models.CharField(max_length=20, choices=QUESTION_ATTACH_TYPES, db_index=True)
    template_id = models.UUIDField(null=True, blank=True, db_index=True)
    interview_type = models.CharField(max_length=80, blank=True, db_index=True)
    assessment_ref = models.CharField(max_length=120, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    order_index = models.IntegerField(default=0)
    created_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'interviews_question_attachment'
        ordering = ['order_index', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'question', 'attach_type', 'template_id', 'interview_type', 'assessment_ref'],
                name='uniq_question_attachment_scope',
            ),
        ]


class InterviewQuestionGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    scope = models.CharField(max_length=20, choices=QUESTION_BANK_SCOPE, default='tenant', db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    section_name = models.CharField(max_length=120, blank=True)
    target_type = models.CharField(max_length=20, choices=QUESTION_ATTACH_TYPES, default='template')
    target_ref = models.CharField(max_length=120, blank=True, db_index=True)
    order_index = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'interviews_question_group'
        ordering = ['order_index', 'created_at']


class InterviewQuestionGroupItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        InterviewQuestionGroup,
        on_delete=models.CASCADE,
        related_name='items',
    )
    question = models.ForeignKey(
        InterviewQuestionBank,
        on_delete=models.CASCADE,
        related_name='group_items',
    )
    order_index = models.IntegerField(default=0)
    required = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'interviews_question_group_item'
        ordering = ['order_index', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'question'],
                name='uniq_question_group_item',
            ),
        ]


class InterviewAvailabilityProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    interviewer_id = models.UUIDField(db_index=True)
    mode = models.CharField(max_length=20, choices=AVAILABILITY_MODES, default='system')
    timezone = models.CharField(max_length=64, default='UTC')
    working_hours = models.JSONField(default=default_working_hours, blank=True)
    default_duration_minutes = models.IntegerField(default=60)
    default_buffer_minutes = models.IntegerField(default=15)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'interviews_availability_profile'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'interviewer_id'],
                name='uniq_availability_profile_tenant_interviewer',
            ),
        ]


class InterviewAvailabilityBlock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    interviewer_id = models.UUIDField(db_index=True)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    reason = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=30, default='manual')
    created_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'interviews_availability_block'
        ordering = ['starts_at']


class InterviewCalendarConnection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    interviewer_id = models.UUIDField(db_index=True)
    provider = models.CharField(max_length=20, choices=CALENDAR_PROVIDERS)
    external_calendar_id = models.CharField(max_length=255, blank=True)
    account_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    sync_enabled = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'interviews_calendar_connection'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'interviewer_id', 'provider', 'external_calendar_id'],
                name='uniq_calendar_connection_scope',
            ),
        ]


class InterviewIntegrationProvider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=80, unique=True, db_index=True)
    provider_type = models.CharField(max_length=30, choices=INTEGRATION_PROVIDER_TYPES)
    is_active = models.BooleanField(default=True, db_index=True)
    tenant_configurable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'interviews_integration_provider'
        ordering = ['provider_type', 'name']


class InterviewTenantProviderConnection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    provider = models.ForeignKey(
        InterviewIntegrationProvider,
        on_delete=models.CASCADE,
        related_name='tenant_connections',
    )
    auth_data = models.JSONField(default=dict, blank=True)
    config_data = models.JSONField(default=dict, blank=True)
    is_enabled = models.BooleanField(default=True, db_index=True)
    connection_status = models.CharField(max_length=30, default='configured')
    last_validated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'interviews_tenant_provider_connection'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'provider'],
                name='uniq_tenant_provider_connection',
            ),
        ]


class InterviewExecutionMapping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    interview_type = models.CharField(max_length=50, db_index=True)
    stage_code = models.CharField(max_length=80, blank=True, db_index=True)
    execution_mode = models.CharField(
        max_length=30,
        choices=INTERVIEW_INTEGRATION_EXECUTION_MODES,
        default='native',
    )
    provider_code = models.CharField(max_length=80, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'interviews_execution_mapping'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'interview_type', 'stage_code'],
                name='uniq_tenant_interview_execution_mapping',
            ),
        ]


class InterviewSchedulingLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    interview_id = models.UUIDField(db_index=True)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    timezone = models.CharField(max_length=64, default='UTC')
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    max_bookings = models.IntegerField(default=1)
    booking_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    last_selected_slot = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'interviews_scheduling_link'
