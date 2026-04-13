"""
Notification Automation Orchestration Models
=============================================
Tracks every scheduled automation action (fallback, escalation, reminder)
and records the full history of escalation actions taken.

These models give the platform an auditable, cancellable, idempotent record
of every pending or executed automation flow per notification.
"""
import uuid

from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# NotificationAutomationJob
# ---------------------------------------------------------------------------

class NotificationAutomationJobType(models.TextChoices):
    FALLBACK_EMAIL     = 'fallback_email',     'Fallback Email'
    ESCALATION         = 'escalation',         'Escalation'
    REMINDER           = 'reminder',           'Reminder'
    DIGEST             = 'digest',             'Digest'
    # Multi-channel additions
    WHATSAPP_FALLBACK  = 'whatsapp_fallback',  'WhatsApp Fallback'
    SMS_ESCALATION     = 'sms_escalation',     'SMS Escalation'
    PUSH_NOTIFICATION  = 'push_notification',  'Push Notification'
    CHANNEL_DELIVERY   = 'channel_delivery',   'Channel Delivery'


class NotificationAutomationJobStatus(models.TextChoices):
    PENDING   = 'pending',   'Pending'
    EXECUTED  = 'executed',  'Executed'
    CANCELLED = 'cancelled', 'Cancelled'
    FAILED    = 'failed',    'Failed'
    SKIPPED   = 'skipped',   'Skipped'


class NotificationAutomationJob(models.Model):
    """
    Tracks a scheduled automation action tied to a notification.

    Lifecycle:
        PENDING   — job is scheduled, Celery task is queued
        EXECUTED  — task ran and sent its payload
        CANCELLED — notification was read/resolved before task ran
        FAILED    — task ran but encountered an error
        SKIPPED   — task ran but preconditions were already satisfied
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    # Parent notification this job is associated with
    notification = models.ForeignKey(
        'communications.Notification',
        on_delete=models.CASCADE,
        related_name='automation_jobs',
        null=True,
        blank=True,
    )

    # The event that triggered this chain
    event_key = models.CharField(max_length=120, blank=True, db_index=True)

    # What kind of automation action this job represents
    job_type = models.CharField(
        max_length=30,
        choices=NotificationAutomationJobType.choices,
        db_index=True,
    )

    # When this job is scheduled to execute
    scheduled_for = models.DateTimeField(db_index=True)

    # When it actually ran
    executed_at = models.DateTimeField(null=True, blank=True)

    # Current state
    status = models.CharField(
        max_length=20,
        choices=NotificationAutomationJobStatus.choices,
        default=NotificationAutomationJobStatus.PENDING,
        db_index=True,
    )

    # Reason when cancelled (e.g., 'notification_read', 'entity_resolved', 'manual')
    cancel_reason = models.CharField(max_length=200, blank=True)

    # Number of retries attempted
    retry_count = models.PositiveSmallIntegerField(default=0)

    # Celery task ID for potential inspection
    celery_task_id = models.CharField(max_length=255, blank=True)

    # The business entity driving this job
    related_entity_type = models.CharField(max_length=80, blank=True)
    related_entity_id = models.UUIDField(null=True, blank=True)

    # Free-form context saved at scheduling time
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def cancel(self, reason: str = ''):
        if self.status == NotificationAutomationJobStatus.PENDING:
            self.status = NotificationAutomationJobStatus.CANCELLED
            self.cancel_reason = reason or 'cancelled'
            self.save(update_fields=['status', 'cancel_reason', 'updated_at'])

    def mark_executed(self):
        self.status = NotificationAutomationJobStatus.EXECUTED
        self.executed_at = timezone.now()
        self.save(update_fields=['status', 'executed_at', 'updated_at'])

    def mark_failed(self):
        self.status = NotificationAutomationJobStatus.FAILED
        self.save(update_fields=['status', 'updated_at'])

    def mark_skipped(self):
        self.status = NotificationAutomationJobStatus.SKIPPED
        self.save(update_fields=['status', 'updated_at'])

    class Meta:
        app_label = 'communications'
        db_table = 'comms_notification_automation_job'
        ordering = ['-scheduled_for']
        indexes = [
            models.Index(fields=['tenant_id', 'status', 'scheduled_for']),
            models.Index(fields=['notification_id', 'status']),
            models.Index(fields=['tenant_id', 'job_type', 'status']),
            models.Index(fields=['related_entity_type', 'related_entity_id', 'status']),
        ]

    def __str__(self):
        return f'{self.job_type} / {self.status} — notification={self.notification_id}'


# ---------------------------------------------------------------------------
# NotificationEscalationLog
# ---------------------------------------------------------------------------

class NotificationEscalationLogStatus(models.TextChoices):
    SENT    = 'sent',    'Sent'
    FAILED  = 'failed',  'Failed'
    SKIPPED = 'skipped', 'Skipped — target not resolved'


class NotificationEscalationLog(models.Model):
    """
    Immutable record of each escalation action taken.
    Created when escalate_notification actually fires and notifies a target.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    notification = models.ForeignKey(
        'communications.Notification',
        on_delete=models.CASCADE,
        related_name='escalation_logs',
    )

    # Which escalation step this is (1, 2, 3 …)
    escalation_level = models.PositiveSmallIntegerField(default=1)

    # The user who received the escalation notification
    target_user_id = models.UUIDField(null=True, blank=True, db_index=True)

    # How the target was resolved (from EscalationTargetType choices)
    target_type = models.CharField(max_length=40, blank=True)

    # When the escalation was triggered
    triggered_at = models.DateTimeField(auto_now_add=True)

    # Channel used to notify the escalation target
    channel_used = models.CharField(max_length=20, default='in_app')

    # Whether the escalation was actually delivered
    status = models.CharField(
        max_length=20,
        choices=NotificationEscalationLogStatus.choices,
        default=NotificationEscalationLogStatus.SENT,
        db_index=True,
    )

    # Original notification details saved for audit
    original_event_key = models.CharField(max_length=120, blank=True)
    original_user_id = models.UUIDField(null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'communications'
        db_table = 'comms_notification_escalation_log'
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['tenant_id', 'notification_id']),
            models.Index(fields=['tenant_id', 'target_user_id', 'triggered_at']),
        ]

    def __str__(self):
        return (
            f'Escalation L{self.escalation_level} / {self.status} '
            f'— notification={self.notification_id} → user={self.target_user_id}'
        )
