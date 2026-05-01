from rest_framework import serializers
from apps.communications.models import (
    Message, MessageThread, Notification, NotificationDelivery,
    ThreadParticipant, EmailTemplate, EmailAccount,
)


class ThreadParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreadParticipant
        fields = [
            'id', 'user_id', 'participant_type', 'external_tenant_id',
            'last_read_at', 'is_muted', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    # Expose canonical `body` but also read legacy `content` so old clients keep working
    body = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'tenant_id', 'sender_id', 'sender_tenant_id',
            'message_type', 'channel_type',
            'body', 'content',  # content kept for backward compat
            'attachments_json', 'attachments',
            'related_entity_type', 'related_entity_id',
            'is_read', 'read_at',
            'is_system_generated', 'is_deleted',
            'sent_at', 'delivered_at',
            'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'sender_id', 'sent_at',
            'is_deleted', 'is_system_generated',
        ]

    def get_body(self, obj):
        return obj.body or obj.content


class MessageThreadSerializer(serializers.ModelSerializer):
    participants = ThreadParticipantSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = [
            'id', 'tenant_id', 'thread_type', 'subject',
            'is_internal', 'is_archived',
            'created_by', 'related_entity_type', 'related_entity_id',
            'participant_ids', 'participants',
            'last_message_at', 'last_message_preview',
            'unread_count',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        return obj.messages.filter(
            is_deleted=False,
            is_read=False,
        ).exclude(sender_id=request.user.id).count()


class MessageThreadCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=500, required=False, default='')
    thread_type = serializers.CharField(max_length=40, required=False, default='general')
    is_internal = serializers.BooleanField(required=False, default=True)
    related_entity_type = serializers.CharField(max_length=80, required=False, default='')
    related_entity_id = serializers.UUIDField(required=False, allow_null=True)
    participant_user_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )
    message = serializers.CharField(required=True)


class NotificationDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationDelivery
        fields = [
            'id', 'channel', 'provider', 'status',
            'attempted_at', 'delivered_at', 'failed_at',
            'external_message_id', 'error_message',
        ]
        read_only_fields = [
            'id', 'attempted_at', 'delivered_at', 'failed_at', 'external_message_id',
        ]


class NotificationSerializer(serializers.ModelSerializer):
    notification_type = serializers.SerializerMethodField()
    deliveries = NotificationDeliverySerializer(many=True, read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'tenant_id', 'user_id', 'type', 'notification_type',
            'title', 'body', 'severity', 'action_url',
            'is_read', 'read_at',
            'related_entity_type', 'related_entity_id',
            'fallback_email_sent_at', 'escalation_level',
            'expires_at', 'created_at', 'updated_at',
            'deliveries',
            'metadata',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'read_at',
            'fallback_email_sent_at', 'escalation_level',
        ]

    def get_notification_type(self, obj):
        return obj.get_type()


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