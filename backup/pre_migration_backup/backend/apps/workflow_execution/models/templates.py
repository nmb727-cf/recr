from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from shared.models import BaseModel


class WorkflowTemplate(BaseModel):
    TEMPLATE_TYPES = [
        ('system', 'System'),
        ('company', 'Company'),
        ('agency', 'Agency'),
        ('custom', 'Custom'),
    ]
    VISIBILITY_TYPES = [
        ('private', 'Private'),
        ('organization', 'Organization'),
        ('public', 'Public'),
    ]
    CATEGORIES = [
        ('standard_hiring', 'Standard Hiring'),
        ('high_volume_hiring', 'High Volume Hiring'),
        ('executive_hiring', 'Executive Hiring'),
        ('agency_hiring', 'Agency Hiring'),
        ('campus_hiring', 'Campus Hiring'),
        ('contract_hiring', 'Contract Hiring'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64, choices=CATEGORIES, default='custom', db_index=True)
    template_type = models.CharField(max_length=16, choices=TEMPLATE_TYPES, default='custom', db_index=True)
    visibility = models.CharField(max_length=16, choices=VISIBILITY_TYPES, default='private', db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_templates'
        ordering = ['category', 'name', '-updated_at']
        indexes = [
            models.Index(fields=['template_type', 'visibility', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]


class WorkflowTemplateVersion(BaseModel):
    template = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.CASCADE,
        related_name='versions',
    )
    version_number = models.PositiveIntegerField(db_index=True)
    config_snapshot = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_template_versions'
        ordering = ['-version_number', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['template', 'version_number'],
                name='wf_exec_template_version_unique',
            ),
        ]


class WorkflowTemplateUsage(BaseModel):
    template = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.CASCADE,
        related_name='usages',
    )
    workflow_id = models.UUIDField(db_index=True)
    used_by = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'wf_exec_template_usage'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['template', 'tenant_id']),
            models.Index(fields=['workflow_id', 'tenant_id']),
        ]


class WorkflowTemplateRating(BaseModel):
    template = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.CASCADE,
        related_name='ratings',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True,
    )
    review = models.TextField(blank=True)

    class Meta:
        db_table = 'wf_exec_template_ratings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['template', 'rating']),
        ]
