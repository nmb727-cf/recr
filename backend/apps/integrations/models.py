from django.db import models
from shared.models import BaseModel

class IntegrationCategory(models.TextChoices):
    HRMS = 'hrms', 'HRMS'
    EMAIL = 'email', 'Email'
    CALENDAR = 'calendar', 'Calendar'
    JOB_BOARD = 'job_board', 'Job Board'
    ASSESSMENT = 'assessment', 'Assessment Tool'
    BACKGROUND_VERIFICATION = 'background_verification', 'Background Verification'
    PAYROLL = 'payroll', 'Payroll'
    OFFER = 'offer', 'Offer Tool'

class IntegrationStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    ERROR = 'error', 'Error'
    PENDING = 'pending', 'Pending'

class Integration(BaseModel):
    name = models.CharField(max_length=100)
    provider_key = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=50, choices=IntegrationCategory.choices, db_index=True)
    status = models.CharField(max_length=20, choices=IntegrationStatus.choices, default=IntegrationStatus.INACTIVE, db_index=True)
    config_json = models.JSONField(default=dict, blank=True)
    auth_data_json = models.JSONField(default=dict, blank=True)
    is_connected = models.BooleanField(default=False)
    last_sync_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'icc_integrations'
        unique_together = ('tenant_id', 'provider_key')

    def __str__(self):
        return f'{self.name} ({self.provider_key})'
