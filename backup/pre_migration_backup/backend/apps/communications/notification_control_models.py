"""
Notification Control Center — Models
======================================
Admin-configurable rules that govern how the notification engine behaves
on a per-tenant, per-event-trigger basis.

These models sit alongside the core Notification / NotificationDelivery
models and are read by NotificationService at runtime.
"""
import uuid
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

class NotificationRuleCategory(models.TextChoices):
    CANDIDATE    = 'candidate',    'Candidate'
    APPLICATION  = 'application',  'Application'
    INTERVIEW    = 'interview',    'Interview'
    OFFER        = 'offer',        'Offer'
    APPROVAL     = 'approval',     'Approval'
    AGENCY       = 'agency',       'Agency'
    DEADLINE     = 'deadline',     'Deadline / SLA'
    MESSAGING    = 'messaging',    'Messaging'
    PASSPORT     = 'passport',     'Passport'
    SYSTEM       = 'system',       'System'


class EscalationTargetType(models.TextChoices):
    ASSIGNED_MANAGER  = 'assigned_manager',  "Assigned User's Manager"
    HIRING_MANAGER    = 'hiring_manager',    'Hiring Manager'
    RECRUITER_LEAD    = 'recruiter_lead',    'Recruiter Lead'
    TENANT_ADMIN      = 'tenant_admin',      'Tenant Admin'


# ---------------------------------------------------------------------------
# NotificationRule
# ---------------------------------------------------------------------------

class NotificationRule(models.Model):
    """
    Per-tenant, per-trigger rule that controls notification behaviour.

    Merge order:
        System default (is_system=True, tenant_id=None)
        → Tenant override (is_system=False, tenant_id=<uuid>)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # tenant_id=None means "system default"
    tenant_id  = models.UUIDField(null=True, blank=True, db_index=True)
    event_key  = models.CharField(max_length=120, db_index=True,
                                  help_text='Internal event key (e.g. application_shortlisted)')
    # ── Business-facing fields ───────────────────────────────────────────────
    business_label = models.CharField(max_length=200,
                                      help_text='Human-friendly label shown in admin UI')
    category       = models.CharField(max_length=40,
                                      choices=NotificationRuleCategory.choices,
                                      default=NotificationRuleCategory.SYSTEM,
                                      db_index=True)
    priority       = models.CharField(
        max_length=20,
        choices=[
            ('info',     'Info'),
            ('medium',   'Medium'),
            ('high',     'High'),
            ('critical', 'Critical'),
        ],
        default='info',
        db_index=True,
    )
    # ── Rule state ───────────────────────────────────────────────────────────
    is_active      = models.BooleanField(default=True, db_index=True)
    is_system      = models.BooleanField(default=False,
                                         help_text='System rules cannot be deleted by tenants')
    is_locked      = models.BooleanField(default=False,
                                         help_text='Locked rules cannot be edited')
    # ── Channel controls ─────────────────────────────────────────────────────
    in_app_enabled    = models.BooleanField(default=True)
    email_enabled     = models.BooleanField(default=True)
    whatsapp_enabled  = models.BooleanField(default=False)
    sms_enabled       = models.BooleanField(default=False)
    # ── Delivery timing ──────────────────────────────────────────────────────
    send_immediately  = models.BooleanField(default=True)
    # ── Fallback controls ────────────────────────────────────────────────────
    fallback_enabled        = models.BooleanField(default=False)
    fallback_delay_minutes  = models.PositiveIntegerField(
        default=40,
        help_text='Minutes after creation before fallback email is sent',
    )
    # ── Escalation controls ──────────────────────────────────────────────────
    escalation_enabled       = models.BooleanField(default=False)
    escalation_delay_minutes = models.PositiveIntegerField(
        default=60,
        help_text='Minutes after fallback before escalation fires',
    )
    escalation_target_type   = models.CharField(
        max_length=40,
        choices=EscalationTargetType.choices,
        default=EscalationTargetType.TENANT_ADMIN,
    )
    # ── Template linkage ─────────────────────────────────────────────────────
    template_id    = models.UUIDField(null=True, blank=True,
                                      help_text='Linked email template UUID')
    template_name  = models.CharField(max_length=200, blank=True)
    # ── User preference override ─────────────────────────────────────────────
    allow_user_override = models.BooleanField(
        default=True,
        help_text='Whether users can individually turn this notification off',
    )
    # ── Help text shown to admin ─────────────────────────────────────────────
    admin_notes = models.TextField(blank=True)
    # ── Audit ────────────────────────────────────────────────────────────────
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    updated_by  = models.UUIDField(null=True, blank=True)
    is_deleted  = models.BooleanField(default=False, db_index=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)
    metadata    = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    def __str__(self):
        return f'{self.business_label} ({self.event_key}) — tenant={self.tenant_id}'

    class Meta:
        db_table = 'comms_notification_rule'
        # One rule per event per tenant (None = system default)
        unique_together = ('tenant_id', 'event_key')
        indexes = [
            models.Index(fields=['tenant_id', 'category', 'is_active']),
            models.Index(fields=['tenant_id', 'event_key', 'is_deleted']),
        ]
        ordering = ['category', 'business_label']


# ---------------------------------------------------------------------------
# NotificationChannelSetting
# ---------------------------------------------------------------------------

class NotificationChannelSetting(models.Model):
    """
    Tenant-level on/off toggle for each notification channel.
    Controls whether the channel is globally available for a tenant.
    """
    CHANNEL_CHOICES = [
        ('in_app',    'In-App'),
        ('email',     'Email'),
        ('whatsapp',  'WhatsApp'),
        ('sms',       'SMS'),
        ('push',      'Push'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id    = models.UUIDField(db_index=True)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_CHOICES, db_index=True)
    is_enabled   = models.BooleanField(default=True)
    provider     = models.CharField(max_length=80, blank=True)
    # Business hours config (future-ready)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start   = models.TimeField(null=True, blank=True)
    quiet_hours_end     = models.TimeField(null=True, blank=True)
    # Sender config
    sender_name  = models.CharField(max_length=200, blank=True)
    sender_email = models.EmailField(blank=True)
    config_json  = models.JSONField(default=dict, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    metadata     = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'comms_notification_channel_setting'
        unique_together = ('tenant_id', 'channel_type')
        indexes = [
            models.Index(fields=['tenant_id', 'channel_type', 'is_enabled']),
        ]


# ---------------------------------------------------------------------------
# TenantNotificationPreferenceDefaults
# ---------------------------------------------------------------------------

class TenantNotificationPreferenceDefaults(models.Model):
    """
    Tenant-level defaults for user notification preferences.
    Controls what new users get by default and whether they can override.
    """
    id                       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id                = models.UUIDField(unique=True, db_index=True)
    default_in_app_enabled   = models.BooleanField(default=True)
    default_email_enabled    = models.BooleanField(default=True)
    default_reminder_enabled = models.BooleanField(default=True)
    allow_user_override      = models.BooleanField(
        default=True,
        help_text='Allow users to change their own notification preferences',
    )
    digest_frequency         = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('hourly',    'Hourly digest'),
            ('daily',     'Daily digest'),
        ],
        default='immediate',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata   = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'comms_tenant_notification_prefs'
