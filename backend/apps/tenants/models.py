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
    auto_create_schema = True

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    def __str__(self):
        return self.domain
