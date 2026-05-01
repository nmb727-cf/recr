"""
Multi-Channel Configuration and Delivery Tracking Models
=========================================================
Provides:

  TenantChannelConfig   — per-tenant provider credentials and settings for
                          WhatsApp, SMS, and Push channels.  Mirror of
                          TenantEmailConfig for non-email channels.

  CommunicationDelivery — unified delivery-attempt record for every outbound
                          message on any channel (WhatsApp, SMS, Push).
                          Email tracking stays in EmailDelivery; this model
                          covers the rest and gives unified queryability across
                          all channels via the channel_type field.

Both models live outside models.py (same pattern as email_delivery_models.py)
and are imported at the bottom of models.py so Django's migration engine
discovers them under the 'communications' app label.
"""
import uuid

from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

class ChannelType(models.TextChoices):
    """Canonical channel identifiers used across the whole comms engine."""
    IN_APP    = 'in_app',    'In-App'
    EMAIL     = 'email',     'Email'
    WHATSAPP  = 'whatsapp',  'WhatsApp'
    SMS       = 'sms',       'SMS'
    PUSH      = 'push',      'Push'


class WhatsAppProvider(models.TextChoices):
    WHATSAPP_BUSINESS_API = 'whatsapp_business_api', 'WhatsApp Business API'
    TWILIO_WHATSAPP       = 'twilio_whatsapp',       'Twilio WhatsApp'
    MOCK                  = 'mock',                  'Mock (Dev/Test)'


class SMSProvider(models.TextChoices):
    TWILIO      = 'twilio',      'Twilio SMS'
    GENERIC_HTTP = 'generic_http', 'Generic HTTP Gateway'
    MOCK        = 'mock',        'Mock (Dev/Test)'


class PushProvider(models.TextChoices):
    WEB_PUSH  = 'web_push',  'Web Push (VAPID)'
    FCM       = 'fcm',       'Firebase Cloud Messaging'
    APNS      = 'apns',      'Apple Push (APNs)'
    MOCK      = 'mock',      'Mock (Dev/Test)'


# ---------------------------------------------------------------------------
# TenantChannelConfig
# ---------------------------------------------------------------------------

class TenantChannelConfig(models.Model):
    """
    Per-tenant provider configuration for WhatsApp, SMS, and Push channels.

    Design:
      • One row per channel per tenant.
      • Only one active config per (tenant_id, channel_type) at a time —
        enforced at service level to allow zero-downtime credential rotation.
      • Credentials are stored AES-256 encrypted via apps.communications.utils.
      • Use the property helpers (e.g. decrypted_whatsapp_token) to read creds.

    Usage:
        config = TenantChannelConfig.get_active(tenant_id, 'whatsapp')
        if config:
            token = config.decrypted_api_token
    """

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id   = models.UUIDField(db_index=True)
    channel_type = models.CharField(
        max_length=20,
        choices=[
            ('whatsapp', 'WhatsApp'),
            ('sms', 'SMS'),
            ('push', 'Push'),
        ],
        db_index=True,
    )

    # Which provider implementation to use
    provider = models.CharField(max_length=40, blank=True)

    # Sender identity
    sender_name       = models.CharField(max_length=200, blank=True)
    sender_identifier = models.CharField(
        max_length=200,
        blank=True,
        help_text='Phone number (E.164), sender ID, or push project ID',
    )

    # --- Generic encrypted credential fields ---
    # api_token covers: WA token, Twilio auth token, FCM server key, etc.
    api_token_encrypted        = models.TextField(blank=True)
    # api_key_id covers: Twilio Account SID, WA phone number ID, APNS key ID
    api_key_id                 = models.CharField(max_length=255, blank=True)
    # webhook_secret for inbound payload verification
    webhook_secret_encrypted   = models.TextField(blank=True)

    # --- WhatsApp-specific ---
    whatsapp_phone_number_id   = models.CharField(max_length=64, blank=True)
    whatsapp_business_account_id = models.CharField(max_length=64, blank=True)
    whatsapp_api_version       = models.CharField(max_length=20, default='v19.0', blank=True)

    # --- SMS-specific ---
    sms_http_endpoint          = models.CharField(max_length=500, blank=True)
    sms_http_method            = models.CharField(max_length=10, default='POST', blank=True)

    # --- Push-specific ---
    push_vapid_public_key      = models.TextField(blank=True)
    push_vapid_private_key_encrypted = models.TextField(blank=True)
    push_fcm_project_id        = models.CharField(max_length=255, blank=True)

    # State
    is_active   = models.BooleanField(default=True, db_index=True)
    is_default  = models.BooleanField(default=True)

    # Free-form extra config (HTTP headers, regional settings, etc.)
    config_json = models.JSONField(default=dict, blank=True)

    # Audit
    metadata   = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label  = 'communications'
        db_table   = 'comms_tenant_channel_config'
        ordering   = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'channel_type', 'is_active']),
            models.Index(fields=['tenant_id', 'channel_type', 'is_deleted']),
        ]

    def __str__(self):
        return f'TenantChannelConfig({self.tenant_id}, channel={self.channel_type}, provider={self.provider})'

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    # ------------------------------------------------------------------
    # Class helpers
    # ------------------------------------------------------------------

    @classmethod
    def get_active(cls, tenant_id, channel_type: str) -> 'TenantChannelConfig | None':
        """Return the active config for (tenant_id, channel_type), or None."""
        return cls.objects.filter(
            tenant_id=tenant_id,
            channel_type=channel_type,
            is_active=True,
            is_deleted=False,
        ).order_by('-is_default', '-created_at').first()

    # ------------------------------------------------------------------
    # Decryption helpers — never log plain credentials
    # ------------------------------------------------------------------

    @property
    def decrypted_api_token(self) -> str:
        from apps.communications.utils import decrypt_string
        return decrypt_string(self.api_token_encrypted)

    @property
    def decrypted_webhook_secret(self) -> str:
        from apps.communications.utils import decrypt_string
        return decrypt_string(self.webhook_secret_encrypted)

    @property
    def decrypted_vapid_private_key(self) -> str:
        from apps.communications.utils import decrypt_string
        return decrypt_string(self.push_vapid_private_key_encrypted)

    def masked_api_token(self) -> str:
        from apps.communications.utils import redact_secret
        return redact_secret(self.decrypted_api_token)


# ---------------------------------------------------------------------------
# CommunicationDelivery
# ---------------------------------------------------------------------------

class CommunicationDeliveryStatus(models.TextChoices):
    PENDING   = 'pending',   'Pending'
    SENT      = 'sent',      'Sent'
    DELIVERED = 'delivered', 'Delivered'
    READ      = 'read',      'Read'
    FAILED    = 'failed',    'Failed'
    BOUNCED   = 'bounced',   'Bounced'
    DEFERRED  = 'deferred',  'Deferred'
    CANCELLED = 'cancelled', 'Cancelled'
    SKIPPED   = 'skipped',   'Skipped'


class CommunicationDeliveryPriority(models.TextChoices):
    LOW      = 'low',      'Low'
    MEDIUM   = 'medium',   'Medium'
    HIGH     = 'high',     'High'
    CRITICAL = 'critical', 'Critical'


class CommunicationDelivery(models.Model):
    """
    Unified delivery-attempt record for every outbound channel message
    (WhatsApp, SMS, Push).

    Email tracking uses EmailDelivery; this model covers all other channels
    and can be queried together with EmailDelivery for cross-channel views
    via channel_type.

    Lifecycle:
        PENDING  → SENT  → DELIVERED → READ       (happy path)
        PENDING  → FAILED → DEFERRED              (retry path)
        PENDING  → SKIPPED                        (channel disabled / no identifier)
        PENDING  → CANCELLED                      (notification read before delivery)

    Idempotency:
        Before creating a new record, callers should check for an existing
        PENDING or SENT record for the same (notification_id, channel_type,
        attempt_number) to avoid double-sends on Celery retries.
    """

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id       = models.UUIDField(db_index=True)

    # Link to the in-app notification that triggered this delivery (nullable
    # to support direct sends without a prior notification record)
    notification_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Link to the automation job that scheduled this delivery (nullable)
    automation_job_id = models.UUIDField(null=True, blank=True, db_index=True)

    channel_type    = models.CharField(
        max_length=20,
        choices=ChannelType.choices,
        db_index=True,
    )
    provider        = models.CharField(max_length=80, blank=True)

    # Who / what to deliver to
    recipient_identifier = models.CharField(
        max_length=255,
        blank=True,
        help_text='Normalised phone (E.164), push token, or user_id for push',
    )
    recipient_user_id    = models.UUIDField(null=True, blank=True, db_index=True)

    # What was sent
    template_used   = models.CharField(max_length=255, blank=True)
    rendered_body   = models.TextField(blank=True)
    rendered_subject = models.CharField(max_length=500, blank=True)

    # Status lifecycle
    status = models.CharField(
        max_length=20,
        choices=CommunicationDeliveryStatus.choices,
        default=CommunicationDeliveryStatus.PENDING,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=CommunicationDeliveryPriority.choices,
        default=CommunicationDeliveryPriority.MEDIUM,
        db_index=True,
    )

    # Delivery timing
    scheduled_for   = models.DateTimeField(null=True, blank=True, db_index=True)
    attempted_at    = models.DateTimeField(null=True, blank=True)
    delivered_at    = models.DateTimeField(null=True, blank=True)
    read_at         = models.DateTimeField(null=True, blank=True)
    failed_at       = models.DateTimeField(null=True, blank=True)

    # Retry tracking
    attempt_number  = models.PositiveSmallIntegerField(default=1)
    max_attempts    = models.PositiveSmallIntegerField(default=3)
    next_retry_at   = models.DateTimeField(null=True, blank=True)

    # Provider response data
    external_message_id      = models.CharField(max_length=255, blank=True)
    external_status_payload  = models.JSONField(default=dict, blank=True)
    error_message            = models.TextField(blank=True)

    # Skipped reason (e.g. 'channel_disabled', 'no_recipient_identifier')
    skip_reason = models.CharField(max_length=200, blank=True)

    # Audit
    metadata    = models.JSONField(default=dict, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'communications'
        db_table  = 'comms_communication_delivery'
        ordering  = ['-created_at']
        indexes   = [
            models.Index(fields=['tenant_id', 'channel_type', 'status']),
            models.Index(fields=['tenant_id', 'created_at']),
            models.Index(fields=['notification_id', 'channel_type']),
            models.Index(fields=['tenant_id', 'recipient_user_id', 'channel_type']),
            models.Index(fields=['automation_job_id']),
        ]

    def __str__(self):
        return (
            f'CommunicationDelivery({self.id}, '
            f'channel={self.channel_type}, '
            f'status={self.status}, '
            f'to={self.recipient_identifier})'
        )

    # ------------------------------------------------------------------
    # State transition helpers (mirrors EmailDelivery pattern)
    # ------------------------------------------------------------------

    def mark_sending(self):
        self.attempted_at = timezone.now()
        self.save(update_fields=['attempted_at', 'updated_at'])

    def mark_sent(self, external_message_id: str = '', payload: dict = None):
        self.status = CommunicationDeliveryStatus.SENT
        self.attempted_at = self.attempted_at or timezone.now()
        self.external_message_id = external_message_id
        if payload:
            self.external_status_payload = payload
        self.error_message = ''
        self.save(update_fields=[
            'status', 'attempted_at', 'external_message_id',
            'external_status_payload', 'error_message', 'updated_at',
        ])

    def mark_delivered(self, payload: dict = None):
        self.status = CommunicationDeliveryStatus.DELIVERED
        self.delivered_at = timezone.now()
        if payload:
            self.external_status_payload = payload
        self.save(update_fields=['status', 'delivered_at', 'external_status_payload', 'updated_at'])

    def mark_read(self):
        self.status = CommunicationDeliveryStatus.READ
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at', 'updated_at'])

    def mark_failed(self, error: str = '', payload: dict = None):
        self.status = CommunicationDeliveryStatus.FAILED
        self.failed_at = timezone.now()
        self.error_message = error[:2000] if error else ''
        if payload:
            self.external_status_payload = payload
        self.save(update_fields=[
            'status', 'failed_at', 'error_message',
            'external_status_payload', 'updated_at',
        ])

    def mark_deferred(self, next_retry_at, error: str = ''):
        self.status = CommunicationDeliveryStatus.DEFERRED
        self.error_message = error[:2000] if error else ''
        self.next_retry_at = next_retry_at
        self.attempt_number += 1
        self.save(update_fields=[
            'status', 'error_message', 'next_retry_at',
            'attempt_number', 'updated_at',
        ])

    def mark_cancelled(self, reason: str = ''):
        self.status = CommunicationDeliveryStatus.CANCELLED
        if reason:
            self.skip_reason = reason[:200]
        self.save(update_fields=['status', 'skip_reason', 'updated_at'])

    def mark_skipped(self, reason: str = ''):
        self.status = CommunicationDeliveryStatus.SKIPPED
        self.skip_reason = reason[:200] if reason else ''
        self.save(update_fields=['status', 'skip_reason', 'updated_at'])

    def can_retry(self) -> bool:
        return (
            self.attempt_number < self.max_attempts
            and self.status in (
                CommunicationDeliveryStatus.FAILED,
                CommunicationDeliveryStatus.DEFERRED,
            )
        )
