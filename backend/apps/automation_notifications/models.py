import uuid
from django.db import models
from shared.models import BaseModel


# ─── Choice constants ─────────────────────────────────────────────────────────

class NotificationChannel(models.TextChoices):
    EMAIL    = 'email',    'Email'
    WHATSAPP = 'whatsapp', 'WhatsApp'
    IN_APP   = 'in_app',  'In-App'
    SMS      = 'sms',     'SMS'
    PUSH     = 'push',    'Push'


class RecipientType(models.TextChoices):
    CANDIDATE          = 'candidate',           'Candidate'
    ASSIGNED_RECRUITER = 'assigned_recruiter',  'Assigned Recruiter'
    HIRING_MANAGER     = 'hiring_manager',      'Hiring Manager'
    RECRUITER_MANAGER  = 'recruiter_manager',   'Recruiter Manager'
    AGENCY_CONTACT     = 'agency_contact',      'Agency Contact'
    CUSTOM_USER        = 'custom_user',         'Custom User'
    WORKFLOW_OWNER     = 'workflow_owner',      'Workflow Owner'


class DeliveryStatus(models.TextChoices):
    QUEUED        = 'queued',        'Queued'
    SENT          = 'sent',          'Sent'
    DELIVERED     = 'delivered',     'Delivered'
    FAILED        = 'failed',        'Failed'
    SKIPPED       = 'skipped',       'Skipped'
    THROTTLED     = 'throttled',     'Throttled'
    DEDUPLICATED  = 'deduplicated',  'Deduplicated'


class EscalationStatus(models.TextChoices):
    PENDING   = 'pending',   'Pending'
    SENT      = 'sent',      'Sent'
    RESOLVED  = 'resolved',  'Resolved'
    CANCELLED = 'cancelled', 'Cancelled'


class InsightType(models.TextChoices):
    HIGH_FAILURE_RATE           = 'high_failure_rate',            'High Failure Rate'
    DUPLICATE_RISK              = 'duplicate_risk',               'Duplicate Risk'
    CHANNEL_UNDERPERFORMING     = 'channel_underperforming',      'Channel Underperforming'
    ESCALATION_SPIKE            = 'escalation_spike',             'Escalation Spike'
    CANDIDATE_NON_RESPONSE      = 'candidate_non_response_pattern','Candidate Non-Response Pattern'


# ─── Model 1: WorkflowNotificationRule ───────────────────────────────────────

class WorkflowNotificationRule(BaseModel):
    """
    Defines how notifications should be sent for a specific workflow/event combination.
    """
    workflow_id            = models.UUIDField(db_index=True)
    action_node_id         = models.CharField(max_length=100, blank=True)
    notification_event     = models.CharField(max_length=150)
    recipient_type         = models.CharField(max_length=50, choices=RecipientType.choices)
    channel                = models.CharField(max_length=20, choices=NotificationChannel.choices, default=NotificationChannel.IN_APP)
    template_id            = models.UUIDField(null=True, blank=True)
    fallback_channels      = models.JSONField(default=list, blank=True)   # ordered list of channel strings
    send_delay_minutes     = models.PositiveIntegerField(default=0)
    throttle_window_minutes= models.PositiveIntegerField(default=0)       # 0 = no throttle
    dedupe_key_template    = models.CharField(max_length=255, blank=True) # e.g. "reminder:{candidate_id}:{job_id}"
    is_active              = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'Workflow Notification Rule'
        ordering     = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'workflow_id']),
            models.Index(fields=['tenant_id', 'notification_event', 'is_active']),
        ]

    def __str__(self):
        return f'{self.notification_event} → {self.channel} ({self.recipient_type})'


# ─── Model 2: WorkflowNotificationDelivery ───────────────────────────────────

class WorkflowNotificationDelivery(models.Model):
    """
    Immutable record of each notification attempt and its outcome.
    """
    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id            = models.UUIDField(db_index=True)
    execution_id         = models.UUIDField(null=True, blank=True, db_index=True)
    workflow_id          = models.UUIDField(null=True, blank=True, db_index=True)
    notification_rule    = models.ForeignKey(
        WorkflowNotificationRule,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='deliveries',
    )
    recipient_user_id    = models.UUIDField(null=True, blank=True)
    recipient_email      = models.EmailField(blank=True)
    recipient_phone      = models.CharField(max_length=30, blank=True)
    channel              = models.CharField(max_length=20, choices=NotificationChannel.choices)
    status               = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.QUEUED, db_index=True)
    provider_message_id  = models.CharField(max_length=255, blank=True)
    subject              = models.CharField(max_length=500, blank=True)
    rendered_message     = models.TextField(blank=True)
    dedupe_key           = models.CharField(max_length=500, blank=True, db_index=True)
    sent_at              = models.DateTimeField(null=True, blank=True)
    delivered_at         = models.DateTimeField(null=True, blank=True)
    failed_at            = models.DateTimeField(null=True, blank=True)
    retry_count          = models.PositiveSmallIntegerField(default=0)
    failure_reason       = models.TextField(blank=True)
    metadata             = models.JSONField(default=dict, blank=True)
    created_at           = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Workflow Notification Delivery'
        ordering     = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'channel', 'status']),
            models.Index(fields=['tenant_id', 'dedupe_key']),
            models.Index(fields=['execution_id', 'status']),
        ]

    def __str__(self):
        return f'{self.channel} → {self.recipient_email or self.recipient_user_id} [{self.status}]'


# ─── Model 3: WorkflowNotificationPreference ─────────────────────────────────

class WorkflowNotificationPreference(BaseModel):
    """
    Per-user notification preferences for workflow-driven communications.
    """
    user_id                  = models.UUIDField(db_index=True)
    notification_type        = models.CharField(max_length=150)
    preferred_channels       = models.JSONField(default=list)            # ordered list of preferred channels
    quiet_hours_start        = models.TimeField(null=True, blank=True)   # e.g. 22:00
    quiet_hours_end          = models.TimeField(null=True, blank=True)   # e.g. 08:00
    allow_escalation_override = models.BooleanField(default=False)       # bypass quiet hours on escalations
    is_active                = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Workflow Notification Preference'
        ordering     = ['user_id']
        unique_together = [('tenant_id', 'user_id', 'notification_type')]
        indexes = [
            models.Index(fields=['tenant_id', 'user_id']),
        ]

    def __str__(self):
        return f'{self.user_id} — {self.notification_type}'


# ─── Model 4: WorkflowEscalationNotification ─────────────────────────────────

class WorkflowEscalationNotification(models.Model):
    """
    Escalation events when no response / action is received within threshold.
    """
    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id            = models.UUIDField(db_index=True)
    workflow_id          = models.UUIDField(db_index=True)
    execution_id         = models.UUIDField(null=True, blank=True, db_index=True)
    escalation_level     = models.PositiveSmallIntegerField(default=1)   # 1 = first escalation, 2 = second…
    trigger_reason       = models.CharField(max_length=255)
    target_recipient_type= models.CharField(max_length=50, choices=RecipientType.choices)
    channel              = models.CharField(max_length=20, choices=NotificationChannel.choices)
    status               = models.CharField(max_length=20, choices=EscalationStatus.choices, default=EscalationStatus.PENDING)
    sent_at              = models.DateTimeField(null=True, blank=True)
    metadata             = models.JSONField(default=dict, blank=True)
    created_at           = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Workflow Escalation Notification'
        ordering     = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'workflow_id']),
        ]

    def __str__(self):
        return f'L{self.escalation_level} escalation — {self.trigger_reason} [{self.status}]'


# ─── Model 5: WorkflowNotificationInsight ────────────────────────────────────

class WorkflowNotificationInsight(models.Model):
    """
    AI/analytics-surfaced insights about notification health and patterns.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id    = models.UUIDField(db_index=True)
    workflow_id  = models.UUIDField(null=True, blank=True, db_index=True)
    insight_type = models.CharField(max_length=60, choices=InsightType.choices)
    title        = models.CharField(max_length=255)
    description  = models.TextField(blank=True)
    metric_value = models.FloatField(default=0.0)
    created_at   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Workflow Notification Insight'
        ordering     = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'insight_type']),
        ]

    def __str__(self):
        return f'{self.insight_type}: {self.title}'
