from django.dispatch import receiver

from apps.core import events

from apps.communications.email_dispatch.dispatch import EmailDispatchService
from apps.communications.email_dispatch.types import EmailSendRequest


class EmailEventConsumers:
    @staticmethod
    def handle_event(*, event_name: str, tenant_id, actor_user_id=None, recipients=None, subject='', body_text='', body_html='', message_purpose='platform_notification', related_object_type='', related_object_id=None, variables=None):
        recipients = recipients or []
        if not recipients:
            return None

        request = EmailSendRequest(
            tenant_id=str(tenant_id),
            actor_user_id=str(actor_user_id) if actor_user_id else None,
            email_type='business' if message_purpose not in {'otp', 'password_reset', 'email_verification'} else 'system',
            message_purpose=message_purpose,
            recipients=recipients,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            related_object_type=related_object_type,
            related_object_id=str(related_object_id) if related_object_id else None,
            trigger_source='event',
            triggered_by_event_id=event_name,
            variables=variables or {},
        )
        EmailDispatchService.queue_send(request)
        return request


@receiver(events.application.created)
def on_application_submitted(sender, **kwargs):
    app = kwargs.get('application')
    user = kwargs.get('user')
    if not app:
        return

    recipient = kwargs.get('recipient_email')
    if not recipient:
        return

    EmailEventConsumers.handle_event(
        event_name='application.submitted',
        tenant_id=app.tenant_id,
        actor_user_id=getattr(user, 'id', None),
        recipients=[recipient],
        subject='Application received',
        body_text='Your application has been received.',
        message_purpose='platform_notification',
        related_object_type='application',
        related_object_id=app.id,
    )


@receiver(events.application.stage_changed)
def on_application_stage_changed(sender, **kwargs):
    app = kwargs.get('application')
    user = kwargs.get('user')
    recipient = kwargs.get('recipient_email')
    if not app or not recipient:
        return

    EmailEventConsumers.handle_event(
        event_name='application.stage_changed',
        tenant_id=app.tenant_id,
        actor_user_id=getattr(user, 'id', None),
        recipients=[recipient],
        subject='Application stage updated',
        body_text='There is an update to your application stage.',
        message_purpose='shortlist_notification',
        related_object_type='application',
        related_object_id=app.id,
    )


@receiver(events.application.shortlisted)
def on_application_shortlisted(sender, **kwargs):
    app = kwargs.get('application')
    user = kwargs.get('user')
    recipient = kwargs.get('recipient_email')
    if not app or not recipient:
        return

    EmailEventConsumers.handle_event(
        event_name='application.shortlisted',
        tenant_id=app.tenant_id,
        actor_user_id=getattr(user, 'id', None),
        recipients=[recipient],
        subject='You have been shortlisted',
        body_text='Great news, you have been shortlisted.',
        message_purpose='shortlist_notification',
        related_object_type='application',
        related_object_id=app.id,
    )


@receiver(events.onboarding.completed)
def on_onboarding_completed(sender, **kwargs):
    user = kwargs.get('user')
    if not user:
        return

    EmailEventConsumers.handle_event(
        event_name='onboarding.completed',
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        recipients=[user.email],
        subject='Welcome to TalentOS',
        body_text='Your onboarding is complete. You can optionally connect your work email in settings.',
        message_purpose='platform_notification',
        related_object_type='user',
        related_object_id=user.id,
    )
