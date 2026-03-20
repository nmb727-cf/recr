from django.db import models
from shared.models import BaseModel

class Message(models.Model):
    thread_id = models.UUIDField(db_index=True)
    sender_id = models.UUIDField(db_index=True)
    recipient_id = models.UUIDField(null=True, blank=True)
    recipient_tenant_id = models.UUIDField(null=True, blank=True)
    message_type = models.CharField(max_length=50, choices=[
        ('text', 'Text'),
        ('file', 'File'),
        ('template', 'Template'),
        ('system', 'System'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('sms', 'SMS')
    ], default='text')
    content = models.TextField(blank=True)
    attachments = models.JSONField(default=list, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    related_entity_type = models.CharField(max_length=50, blank=True)
    related_entity_id = models.UUIDField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:50]

    class Meta:
        db_table = 'communications_message'
        ordering = ['-sent_at']

class Notification(models.Model):
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
    # Added the missing field below
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'communications_notification'
        ordering = ['-created_at']

class EmailTemplate(models.Model):
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=500)
    body_html = models.TextField()
    body_text = models.TextField(blank=True)
    template_type = models.CharField(max_length=100, blank=True)
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'communications_email_template'