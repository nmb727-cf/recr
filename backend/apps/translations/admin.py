from django.contrib import admin
from apps.translations.models import TranslationOverride, ContentTranslation


@admin.register(TranslationOverride)
class TranslationOverrideAdmin(admin.ModelAdmin):
    list_display = ['key', 'language_code', 'module', 'tenant_id', 'is_active', 'updated_at']
    list_filter = ['language_code', 'module', 'is_active']
    search_fields = ['key', 'value', 'description']
    ordering = ['module', 'key', 'language_code']


@admin.register(ContentTranslation)
class ContentTranslationAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'object_id', 'field_name', 'original_language',
                    'translated_language', 'translation_source', 'is_verified', 'updated_at']
    list_filter = ['content_type', 'translated_language', 'translation_source', 'is_verified']
    search_fields = ['content_type', 'translated_content']
    ordering = ['-updated_at']
