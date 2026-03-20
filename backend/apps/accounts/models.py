from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone

class CustomUser(AbstractUser):
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    phone_verified = models.BooleanField(default=False)
    avatar_url = models.TextField(blank=True)
    role = models.CharField(
        max_length=50,
        default='viewer',
        choices=[
            ('super_admin', 'Super Admin'),
            ('tenant_admin', 'Tenant Admin'),
            ('hr_manager', 'HR Manager'),
            ('hiring_manager', 'Hiring Manager'),
            ('recruiter', 'Recruiter'),
            ('interviewer', 'Interviewer'),
            ('agency_owner', 'Agency Owner'),
            ('agency_recruiter', 'Agency Recruiter'),
            ('candidate', 'Candidate'),
            ('viewer', 'Viewer')
        ]
    )
    is_active = models.BooleanField(default=True)
    last_login_ip = models.CharField(max_length=45, blank=True)
    mfa_enabled = models.BooleanField(default=False)
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    ui_preferences = models.JSONField(default=dict, blank=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'accounts_user'

# Reminder to set AUTH_USER_MODEL = 'accounts.CustomUser' in settings.py
