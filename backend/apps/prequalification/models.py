import uuid
from django.db import models
from django.utils import timezone


# ─── Choices ──────────────────────────────────────────────────────────────────

QUESTION_TYPES = [
    ('yes_no',        'Yes / No'),
    ('single_select', 'Single Choice'),
    ('multi_select',  'Multiple Choice'),
    ('short_text',    'Short Answer'),
    ('long_text',     'Paragraph'),
    ('number',        'Number'),
    ('dropdown',      'Dropdown'),
    ('date',          'Date'),
    ('file_upload',   'File Upload'),
    # legacy aliases kept for backward compat
    ('multiple_choice', 'Multiple Choice (legacy)'),
    ('text',            'Text (legacy)'),
]

CONDITION_TYPES = [
    ('equals',        'Equals'),
    ('not_equals',    'Not Equals'),
    ('greater_than',  'Greater Than'),
    ('less_than',     'Less Than'),
    ('contains',      'Contains'),
    ('is_empty',      'Is Empty'),
    ('is_not_empty',  'Is Not Empty'),
    ('in',            'Is One Of'),
    ('not_in',        'Is Not One Of'),
]

ACTION_TYPES = [
    ('reject',            'Auto Reject'),
    ('next_question',     'Continue to Next'),
    ('skip_section',      'Skip to Section'),
    ('manual_review',     'Flag for Manual Review'),
    ('show_question',     'Show Question'),
    ('hide_question',     'Hide Question'),
    ('route_to_outcome',  'Route to Outcome'),
    ('end_form',          'End Form'),
]


# ─── PrequalForm ──────────────────────────────────────────────────────────────

class PrequalForm(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id   = models.UUIDField(db_index=True)
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True)
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
        db_table = 'prequalification_form'
        ordering = ['-created_at']


# ─── PrequalSection ───────────────────────────────────────────────────────────

class PrequalSection(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id   = models.UUIDField(db_index=True)
    form        = models.ForeignKey(
        PrequalForm,
        on_delete=models.CASCADE,
        related_name='sections',
        db_column='form_id',
    )
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order       = models.IntegerField(default=0, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    created_by  = models.UUIDField(null=True, blank=True)
    metadata    = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.form} › {self.title}"

    class Meta:
        db_table = 'prequalification_section'
        ordering = ['order']


# ─── PrequalQuestion ──────────────────────────────────────────────────────────

class PrequalQuestion(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id     = models.UUIDField(db_index=True)
    section       = models.ForeignKey(
        PrequalSection,
        on_delete=models.CASCADE,
        related_name='questions',
        db_column='section_id',
    )
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES, default='yes_no')
    required      = models.BooleanField(default=True)
    order         = models.IntegerField(default=0, db_index=True)
    help_text     = models.TextField(blank=True)
    options_json  = models.JSONField(default=list, blank=True)
    score_weight  = models.IntegerField(default=0)
    is_knockout   = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)
    created_by    = models.UUIDField(null=True, blank=True)
    metadata      = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.question_text[:60]

    class Meta:
        db_table = 'prequalification_question'
        ordering = ['order']


# ─── PrequalRule ──────────────────────────────────────────────────────────────

class PrequalRule(models.Model):
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id           = models.UUIDField(db_index=True)
    question            = models.ForeignKey(
        PrequalQuestion,
        on_delete=models.CASCADE,
        related_name='rules',
        db_column='question_id',
    )
    condition_type      = models.CharField(max_length=50, choices=CONDITION_TYPES, default='equals')
    compare_value       = models.CharField(max_length=500, blank=True)
    action_type         = models.CharField(max_length=50, choices=ACTION_TYPES, default='next_question')
    outcome_code        = models.CharField(max_length=100, blank=True)
    target_question_id  = models.UUIDField(null=True, blank=True)
    target_section_id   = models.UUIDField(null=True, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)
    created_by          = models.UUIDField(null=True, blank=True)
    metadata            = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Rule: {self.condition_type}={self.compare_value} → {self.action_type}"

    class Meta:
        db_table = 'prequalification_rule'
        ordering = ['created_at']


# ─── PrequalResponse ──────────────────────────────────────────────────────────

class PrequalResponse(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id    = models.UUIDField(db_index=True)
    form         = models.ForeignKey(
        PrequalForm,
        on_delete=models.CASCADE,
        related_name='responses',
        db_column='form_id',
    )
    candidate_id = models.UUIDField(db_index=True)
    question     = models.ForeignKey(
        PrequalQuestion,
        on_delete=models.CASCADE,
        related_name='responses',
        db_column='question_id',
    )
    answer_text  = models.TextField(blank=True)
    answer_json  = models.JSONField(default=dict, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    created_by   = models.UUIDField(null=True, blank=True)
    metadata     = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Response: {self.candidate_id} → {self.question_id}"

    class Meta:
        db_table = 'prequalification_response'
        ordering = ['-created_at']
