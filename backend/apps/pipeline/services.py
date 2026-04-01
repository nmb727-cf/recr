import uuid
from datetime import timedelta

from django.utils import timezone

from apps.pipeline.models import ActionDeadline, Application
from shared.owner_contracts import OwnerActionContext, OwnerActionResult, OwnerContractError


class PipelineDeadlineService:
    EXTERNAL_SOURCE_ORCHESTRATION_CENTER = 'orchestration_center'

    @staticmethod
    def create_automation_deadline(
        *,
        tenant_id,
        entity_type: str,
        entity_id,
        action_required: str,
        due_in_hours: int = 24,
        assigned_to=None,
        escalate_to=None,
        metadata: dict | None = None,
        external_source: str = EXTERNAL_SOURCE_ORCHESTRATION_CENTER,
        external_reference: str = '',
    ):
        parsed_entity_id = PipelineDeadlineService._parse_uuid(entity_id)
        if not parsed_entity_id:
            raise ValueError('ActionDeadline requires a valid UUID entity_id.')
        if not action_required:
            raise ValueError('action_required is required for pipeline deadlines.')

        metadata = dict(metadata or {})
        metadata.update(
            {
                'external_source': external_source,
                'external_reference': external_reference,
            }
        )

        existing = None
        if external_reference:
            existing = ActionDeadline.objects.filter(
                tenant_id=tenant_id,
                entity_type=entity_type,
                entity_id=parsed_entity_id,
                status__in=['pending', 'reminded', 'escalated'],
                metadata__external_source=external_source,
                metadata__external_reference=external_reference,
            ).first()
        if existing:
            return existing, False

        deadline = ActionDeadline.objects.create(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=parsed_entity_id,
            action_required=action_required,
            assigned_to=PipelineDeadlineService._parse_uuid(assigned_to),
            escalate_to=PipelineDeadlineService._parse_uuid(escalate_to),
            deadline_at=timezone.now() + timedelta(hours=int(due_in_hours or 24)),
            metadata=metadata,
        )
        return deadline, True

    @staticmethod
    def escalate_automation_deadline(
        *,
        tenant_id,
        entity_type: str,
        entity_id,
        action_required: str = '',
        escalate_to=None,
        metadata: dict | None = None,
        external_source: str = EXTERNAL_SOURCE_ORCHESTRATION_CENTER,
        external_reference: str = '',
    ):
        parsed_entity_id = PipelineDeadlineService._parse_uuid(entity_id)
        if not parsed_entity_id:
            raise ValueError('ActionDeadline escalation requires a valid UUID entity_id.')
        qs = ActionDeadline.objects.filter(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=parsed_entity_id,
            status__in=['pending', 'reminded', 'escalated'],
        )
        if external_reference:
            qs = qs.filter(
                metadata__external_source=external_source,
                metadata__external_reference=external_reference,
            )
        elif action_required:
            qs = qs.filter(action_required=action_required)
        deadline = qs.order_by('-created_at').first()
        if not deadline:
            raise ValueError('No active pipeline deadline matched the escalation request.')

        metadata_payload = dict(deadline.metadata or {})
        metadata_payload.update(metadata or {})
        metadata_payload['external_source'] = external_source
        if external_reference:
            metadata_payload['external_reference'] = external_reference

        if deadline.status == 'escalated' and PipelineDeadlineService._parse_uuid(escalate_to) == deadline.escalate_to:
            return deadline, False

        deadline.status = 'escalated'
        deadline.escalated_at = timezone.now()
        deadline.escalate_to = PipelineDeadlineService._parse_uuid(escalate_to)
        deadline.metadata = metadata_payload
        deadline.save(update_fields=['status', 'escalated_at', 'escalate_to', 'metadata', 'updated_at'])
        return deadline, True

    @staticmethod
    def assign_automation_deadline(
        *,
        tenant_id,
        entity_type: str,
        entity_id,
        action_required: str = '',
        assigned_to=None,
        metadata: dict | None = None,
        external_source: str = EXTERNAL_SOURCE_ORCHESTRATION_CENTER,
        external_reference: str = '',
    ):
        parsed_entity_id = PipelineDeadlineService._parse_uuid(entity_id)
        parsed_assignee = PipelineDeadlineService._parse_uuid(assigned_to)
        if not parsed_entity_id:
            raise ValueError('ActionDeadline assignment requires a valid UUID entity_id.')
        if not parsed_assignee:
            raise ValueError('ActionDeadline assignment requires a valid assigned_to UUID.')
        deadline = PipelineDeadlineService._resolve_deadline_for_contract(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=parsed_entity_id,
            action_required=action_required,
            external_source=external_source,
            external_reference=external_reference,
        )
        metadata_payload = dict(deadline.metadata or {})
        metadata_payload.update(metadata or {})
        metadata_payload['external_source'] = external_source
        if external_reference:
            metadata_payload['external_reference'] = external_reference
        if deadline.assigned_to == parsed_assignee:
            return deadline, False
        deadline.assigned_to = parsed_assignee
        deadline.metadata = metadata_payload
        deadline.save(update_fields=['assigned_to', 'metadata', 'updated_at'])
        return deadline, True

    @staticmethod
    def mark_operational_flag(
        *,
        tenant_id,
        entity_type: str,
        entity_id,
        flag_key: str,
        flag_value=True,
        metadata: dict | None = None,
    ):
        allowed_flags = {'attention_needed', 'review_required', 'overdue_risk', 'manual_check_required'}
        if flag_key not in allowed_flags:
            raise ValueError('Unsupported pipeline operational flag.')
        parsed_entity_id = PipelineDeadlineService._parse_uuid(entity_id)
        if not parsed_entity_id:
            raise ValueError('Pipeline flagging requires a valid UUID entity_id.')
        payload = dict(metadata or {})
        if entity_type == 'application':
            application = Application.objects.filter(
                tenant_id=tenant_id,
                id=parsed_entity_id,
                is_deleted=False,
            ).first()
            if not application:
                raise ValueError('Pipeline application not found for flagging.')
            metadata_json = dict(application.metadata or {})
            flags = dict(metadata_json.get('operational_flags') or {})
            existing = flags.get(flag_key)
            comparable = {
                'value': bool(flag_value),
                **payload,
            }
            if existing and {k: v for k, v in existing.items() if k != 'updated_at'} == comparable:
                return application, False
            desired = {
                **comparable,
                'updated_at': timezone.now().isoformat(),
            }
            flags[flag_key] = desired
            metadata_json['operational_flags'] = flags
            application.metadata = metadata_json
            application.save(update_fields=['metadata', 'updated_at'])
            return application, True
        if entity_type == 'deadline':
            deadline = ActionDeadline.objects.filter(
                tenant_id=tenant_id,
                id=parsed_entity_id,
            ).first()
            if not deadline:
                raise ValueError('Pipeline deadline not found for flagging.')
            metadata_json = dict(deadline.metadata or {})
            flags = dict(metadata_json.get('operational_flags') or {})
            comparable = {
                'value': bool(flag_value),
                **payload,
            }
            if flags.get(flag_key) and {k: v for k, v in flags[flag_key].items() if k != 'updated_at'} == comparable:
                return deadline, False
            desired = {
                **comparable,
                'updated_at': timezone.now().isoformat(),
            }
            flags[flag_key] = desired
            metadata_json['operational_flags'] = flags
            deadline.metadata = metadata_json
            deadline.save(update_fields=['metadata', 'updated_at'])
            return deadline, True
        raise ValueError('Unsupported pipeline entity_type for flagging.')

    @staticmethod
    def _resolve_deadline_for_contract(*, tenant_id, entity_type, entity_id, action_required='', external_source=EXTERNAL_SOURCE_ORCHESTRATION_CENTER, external_reference=''):
        qs = ActionDeadline.objects.filter(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status__in=['pending', 'reminded', 'escalated'],
        )
        if external_reference:
            qs = qs.filter(
                metadata__external_source=external_source,
                metadata__external_reference=external_reference,
            )
        elif action_required:
            qs = qs.filter(action_required=action_required)
        deadline = qs.order_by('-created_at').first()
        if not deadline:
            raise ValueError('No active pipeline deadline matched the contract request.')
        return deadline

    @staticmethod
    def _parse_uuid(value):
        if not value:
            return None
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError, AttributeError):
            return None

    @staticmethod
    def assign_from_orchestration(
        *,
        context: OwnerActionContext,
        entity_type: str,
        entity_id,
        assigned_to,
        action_required: str = '',
    ):
        try:
            deadline, created = PipelineDeadlineService.assign_automation_deadline(
                tenant_id=context.tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action_required=action_required,
                assigned_to=assigned_to,
                metadata=context.audit_metadata,
                external_source=context.external_source,
                external_reference=context.external_reference,
            )
        except ValueError as exc:
            raise OwnerContractError(str(exc)) from exc
        return OwnerActionResult(
            owner_module='pipeline',
            action_family='assign',
            status='completed',
            target_type='deadline',
            target_id=str(deadline.id),
            duplicate=not created,
            audit_metadata=context.metadata_payload(action_required=action_required),
            payload={
                'deadline_id': str(deadline.id),
                'assigned_to': str(deadline.assigned_to) if deadline.assigned_to else '',
            },
        )

    @staticmethod
    def create_from_orchestration(
        *,
        context: OwnerActionContext,
        entity_type: str,
        entity_id,
        action_required: str,
        due_in_hours: int = 24,
        assigned_to=None,
        escalate_to=None,
        deadline_type: str = 'followup',
        owner_role: str = 'recruiter',
    ):
        try:
            deadline, created = PipelineDeadlineService.create_automation_deadline(
                tenant_id=context.tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action_required=action_required,
                due_in_hours=due_in_hours,
                assigned_to=assigned_to,
                escalate_to=escalate_to,
                metadata=context.audit_metadata,
                external_source=context.external_source,
                external_reference=context.external_reference,
            )
        except ValueError as exc:
            message = str(exc)
            if 'valid UUID' in message:
                raise OwnerContractError.validation(message) from exc
            if 'action_required is required' in message:
                raise OwnerContractError.validation(message) from exc
            raise OwnerContractError.validation(message) from exc
        return OwnerActionResult(
            owner_module='pipeline',
            action_family='create_deadline',
            status='completed',
            target_type='deadline',
            target_id=str(deadline.id),
            duplicate=not created,
            audit_metadata=context.metadata_payload(
                deadline_type=deadline_type,
                owner_role=owner_role,
                action_required=action_required,
            ),
            payload={
                'deadline_id': str(deadline.id),
                'deadline_type': deadline_type,
                'due_at': deadline.deadline_at.isoformat(),
                'owner_role': owner_role,
                'assigned_to': str(deadline.assigned_to) if deadline.assigned_to else '',
                'escalate_to': str(deadline.escalate_to) if deadline.escalate_to else '',
            },
        )

    @staticmethod
    def escalate_from_orchestration(
        *,
        context: OwnerActionContext,
        entity_type: str,
        entity_id,
        action_required: str = '',
        escalate_to=None,
        severity: str = 'medium',
    ):
        try:
            deadline, created = PipelineDeadlineService.escalate_automation_deadline(
                tenant_id=context.tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action_required=action_required,
                escalate_to=escalate_to,
                metadata=context.audit_metadata,
                external_source=context.external_source,
                external_reference=context.external_reference,
            )
        except ValueError as exc:
            message = str(exc)
            if 'valid UUID' in message:
                raise OwnerContractError.validation(message) from exc
            if 'No active pipeline deadline matched' in message:
                raise OwnerContractError.not_found(message) from exc
            raise OwnerContractError.validation(message) from exc
        return OwnerActionResult(
            owner_module='pipeline',
            action_family='escalate',
            status='completed',
            target_type='deadline',
            target_id=str(deadline.id),
            duplicate=not created,
            audit_metadata=context.metadata_payload(action_required=action_required, severity=severity),
            payload={
                'deadline_id': str(deadline.id),
                'entity_type': entity_type,
                'entity_id': str(entity_id),
                'escalate_to': str(deadline.escalate_to) if deadline.escalate_to else '',
                'deadline_status': deadline.status,
                'escalated_at': deadline.escalated_at.isoformat() if deadline.escalated_at else '',
            },
        )

    @staticmethod
    def mark_flag_from_orchestration(
        *,
        context: OwnerActionContext,
        entity_type: str,
        entity_id,
        flag_key: str,
        flag_value=True,
    ):
        try:
            obj, created = PipelineDeadlineService.mark_operational_flag(
                tenant_id=context.tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                flag_key=flag_key,
                flag_value=flag_value,
                metadata=context.audit_metadata,
            )
        except ValueError as exc:
            raise OwnerContractError(str(exc)) from exc
        return OwnerActionResult(
            owner_module='pipeline',
            action_family='mark_flag',
            status='completed',
            target_type=entity_type,
            target_id=str(obj.id),
            duplicate=not created,
            audit_metadata=context.metadata_payload(flag_key=flag_key, flag_value=bool(flag_value)),
            payload={
                'flag_key': flag_key,
                'entity_id': str(obj.id),
            },
        )
