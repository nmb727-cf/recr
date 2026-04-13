"""
Translation models.

Two concerns are kept separate:

1. TranslationOverride
   DB-backed overrides for system UI translation strings.
   Layered on top of the static JSON files shipped with the frontend.

   Use cases:
   - Tenant custom labels ("Candidates" → "Talent" for one client)
   - Global corrections without a frontend deploy
   - New language additions driven by admin UI

   Hierarchy: tenant override > global override > static JSON file

2. ContentTranslation
   Stores translated copies of user-generated content.

   IMMUTABILITY RULE: this table NEVER modifies the source record.
   Original content lives on the source model untouched.
   This table stores additional translated copies only.

   Entities recommended for future support:
   - candidates.note          (note body)
   - jobs.job                 (description, requirements)
   - candidates.candidate     (summary, profile_headline)
   - interviews.feedback      (comments, strengths, concerns)
   - communications.message   (body)
   - communications.template  (subject, body)
"""
import uuid
from django.db import models


class TranslationOverride(models.Model):
    """DB-backed override for a single translation key in a given language."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # The dotted key matching the frontend JSON path, e.g. "sidebar.candidates"
    key = models.CharField(max_length=255, db_index=True)

    language_code = models.CharField(max_length=10, db_index=True)   # "en", "hi", "fr"
    value = models.TextField()

    # Optional grouping to filter overrides by module on the API
    module = models.CharField(max_length=100, blank=True, db_index=True)

    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # NULL = global (all tenants); UUID = tenant-specific override
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'translations_override'
        unique_together = [('key', 'language_code', 'tenant_id')]
        ordering = ['module', 'key', 'language_code']

    def __str__(self):
        scope = f'tenant:{self.tenant_id}' if self.tenant_id else 'global'
        return f'[{self.language_code}] {self.key} ({scope})'


class ContentTranslation(models.Model):
    """
    Translated copy of a user-generated content field.

    Source model must expose:
        <field_name>           — the original text (immutable, never modified here)
        <field_name>_language  — detected or user-declared language code (optional)

    This record stores the translated copy only.
    """

    TRANSLATION_SOURCE_CHOICES = [
        ('machine', 'Machine (auto)'),
        ('human', 'Human reviewed'),
        ('user', 'User provided'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identifies the source record — uses app_label.ModelName convention
    # e.g. "candidates.note", "jobs.job", "interviews.feedback"
    content_type = models.CharField(max_length=100, db_index=True)
    object_id = models.UUIDField(db_index=True)

    # Which field on the source model was translated
    field_name = models.CharField(max_length=100)

    original_language = models.CharField(max_length=10)       # "en", "hi"
    translated_language = models.CharField(max_length=10, db_index=True)
    translated_content = models.TextField()

    translation_source = models.CharField(
        max_length=20,
        choices=TRANSLATION_SOURCE_CHOICES,
        default='machine',
    )
    is_verified = models.BooleanField(default=False)

    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'translations_content'
        unique_together = [('content_type', 'object_id', 'field_name', 'translated_language')]
        indexes = [
            models.Index(fields=['content_type', 'object_id'], name='trans_content_lookup'),
        ]

    def __str__(self):
        return f'{self.content_type}:{self.object_id} [{self.field_name}] → {self.translated_language}'
