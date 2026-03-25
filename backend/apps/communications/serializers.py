from rest_framework import serializers
from apps.communications.models import MessageThread, Message, Notification, EmailTemplate, EmailAccount


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


class EmailAccountSerializer(serializers.ModelSerializer):
    smtp_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    oauth_token = serializers.JSONField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = EmailAccount
        fields = [
            'id', 'tenant_id', 'user_id', 'email_address', 'provider',
            'is_default', 'smtp_host', 'smtp_port', 'smtp_username',
            'smtp_password', 'smtp_encryption', 'from_name', 'signature',
            'oauth_token', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'user_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        from apps.communications.utils import encrypt_string, encrypt_json

        smtp_password = validated_data.pop('smtp_password', '')
        if smtp_password:
            validated_data['smtp_password'] = encrypt_string(smtp_password)

        oauth_token = validated_data.pop('oauth_token', None)
        if oauth_token:
            validated_data['oauth_token_encrypted'] = encrypt_json(oauth_token)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        from apps.communications.utils import encrypt_string, encrypt_json

        smtp_password = validated_data.pop('smtp_password', None)
        if smtp_password is not None:
            instance.smtp_password = encrypt_string(smtp_password)

        oauth_token = validated_data.pop('oauth_token', None)
        if oauth_token is not None:
            instance.oauth_token_encrypted = encrypt_json(oauth_token)

        return super().update(instance, validated_data)