from rest_framework import serializers

from apps.communications.models import EmailTemplateDefinition, QuickReplyTemplate


class EmailTemplateDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplateDefinition
        fields = [
            'id', 'tenant_id', 'template_scope', 'template_type', 'channel',
            'name', 'slug', 'category', 'subject_template', 'body_html', 'body_text',
            'variables_schema_json', 'usage_context_json',
            'is_active', 'is_system_locked', 'language_code', 'version',
            'parent_template', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_by', 'created_at', 'updated_at', 'is_system_locked']


class QuickReplyTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickReplyTemplate
        fields = [
            'id', 'tenant_id', 'user_id', 'name', 'category', 'subject_template',
            'body_html', 'body_text', 'variables_schema_json', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'user_id', 'created_at', 'updated_at']
