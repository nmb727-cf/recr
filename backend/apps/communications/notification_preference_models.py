"""
User Notification Preferences — Models
=======================================
Allows individual users to control their notification experience within
the constraints set by the tenant admin and system defaults.

Hierarchy:
  1. System Default Rule (e.g. Interview scheduled is HIGH priority)
  2. Tenant Override Rule (e.g. Interview scheduled is CRITICAL priority)
  3. User Preference Override (e.g. I don't want interview emails)
"""
import uuid
from django.db import models
from django.utils import timezone


class UserNotificationPreference(models.Model):
    """
    Per-user, per-category, per-channel preference.
    
    Example:
        user_id='...', category='interview', channel_type='email', is_enabled=False
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(db_index=True)
    
    # Matches NotificationRuleCategory (interview, application, etc.)
    category = models.CharField(max_length=40, db_index=True)
    
    # Matches NotificationChannelSetting.CHANNEL_CHOICES (in_app, email, etc.)
    channel_type = models.CharField(max_length=20, db_index=True)
    
    is_enabled = models.BooleanField(default=True)
    
    # Minimum priority level to receive for this category/channel
    # If notification priority < min_priority, it's suppressed.
    # Choices: info, medium, high, critical
    min_priority = models.CharField(max_length=20, default='info')
    
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comms_user_notification_preference'
        unique_together = ('user_id', 'category', 'channel_type')
        indexes = [
            models.Index(fields=['user_id', 'category', 'is_enabled']),
        ]


class UserNotificationSetting(models.Model):
    """
    Global notification settings for a specific user.
    """
    DIGEST_MODE_CHOICES = [
        ('none',      'None (Immediate)'),
        ('hourly',    'Hourly Digest'),
        ('daily',     'Daily Digest'),
        ('weekly',    'Weekly Digest'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(unique=True, db_index=True)
    
    # Quiet Hours (stored in user's timezone)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Digest Preferences
    digest_mode = models.CharField(max_length=20, choices=DIGEST_MODE_CHOICES, default='none')
    
    # Global Channel Overrides (e.g. "Turn off ALL SMS")
    all_email_enabled = models.BooleanField(default=True)
    all_sms_enabled = models.BooleanField(default=True)
    all_whatsapp_enabled = models.BooleanField(default=True)
    all_push_enabled = models.BooleanField(default=True)
    
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comms_user_notification_setting'
