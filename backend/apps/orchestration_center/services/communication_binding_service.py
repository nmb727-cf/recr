import uuid

from apps.communications.email_dispatch.types import EmailSendRequest
from apps.communications.services import CommunicationDispatchService
from apps.communications.models import EmailTemplateDefinition
from shared.owner_contracts import OwnerActionContext


class CommunicationBindingService:
    @staticmethod
    def _build_dedupe_key(*, run, action_type: str, config: dict):
        return config.get('dedupe_key') or f'{run.id}:{action_type}:{config.get("notification_type", config.get("message_purpose", "platform_notification"))}'

    @staticmethod
    def queue_email_from_automation(*, run, action_type: str, config: dict, schedule_at=None):
        recipients = CommunicationBindingService._resolve_recipients(
            payload=run.trigger_payload_json or {},
            config=config,
        )
        if not recipients:
            return {
                'action_type': action_type,
                'status': 'skipped',
                'reason': 'recipients_missing',
            }

        template = CommunicationBindingService._resolve_template(
            tenant_id=run.tenant_id,
            template_slug=config.get('template_key') or config.get('template_slug', ''),
        )
        if not template and not any(config.get(key) for key in ('subject', 'body_text', 'body_html')):
            return {
                'action_type': action_type,
                'status': 'skipped',
                'reason': 'template_missing',
            }

        request = EmailSendRequest(
            tenant_id=str(run.tenant_id),
            actor_user_id=str(run.created_by) if run.created_by else None,
            email_type='business',
            message_purpose=config.get('message_purpose', 'followup'),
            recipients=recipients,
            related_object_type=run.source_entity_type,
            related_object_id=CommunicationBindingService._as_uuid_string(run.source_entity_id),
            workflow_context_type='automation_run',
            workflow_context_id=str(run.id),
            subject=config.get('subject', ''),
            body_html=config.get('body_html', ''),
            body_text=config.get('body_text', ''),
            template_id=str(template.id) if template else None,
            preferred_sender_account_id=config.get('preferred_sender_account_id'),
            attachments=config.get('attachments', []),
            variables=CommunicationBindingService._build_template_variables(run=run, config=config),
            allow_fallback=True,
            track_delivery=True,
            schedule_at=schedule_at,
            cc_emails=config.get('cc_emails', []),
            bcc_emails=config.get('bcc_emails', []),
            reply_to_email=config.get('reply_to_email', ''),
            trigger_source='automation',
            triggered_by_event_id=run.source_event,
            metadata={
                'automation_run_id': str(run.id),
                'rule_id': str(run.rule_id),
                'action_type': action_type,
                'template_slug': config.get('template_key') or config.get('template_slug', ''),
                'notification_style': config.get('notification_style', ''),
            },
        )
        dedupe_key = CommunicationBindingService._build_dedupe_key(
            run=run,
            action_type=action_type,
            config=config,
        )
        context = OwnerActionContext(
            tenant_id=run.tenant_id,
            actor_id=run.created_by,
            external_reference=config.get('external_reference', dedupe_key),
            audit_metadata={
                'automation_run_id': str(run.id),
                'rule_id': str(run.rule_id),
                'action_type': action_type,
                'template_slug': config.get('template_key') or config.get('template_slug', ''),
                'notification_style': config.get('notification_style', ''),
            },
        )
        result = CommunicationDispatchService.enqueue_email_from_orchestration(
            context=context,
            request=request,
            dedupe_key=dedupe_key,
        )
        return result.as_execution_payload(action_type=action_type)

    @staticmethod
    def dispatch_in_app_notification_from_automation(*, run, action_type: str, config: dict):
        recipient_user_ids = CommunicationBindingService._resolve_user_ids(
            payload=run.trigger_payload_json or {},
            config=config,
            fallback_user_id=run.created_by if config.get('default_to_actor', True) else None,
        )
        if not recipient_user_ids:
            return {
                'action_type': action_type,
                'status': 'skipped',
                'reason': 'notification_recipients_missing',
            }
        title = config.get('title') or config.get('message') or config.get('notification_key') or 'Automation notification'
        body = config.get('body') or config.get('message', '')
        dedupe_key = CommunicationBindingService._build_dedupe_key(
            run=run,
            action_type=action_type,
            config=config,
        )
        context = OwnerActionContext(
            tenant_id=run.tenant_id,
            actor_id=run.created_by,
            external_reference=config.get('external_reference', dedupe_key),
            audit_metadata={
                'automation_run_id': str(run.id),
                'rule_id': str(run.rule_id),
                'action_type': action_type,
                'notification_style': config.get('notification_style', ''),
            },
        )
        result = CommunicationDispatchService.notify_from_orchestration(
            context=context,
            recipient_user_ids=recipient_user_ids,
            title=title[:255],
            body=body,
            notification_type=config.get('notification_type', 'platform_notification'),
            action_url=config.get('action_url', ''),
            related_entity_type=run.source_entity_type,
            related_entity_id=CommunicationBindingService._as_uuid_string(run.source_entity_id),
            dedupe_key=dedupe_key,
            notification_style=config.get('notification_style', ''),
        )
        return result.as_execution_payload(action_type=action_type)

    @staticmethod
    def _resolve_template(*, tenant_id, template_slug: str):
        if not template_slug:
            return None
        return (
            EmailTemplateDefinition.objects.filter(
                slug=template_slug,
                tenant_id__in=[tenant_id, None],
                is_active=True,
            )
            .order_by('-tenant_id', '-version')
            .first()
        )

    @staticmethod
    def _resolve_recipients(*, payload: dict, config: dict):
        recipients = [email for email in config.get('recipient_emails', []) if email]
        for path in config.get('recipient_paths', []):
            value = CommunicationBindingService._resolve_field(payload, path)
            if isinstance(value, list):
                recipients.extend(str(item) for item in value if item)
            elif value:
                recipients.append(str(value))
        return sorted({email.strip() for email in recipients if isinstance(email, str) and email.strip()})

    @staticmethod
    def _resolve_user_ids(*, payload: dict, config: dict, fallback_user_id=None):
        user_ids = [str(user_id) for user_id in config.get('recipient_user_ids', []) if user_id]
        for path in config.get('recipient_user_paths', []):
            value = CommunicationBindingService._resolve_field(payload, path)
            if isinstance(value, list):
                user_ids.extend(str(item) for item in value if item)
            elif value:
                user_ids.append(str(value))
        if fallback_user_id:
            user_ids.append(str(fallback_user_id))
        return sorted({item for item in user_ids if item})

    @staticmethod
    def _build_template_variables(*, run, config: dict):
        variables = dict(config.get('variables', {}))
        variables.setdefault('source_event', run.source_event)
        variables.setdefault('source_entity_type', run.source_entity_type)
        variables.setdefault('source_entity_id', run.source_entity_id)
        variables.setdefault('module_scope', run.rule.module_scope)
        variables.setdefault('trigger_payload', run.trigger_payload_json or {})
        return variables

    @staticmethod
    def _resolve_field(payload, path):
        current = payload
        for part in path.split('.'):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def _as_uuid_string(value):
        if not value:
            return None
        try:
            return str(uuid.UUID(str(value)))
        except (ValueError, TypeError, AttributeError):
            return None
