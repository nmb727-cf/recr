import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.candidates.models import Candidate

class TalentPool(models.Model):
    TENANT_TYPE_CHOICES = [
        ('company', 'Company'),
        ('agency', 'Agency'),
    ]
    POOL_TYPE_CHOICES = [
        ('manual', 'Manual'),
        ('smart', 'Smart'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    tenant_type = models.CharField(max_length=20, choices=TENANT_TYPE_CHOICES, default='company')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    pool_type = models.CharField(max_length=20, choices=POOL_TYPE_CHOICES, default='manual')
    color = models.CharField(max_length=50, blank=True, help_text="Hex code or color name for UI indicator")
    is_active = models.BooleanField(default=True)
    created_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    filters_json = models.JSONField(default=dict, blank=True, help_text="Search filters for smart pools")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Talent Pool"
        verbose_name_plural = "Talent Pools"
        unique_together = ('tenant_id', 'slug')

    def __str__(self):
        return f"{self.name} ({self.tenant_id})"

class CandidateTalentPoolMembership(models.Model):
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('rule', 'Rule'),
        ('import', 'Import'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    talent_pool = models.ForeignKey(
        TalentPool, on_delete=models.CASCADE, related_name='memberships'
    )
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name='pool_memberships'
    )
    added_by = models.UUIDField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = "Candidate Talent Pool Membership"
        verbose_name_plural = "Candidate Talent Pool Memberships"
        unique_together = ('candidate', 'talent_pool', 'tenant_id')

    def __str__(self):
        return f"{self.candidate} in {self.talent_pool}"


class TalentPoolActivity(models.Model):
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('system', 'System'),
        ('rule', 'Rule'),
        ('import', 'Import'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    talent_pool = models.ForeignKey(
        TalentPool, on_delete=models.CASCADE, related_name='activity_events'
    )
    event_type = models.CharField(max_length=100, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='talent_pool_activity_events'
    )
    payload = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'talent_pool_activity_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'talent_pool', '-created_at']),
            models.Index(fields=['event_type']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.talent_pool_id}"
