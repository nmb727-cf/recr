from django.db import models

from shared.models import BaseModel


class WorkflowVersion(BaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('rolled_back', 'Rolled Back'),
    ]

    workflow_id = models.UUIDField(db_index=True)
    version_number = models.PositiveIntegerField(db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='draft', db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'wf_exec_versions'
        ordering = ['-version_number', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['workflow_id', 'version_number'], name='wf_exec_version_unique'),
        ]
        indexes = [
            models.Index(fields=['workflow_id', 'status']),
        ]


class WorkflowDraft(BaseModel):
    BUILDER_MODES = [
        ('guided', 'Guided'),
        ('advanced', 'Advanced'),
    ]
    STATUS_CHOICES = [
        ('editing', 'Editing'),
        ('ready_for_publish', 'Ready For Publish'),
        ('published', 'Published'),
        ('discarded', 'Discarded'),
    ]

    workflow_id = models.UUIDField(db_index=True)
    version = models.ForeignKey(
        WorkflowVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drafts',
    )
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    config_snapshot = models.JSONField(default=dict, blank=True)
    builder_mode = models.CharField(max_length=16, choices=BUILDER_MODES, default='guided', db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='editing', db_index=True)

    class Meta:
        db_table = 'wf_exec_drafts'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['workflow_id', 'status']),
        ]


class WorkflowVersionChangeLog(BaseModel):
    CHANGE_TYPES = [
        ('created', 'Created'),
        ('edited', 'Edited'),
        ('published', 'Published'),
        ('rolled_back', 'Rolled Back'),
        ('discarded', 'Discarded'),
        ('cloned', 'Cloned'),
    ]

    workflow_id = models.UUIDField(db_index=True)
    version = models.ForeignKey(
        WorkflowVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='change_logs',
    )
    change_type = models.CharField(max_length=16, choices=CHANGE_TYPES, db_index=True)
    changed_by = models.UUIDField(null=True, blank=True, db_index=True)
    change_summary = models.TextField(blank=True)

    class Meta:
        db_table = 'wf_exec_version_change_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_id', 'change_type']),
        ]


class WorkflowVersionComparison(BaseModel):
    workflow_id = models.UUIDField(db_index=True)
    from_version = models.ForeignKey(
        WorkflowVersion,
        on_delete=models.CASCADE,
        related_name='comparisons_from',
    )
    to_version = models.ForeignKey(
        WorkflowVersion,
        on_delete=models.CASCADE,
        related_name='comparisons_to',
    )
    comparison_result = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_exec_version_comparisons'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_id']),
        ]
