"""
Email Delivery Models
======================
Models for the automation email delivery engine.

Two models:
  TenantEmailConfig  — per-tenant provider credentials for automation emails
  EmailDelivery      — per-message tracking record for every automation email sent

Both are declared in this file with explicit app_label = 'communications'
(same pattern as notification_orchestration_models.py) so they live
outside models.py without confusing Django's app registry.
"""
import uuid

from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# TenantEmailConfig
# ---------------------------------------------------------------------------

class TenantEmailProvider(models.TextChoices):
    SMTP      = 'smtp',      'SMTP'
    SENDGRID  = 'sendgrid',  'SendGrid'
    SES       = 'ses',       'Amazon SES'
    SYSTEM    = 'system',    'System Default'


class TenantEmailConfig(models.Model):
    """
    Per-tenant email provider configuration for automation/notification emails.

    Credentials are stored encrypted using apps.communications.utils.encrypt_string.
    Use the property helpers (e.g. decrypted_smtp_password) to read them safely.

    Only ONE active config per tenant — enforced at service level (not DB unique
    constraint) to allow staged transitions between providers.
    """

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id  = models.UUIDField(db_index=True)
    provider   = models.CharField(
        max_length=20,
        choices=TenantEmailProvider.choices,
        default=TenantEmailProvider.SYSTEM,
    )

    # Sender identity
    from_email     = models.EmailField(blank=True)
    from_name      = models.CharField(max_length=255, blank=True)
    reply_to_email = models.EmailField(blank=True)

    # --- SMTP ---
    smtp_host              = models.CharField(max_length=255, blank=True)
    smtp_port              = models.IntegerField(default=587)
    smtp_username          = models.CharField(max_length=255, blank=True)
    smtp_password_encrypted = models.TextField(blank=True)   # encrypted via encrypt_string
    smtp_use_tls           = models.BooleanField(default=True)
    smtp_use_ssl           = models.BooleanField(default=False)

    # --- SendGrid ---
    sendgrid_api_key_encrypted = models.TextField(blank=True)  # encrypted

    # --- Amazon SES ---
    ses_region                       = models.CharField(max_length=30, blank=True)
    ses_access_key_id                = models.CharField(max_length=128, blank=True)
    ses_secret_access_key_encrypted  = models.TextField(blank=True)  # encrypted

    # Status
    is_active  = models.BooleanField(default=True, db_index=True)
    metadata   = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label  = 'communications'
        db_table   = 'comms_tenant_email_config'
        ordering   = ['-created_at']

    def __str__(self):
        return f'TenantEmailConfig({self.tenant_id}, provider={self.provider})'

    # ------------------------------------------------------------------
    # Decryption helpers — never store plaintext credentials in memory
    # ------------------------------------------------------------------

    @property
    def decrypted_smtp_password(self) -> str:
        from apps.communications.utils import decrypt_string
        return decrypt_string(self.smtp_password_encrypted)

    @property
    def decrypted_sendgrid_api_key(self) -> str:
        from apps.communications.utils import decrypt_string
        return decrypt_string(self.sendgrid_api_key_encrypted)

    @property
    def decrypted_ses_secret(self) -> str:
        from apps.communications.utils import decrypt_string
        return decrypt_string(self.ses_secret_access_key_encrypted)

    # ------------------------------------------------------------------
    # Class-level helpers
    # ------------------------------------------------------------------

    @classmethod
    def get_for_tenant(cls, tenant_id) -> 'TenantEmailConfig | None':
        """Return the active config for a tenant, or None (system default)."""
        return cls.objects.filter(tenant_id=tenant_id, is_active=True).first()


# ---------------------------------------------------------------------------
# EmailDelivery
# ---------------------------------------------------------------------------

class EmailDeliveryStatus(models.TextChoices):
    PENDING   = 'pending',   'Pending'
    SENDING   = 'sending',   'Sending'
    SENT      = 'sent',      'Sent'
    DELIVERED = 'delivered', 'Delivered'
    FAILED    = 'failed',    'Failed'
    BOUNCED   = 'bounced',   'Bounced'
    DEFERRED  = 'deferred',  'Deferred'


class EmailDeliveryPriority(models.TextChoices):
    LOW    = 'low',    'Low'
    NORMAL = 'normal', 'Normal'
    HIGH   = 'high',   'High'
    URGENT = 'urgent', 'Urgent'


class EmailDelivery(models.Model):
    """
    Tracks every automation-triggered email message end-to-end.

    Created in PENDING state by EmailDeliveryService before the Celery
    task is queued.  The task updates status as it progresses.

    This is separate from EmailMessage (which tracks business/conversation
    emails).  EmailDelivery is exclusively for:
    - Notification fallback emails
    - Escalation emails
    - Reminder emails
    - System alert emails
    """

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id       = models.UUIDField(db_index=True)
    notification_id = models.UUIDField(null=True, blank=True, db_index=True)

    recipient_email = models.EmailField()
    subject         = models.CharField(max_length=500)
    template_used   = models.CharField(max_length=255, blank=True)
    provider        = models.CharField(max_length=20, blank=True)

    status = models.CharField(
        max_length=20,
        choices=EmailDeliveryStatus.choices,
        default=EmailDeliveryStatus.PENDING,
        db_index=True,
    )
    priority = models.CharField(
        max_length=10,
        choices=EmailDeliveryPriority.choices,
        default=EmailDeliveryPriority.NORMAL,
        db_index=True,
    )

    error_message = models.TextField(blank=True)
    retry_count   = models.IntegerField(default=0)
    max_retries   = models.IntegerField(default=4)

    sent_at      = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    # Provider-issued message ID (for webhook correlation)
    provider_message_id = models.CharField(max_length=255, blank=True)

    metadata   = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'communications'
        db_table  = 'comms_email_delivery'
        ordering  = ['-created_at']
        indexes   = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'created_at']),
        ]

    def __str__(self):
        return f'EmailDelivery({self.id}, status={self.status}, to={self.recipient_email})'

    # ------------------------------------------------------------------
    # State transition helpers
    # ------------------------------------------------------------------

    def mark_sending(self):
        self.status = EmailDeliveryStatus.SENDING
        self.save(update_fields=['status', 'updated_at'])

    def mark_sent(self, provider_message_id: str = ''):
        self.status = EmailDeliveryStatus.SENT
        self.sent_at = timezone.now()
        self.provider_message_id = provider_message_id
        self.error_message = ''
        self.save(update_fields=['status', 'sent_at', 'provider_message_id', 'error_message', 'updated_at'])

    def mark_failed(self, error: str = ''):
        self.status = EmailDeliveryStatus.FAILED
        self.error_message = error[:2000]
        self.save(update_fields=['status', 'error_message', 'updated_at'])

    def mark_deferred(self, next_retry_at, error: str = ''):
        self.status = EmailDeliveryStatus.DEFERRED
        self.error_message = error[:2000]
        self.next_retry_at = next_retry_at
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'next_retry_at', 'retry_count', 'updated_at'])

    def mark_delivered(self):
        self.status = EmailDeliveryStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])

    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries and self.status in (
            EmailDeliveryStatus.FAILED, EmailDeliveryStatus.DEFERRED,
        )
