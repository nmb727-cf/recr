from django_tenants.models import TenantMixin, DomainMixin
from django.db import models

class Client(TenantMixin, models.Model):
    name = models.CharField(max_length=255)
    tenant_type = models.CharField(
        max_length=20,
        choices=[('company', 'Company'), ('agency', 'Agency'), ('candidate_pool', 'Candidate Pool')],
        default='company'
    )
    slug = models.SlugField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('active', 'Active'), ('suspended', 'Suspended'), ('terminated', 'Terminated')],
        default='pending'
    )
    country_code = models.CharField(max_length=5, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    logo_url = models.TextField(blank=True)
    website = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    size_range = models.CharField(max_length=50, blank=True)
    master_id = models.UUIDField(null=True, blank=True)
    is_master = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    reference_prefix_auto = models.CharField(max_length=12, unique=True, blank=True, null=True)
    reference_prefix_custom = models.CharField(max_length=12, blank=True, null=True)
    auto_create_schema = True

    @property
    def effective_reference_prefix(self):
        if self.reference_prefix_custom:
            return self.reference_prefix_custom
        return self.reference_prefix_auto

    def __str__(self):
        return self.name


class TenantReferenceSequence(models.Model):
    ENTITY_TYPE_CHOICES = [
        ('CC', 'Company Candidate'),
        ('AC', 'Agency Candidate'),
        ('DC', 'Direct Candidate'),
        ('CJ', 'Company Job'),
        ('AJ', 'Agency Job'),
    ]

    tenant_id = models.UUIDField(db_index=True)
    entity_type = models.CharField(max_length=2, choices=ENTITY_TYPE_CHOICES)
    year_suffix = models.CharField(max_length=2, db_index=True)
    next_value = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenants_reference_sequence'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'entity_type', 'year_suffix'],
                name='uniq_ref_seq_tenant_type_year',
            ),
        ]


class Domain(DomainMixin):
    def __str__(self):
        return self.domain


class PlatformSetting(models.Model):
    key = models.CharField(max_length=120, unique=True, db_index=True)
    category = models.CharField(max_length=80, default='general', db_index=True)
    value_json = models.JSONField(default=dict, blank=True)
    description = models.TextField(blank=True)
    is_editable = models.BooleanField(default=True)
    updated_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenants_platform_setting'
        ordering = ['category', 'key']

    def __str__(self):
        return self.key
