from rest_framework import serializers

from apps.communications.email_dispatch.types import EmailSendRequest
from apps.communications.models import EmailMessage


class EmailSendSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False)
    email_type = serializers.ChoiceField(choices=['system', 'business', 'user'])
    message_purpose = serializers.CharField(max_length=64)

    recipients = serializers.ListField(child=serializers.EmailField(), min_length=1)
    cc_emails = serializers.ListField(child=serializers.EmailField(), required=False)
    bcc_emails = serializers.ListField(child=serializers.EmailField(), required=False)

    related_object_type = serializers.CharField(required=False, allow_blank=True)
    related_object_id = serializers.UUIDField(required=False, allow_null=True)
    workflow_context_type = serializers.CharField(required=False, allow_blank=True)
    workflow_context_id = serializers.UUIDField(required=False, allow_null=True)

    subject = serializers.CharField(required=False, allow_blank=True)
    body_html = serializers.CharField(required=False, allow_blank=True)
    body_text = serializers.CharField(required=False, allow_blank=True)

    template_id = serializers.UUIDField(required=False, allow_null=True)
    quick_reply_template_id = serializers.UUIDField(required=False, allow_null=True)
    preferred_sender_account_id = serializers.UUIDField(required=False, allow_null=True)

    attachments = serializers.ListField(child=serializers.DictField(), required=False)
    variables = serializers.DictField(required=False)
    allow_fallback = serializers.BooleanField(required=False, default=True)
    track_delivery = serializers.BooleanField(required=False, default=True)
    schedule_at = serializers.DateTimeField(required=False, allow_null=True)
    reply_to_email = serializers.EmailField(required=False, allow_blank=True)

    def to_request(self, *, tenant_id, actor_user_id, trigger_source='manual') -> EmailSendRequest:
        validated = self.validated_data
        return EmailSendRequest(
            tenant_id=str(tenant_id),
            actor_user_id=str(actor_user_id) if actor_user_id else None,
            email_type=validated['email_type'],
            message_purpose=validated['message_purpose'],
            recipients=validated['recipients'],
            related_object_type=validated.get('related_object_type', ''),
            related_object_id=str(validated.get('related_object_id')) if validated.get('related_object_id') else None,
            workflow_context_type=validated.get('workflow_context_type', ''),
            workflow_context_id=str(validated.get('workflow_context_id')) if validated.get('workflow_context_id') else None,
            subject=validated.get('subject', ''),
            body_html=validated.get('body_html', ''),
            body_text=validated.get('body_text', ''),
            template_id=str(validated.get('template_id')) if validated.get('template_id') else None,
            quick_reply_template_id=str(validated.get('quick_reply_template_id')) if validated.get('quick_reply_template_id') else None,
            preferred_sender_account_id=str(validated.get('preferred_sender_account_id')) if validated.get('preferred_sender_account_id') else None,
            attachments=validated.get('attachments', []),
            variables=validated.get('variables', {}),
            allow_fallback=validated.get('allow_fallback', True),
            track_delivery=validated.get('track_delivery', True),
            schedule_at=validated.get('schedule_at'),
            cc_emails=validated.get('cc_emails', []),
            bcc_emails=validated.get('bcc_emails', []),
            reply_to_email=validated.get('reply_to_email', ''),
            trigger_source=trigger_source,
        )


class EmailMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailMessage
        fields = '__all__'
