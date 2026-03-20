from rest_framework import serializers
from apps.communications.models import MessageThread, Message, Notification, EmailTemplate


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            'id', 'tenant_id', 'thread_id', 'sender_id', 'sender_tenant_id',
            'message_type', 'content', 'attachments',
            'is_read', 'read_at', 'sent_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'thread_id', 'sender_id', 'sent_at']


class MessageThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageThread
        fields = [
            'id', 'tenant_id', 'subject', 'created_by',
            'related_entity_type', 'related_entity_id',
            'participant_ids', 'last_message_at',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'tenant_id', 'user_id', 'title', 'body',
            'notification_type', 'action_url',
            'is_read', 'read_at', 'related_entity_type',
            'related_entity_id', 'expires_at', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'tenant_id', 'name', 'subject', 'body_html', 'body_text',
            'template_type', 'variables', 'is_active', 'is_system',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at', 'is_system']