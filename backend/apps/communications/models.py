import uuid
from django.db import models
from django.utils import timezone


class MessageThread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    subject = models.CharField(max_length=500, blank=True)
    created_by = models.UUIDField(null=True, blank=True)
    related_entity_type = models.CharField(max_length=50, blank=True)
    related_entity_id = models.UUIDField(null=True, blank=True)
    participant_ids = models.JSONField(default=list, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    class Meta:
        db_table = 'communications_thread'
        ordering = ['-last_message_at']


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    thread_id = models.UUIDField(db_index=True)
    sender_id = models.UUIDField(db_index=True)
    sender_tenant_id = models.UUIDField(null=True, blank=True)
    message_type = models.CharField(
        max_length=50,
        choices=[
            ('text', 'Text'), ('file', 'File'), ('template', 'Template'),
            ('system', 'System'), ('whatsapp', 'WhatsApp'),
            ('email', 'Email'), ('sms', 'SMS'),
        ],
        default='text'
    )
    content = models.TextField(blank=True)
    attachments = models.JSONField(default=list, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'communications_message'
        ordering = ['sent_at']


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    user_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    notification_type = models.CharField(max_length=100)
    action_url = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    related_entity_type = models.CharField(max_length=50, blank=True)
    related_entity_id = models.UUIDField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'communications_notification'
        ordering = ['-created_at']


# Legacy model kept for backward compatibility.
class EmailTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=500)
    body_html = models.TextField()
    body_text = models.TextField(blank=True)
    template_type = models.CharField(max_length=100, blank=True)
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    class Meta:
        db_table = 'communications_email_template'


# Legacy model kept for backward compatibility.
class EmailAccount(models.Model):
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('outlook', 'Outlook'),
        ('smtp', 'Custom SMTP'),
    ]

    ENCRYPTION_CHOICES = [
        ('none', 'None'),
        ('ssl', 'SSL'),
        ('tls', 'TLS'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(db_index=True)
    email_address = models.EmailField()
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    is_default = models.BooleanField(default=False)
    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.IntegerField(null=True, blank=True)
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_password = models.TextField(blank=True)
    smtp_encryption = models.CharField(max_length=10, choices=ENCRYPTION_CHOICES, default='tls')
    from_name = models.CharField(max_length=255, blank=True)
    signature = models.TextField(blank=True)
    oauth_token_encrypted = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            EmailAccount.objects.filter(user_id=self.user_id, is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def decrypted_smtp_password(self):
        from apps.communications.utils import decrypt_string
        return decrypt_string(self.smtp_password)

    @property
    def oauth_token(self):
        from apps.communications.utils import decrypt_json
        return decrypt_json(self.oauth_token_encrypted)

    class Meta:
        db_table = 'communications_email_account'
        unique_together = ('user_id', 'email_address')


class EmailProviderType(models.TextChoices):
    SYSTEM = 'system', 'System'
    GMAIL_OAUTH = 'gmail_oauth', 'Gmail OAuth'
    MICROSOFT_OAUTH = 'microsoft_oauth', 'Microsoft OAuth'
    SMTP = 'smtp', 'SMTP'


class EmailAccountScope(models.TextChoices):
    USER = 'user', 'User'
    TENANT_SHARED = 'tenant_shared', 'Tenant Shared'
    SYSTEM = 'system', 'System'


class EmailAccountStatus(models.TextChoices):
    CONNECTED = 'connected', 'Connected'
    EXPIRED = 'expired', 'Expired'
    DISCONNECTED = 'disconnected', 'Disconnected'
    ERROR = 'error', 'Error'
    PENDING = 'pending', 'Pending'


class EmailHealthStatus(models.TextChoices):
    HEALTHY = 'healthy', 'Healthy'
    DEGRADED = 'degraded', 'Degraded'
    UNHEALTHY = 'unhealthy', 'Unhealthy'
    UNKNOWN = 'unknown', 'Unknown'


class EmailSendingAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)

    provider_type = models.CharField(max_length=32, choices=EmailProviderType.choices)
    account_scope = models.CharField(max_length=32, choices=EmailAccountScope.choices, default=EmailAccountScope.USER)

    email_address = models.EmailField(db_index=True)
    display_name = models.CharField(max_length=255, blank=True)
    from_name = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=20, choices=EmailAccountStatus.choices, default=EmailAccountStatus.PENDING)
    is_default_sender = models.BooleanField(default=False, db_index=True)
    can_send = models.BooleanField(default=True)
    can_receive = models.BooleanField(default=False)

    access_token_encrypted = models.TextField(blank=True)
    refresh_token_encrypted = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.IntegerField(null=True, blank=True)
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_password_encrypted = models.TextField(blank=True)
    smtp_encryption_mode = models.CharField(max_length=10, blank=True)

    signature_html = models.TextField(blank=True)
    signature_text = models.TextField(blank=True)

    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    health_status = models.CharField(max_length=20, choices=EmailHealthStatus.choices, default=EmailHealthStatus.UNKNOWN)

    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'communications_email_accounts'
        indexes = [
            models.Index(fields=['tenant_id', 'user_id', 'is_default_sender']),
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'provider_type']),
        ]


class EmailAccountPermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    email_account = models.ForeignKey(EmailSendingAccount, on_delete=models.CASCADE, related_name='permissions')
    user_id = models.UUIDField(db_index=True)
    can_send = models.BooleanField(default=True)
    can_manage = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'communications_email_account_permissions'
        unique_together = ('email_account', 'user_id')


class EmailTemplateScope(models.TextChoices):
    SYSTEM_DEFAULT = 'system_default', 'System Default'
    TENANT_CUSTOM = 'tenant_custom', 'Tenant Custom'
    USER_PERSONAL = 'user_personal', 'User Personal'


class EmailTemplateType(models.TextChoices):
    SYSTEM = 'system', 'System'
    BUSINESS = 'business', 'Business'
    QUICK_REPLY = 'quick_reply', 'Quick Reply'


class EmailChannel(models.TextChoices):
    EMAIL = 'email', 'Email'


class EmailTemplateDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    template_scope = models.CharField(max_length=32, choices=EmailTemplateScope.choices)
    template_type = models.CharField(max_length=32, choices=EmailTemplateType.choices)
    channel = models.CharField(max_length=16, choices=EmailChannel.choices, default=EmailChannel.EMAIL)

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    category = models.CharField(max_length=120, blank=True)

    subject_template = models.CharField(max_length=500, blank=True)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True)

    variables_schema_json = models.JSONField(default=dict, blank=True)
    usage_context_json = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    is_system_locked = models.BooleanField(default=False)
    language_code = models.CharField(max_length=10, default='en')
    version = models.IntegerField(default=1)

    parent_template = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    created_by = models.UUIDField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'communications_email_templates'
        unique_together = ('tenant_id', 'slug', 'language_code', 'version')
        indexes = [
            models.Index(fields=['tenant_id', 'template_type', 'is_active']),
            models.Index(fields=['tenant_id', 'category']),
        ]


class QuickReplyTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=120, blank=True)
    subject_template = models.CharField(max_length=500, null=True, blank=True)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True)
    variables_schema_json = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'communications_quick_reply_templates'
        indexes = [models.Index(fields=['tenant_id', 'user_id', 'is_active'])]


class EmailRouteUsed(models.TextChoices):
    USER_EMAIL = 'user_email', 'User Email'
    SYSTEM_EMAIL_FALLBACK = 'system_email_fallback', 'System Email Fallback'


class EmailMessageStatus(models.TextChoices):
    QUEUED = 'queued', 'Queued'
    SENDING = 'sending', 'Sending'
    SENT = 'sent', 'Sent'
    DELIVERED = 'delivered', 'Delivered'
    FAILED = 'failed', 'Failed'
    BOUNCED = 'bounced', 'Bounced'
    OPENED = 'opened', 'Opened'
    CLICKED = 'clicked', 'Clicked'


class EmailMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    related_object_type = models.CharField(max_length=80, blank=True)
    related_object_id = models.UUIDField(null=True, blank=True)

    workflow_context_type = models.CharField(max_length=80, blank=True)
    workflow_context_id = models.UUIDField(null=True, blank=True)

    sender_account = models.ForeignKey(EmailSendingAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='sent_messages')
    actual_route_used = models.CharField(max_length=40, choices=EmailRouteUsed.choices)

    from_email = models.EmailField()
    from_name = models.CharField(max_length=255, blank=True)
    reply_to_email = models.EmailField(blank=True)

    to_emails = models.JSONField(default=list, blank=True)
    cc_emails = models.JSONField(default=list, blank=True)
    bcc_emails = models.JSONField(default=list, blank=True)

    subject = models.CharField(max_length=500)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True)

    template = models.ForeignKey(EmailTemplateDefinition, null=True, blank=True, on_delete=models.SET_NULL)
    quick_reply_template = models.ForeignKey(QuickReplyTemplate, null=True, blank=True, on_delete=models.SET_NULL)

    message_purpose = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=20, choices=EmailMessageStatus.choices, default=EmailMessageStatus.QUEUED, db_index=True)

    provider_message_id = models.CharField(max_length=255, blank=True)
    provider_thread_id = models.CharField(max_length=255, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    triggered_by_user_id = models.UUIDField(null=True, blank=True)
    triggered_by_event_id = models.CharField(max_length=255, blank=True)

    trigger_source = models.CharField(max_length=20, default='manual')
    metadata_json = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'communications_email_messages'
        indexes = [
            models.Index(fields=['tenant_id', 'created_at']),
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'related_object_type', 'related_object_id']),
        ]


class EmailAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_message = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='attachments')
    file_id = models.CharField(max_length=255, blank=True)
    storage_path = models.TextField(blank=True)
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=255, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'communications_email_attachments'


class EmailDeliveryEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    email_message = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='delivery_events')
    provider_type = models.CharField(max_length=32)
    event_type = models.CharField(max_length=32)
    raw_payload_json = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'communications_email_delivery_events'
        indexes = [models.Index(fields=['tenant_id', 'event_type', 'occurred_at'])]


class EmailPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    default_sender_account = models.ForeignKey(EmailSendingAccount, null=True, blank=True, on_delete=models.SET_NULL)
    fallback_behavior = models.CharField(max_length=64, default='system_fallback_with_label')
    default_signature_mode = models.CharField(max_length=64, default='account_signature')
    allow_system_fallback = models.BooleanField(default=True)
    banner_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'communications_email_preferences'
        unique_together = ('tenant_id', 'user_id')


class EmailUsageAudit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    actor_user_id = models.UUIDField(null=True, blank=True, db_index=True)
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80)
    target_id = models.CharField(max_length=255, blank=True)
    details_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'communications_email_usage_audit'
        indexes = [models.Index(fields=['tenant_id', 'action', 'created_at'])]
