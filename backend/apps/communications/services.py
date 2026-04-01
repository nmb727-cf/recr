from django.contrib.auth import get_user_model

from apps.communications.email_dispatch.dispatch import EmailDispatchService
from apps.communications.email_dispatch.types import EmailSendRequest
from apps.communications.models import EmailMessage, Notification
from shared.owner_contracts import OwnerActionContext, OwnerActionResult, OwnerContractError


class EmailRoutingService:
    """
    Backward-compatible facade.
    Existing code calls EmailRoutingService.send_email(...).
    Internally we now route via the new Communication Engine email architecture.
    """

    @staticmethod
    def send_email(
        subject,
        body_text,
        body_html,
        recipient_list,
        user_id=None,
        tenant_id=None,
        email_type='user',
        attachments=None,
        message_purpose='platform_notification',
    ):
        safe_tenant_id = str(tenant_id) if tenant_id else '00000000-0000-0000-0000-000000000000'
        request = EmailSendRequest(
            tenant_id=safe_tenant_id,
            actor_user_id=str(user_id) if user_id else None,
            email_type='system' if email_type == 'system' else 'business',
            message_purpose=message_purpose,
            recipients=recipient_list,
            subject=subject,
            body_text=body_text or '',
            body_html=body_html or '',
            attachments=attachments or [],
            allow_fallback=True,
            trigger_source='legacy_api',
        )
        message = EmailDispatchService.send_now(request)
        return message.status in {'sent', 'delivered', 'opened', 'clicked'}


class CommunicationDispatchService:
    ACTIVE_EMAIL_STATUSES = {'queued', 'sending', 'sent', 'delivered', 'opened', 'clicked'}

    @staticmethod
    def dispatch_notification(
        *,
        tenant_id,
        actor_user_id=None,
        recipient_user_ids=None,
        title: str,
        body: str = '',
        notification_type: str = 'platform_notification',
        action_url: str = '',
        related_entity_type: str = '',
        related_entity_id=None,
        expires_at=None,
        metadata=None,
        dedupe_key: str = '',
    ):
        recipient_user_ids = sorted({str(user_id) for user_id in (recipient_user_ids or []) if user_id})
        if not recipient_user_ids:
            return [], 0

        notifications = []
        created_count = 0
        metadata = dict(metadata or {})
        if dedupe_key:
            metadata.setdefault('orchestration_dedupe_key', dedupe_key)
        metadata.setdefault('external_source', 'orchestration_center')

        for user_id in recipient_user_ids:
            if dedupe_key:
                existing = Notification.objects.filter(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    notification_type=notification_type,
                    metadata__orchestration_dedupe_key=dedupe_key,
                ).first()
                if existing:
                    notifications.append(existing)
                    continue
            notifications.append(
                Notification.objects.create(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    action_url=action_url,
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id,
                    expires_at=expires_at,
                    metadata={
                        **metadata,
                        'actor_user_id': str(actor_user_id) if actor_user_id else '',
                    },
                )
            )
            created_count += 1
        return notifications, created_count

    @staticmethod
    def queue_email(request: EmailSendRequest):
        EmailDispatchService.queue_send(request)
        return request

    @staticmethod
    def dispatch_automation_notification(
        *,
        tenant_id,
        actor_user_id=None,
        recipient_user_ids=None,
        title: str,
        body: str = '',
        notification_type: str = 'platform_notification',
        action_url: str = '',
        related_entity_type: str = '',
        related_entity_id=None,
        expires_at=None,
        metadata=None,
        dedupe_key: str = '',
        notification_style: str = '',
    ):
        metadata = dict(metadata or {})
        if notification_style:
            metadata.setdefault('notification_style', notification_style)
        return CommunicationDispatchService.dispatch_notification(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            recipient_user_ids=recipient_user_ids,
            title=title,
            body=body,
            notification_type=notification_type,
            action_url=action_url,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            expires_at=expires_at,
            metadata=metadata,
            dedupe_key=dedupe_key,
        )

    @staticmethod
    def queue_automation_email(request: EmailSendRequest, *, dedupe_key: str = ''):
        if dedupe_key:
            request.metadata.setdefault('orchestration_dedupe_key', dedupe_key)
            request.metadata.setdefault('external_source', 'orchestration_center')
            existing = EmailMessage.objects.filter(
                tenant_id=request.tenant_id,
                status__in=CommunicationDispatchService.ACTIVE_EMAIL_STATUSES,
                metadata_json__orchestration_dedupe_key=dedupe_key,
            ).first()
            if existing:
                return existing, False
        CommunicationDispatchService.queue_email(request)
        return request, True

    @staticmethod
    def notify_from_orchestration(
        *,
        context: OwnerActionContext,
        recipient_user_ids=None,
        title: str,
        body: str = '',
        notification_type: str = 'platform_notification',
        action_url: str = '',
        related_entity_type: str = '',
        related_entity_id=None,
        expires_at=None,
        dedupe_key: str = '',
        notification_style: str = '',
    ):
        recipient_user_ids = [str(user_id) for user_id in (recipient_user_ids or []) if user_id]
        if not recipient_user_ids:
            raise OwnerContractError.validation('Notification contract requires at least one recipient user.')

        foreign_recipients = get_user_model().objects.filter(
            id__in=recipient_user_ids,
            is_deleted=False,
        ).exclude(tenant_id=context.tenant_id)
        if foreign_recipients.exists():
            raise OwnerContractError.ownership('Notification recipients must belong to the same tenant.')

        notifications, created_count = CommunicationDispatchService.dispatch_automation_notification(
            tenant_id=context.tenant_id,
            actor_user_id=context.actor_id,
            recipient_user_ids=recipient_user_ids,
            title=title,
            body=body,
            notification_type=notification_type,
            action_url=action_url,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            expires_at=expires_at,
            metadata=context.audit_metadata,
            dedupe_key=dedupe_key,
            notification_style=notification_style,
        )
        duplicate = bool(dedupe_key) and len(notifications) > 0 and created_count == 0
        return OwnerActionResult(
            owner_module='communications',
            action_family='notify',
            status='completed',
            target_type='notification',
            target_id=str(notifications[0].id) if notifications else '',
            duplicate=duplicate,
            audit_metadata=context.metadata_payload(
                channel='in_app',
                dedupe_key=dedupe_key,
                notification_type=notification_type,
                notification_style=notification_style,
            ),
            payload={
                'channel': 'in_app',
                'recipient_count': len(recipient_user_ids),
                'notification_count': len(notifications),
                'notification_ids': [str(item.id) for item in notifications],
            },
        )

    @staticmethod
    def enqueue_email_from_orchestration(
        *,
        context: OwnerActionContext,
        request: EmailSendRequest,
        dedupe_key: str = '',
    ):
        if str(request.tenant_id) != str(context.tenant_id):
            raise OwnerContractError.ownership('Queued email tenant must match the orchestration tenant.')
        if not request.recipients:
            raise OwnerContractError.validation('Queued email contract requires at least one recipient.')

        request.metadata = context.metadata_payload(**dict(request.metadata or {}))
        queued, created = CommunicationDispatchService.queue_automation_email(
            request,
            dedupe_key=dedupe_key,
        )
        return OwnerActionResult(
            owner_module='communications',
            action_family='enqueue_communication',
            status='queued',
            target_type='email_message',
            target_id=str(getattr(queued, 'id', '') or ''),
            duplicate=not created,
            audit_metadata=context.metadata_payload(
                channel='email',
                dedupe_key=dedupe_key,
                message_purpose=request.message_purpose,
            ),
            payload={
                'channel': 'email',
                'recipient_count': len(request.recipients or []),
                'email_message_id': str(getattr(queued, 'id', '') or ''),
                'template_slug': request.metadata.get('template_slug', ''),
                'scheduled_for': request.schedule_at.isoformat() if request.schedule_at else None,
            },
        )
