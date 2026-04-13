import hashlib
import json
from dataclasses import dataclass
from typing import Any

from apps.orchestration_center.models import IntelligenceConnector
from apps.orchestration_center.services.ai_execution_service import AIExecutionService
from apps.orchestration_center.services.audit_service import AuditService
from apps.orchestration_center.services.automation_rule_service import AutomationRuleService
from apps.orchestration_center.services.tenant_settings_service import TenantSettingsService
from apps.orchestration_center.tasks.ai_tasks import execute_ai_request
from apps.orchestration_center.tasks.automation_tasks import execute_automation_rule


@dataclass(frozen=True)
class EventRuntimeConfig:
    module_scope: str
    source_module: str
    source_entity_type: str
    ai_use_case_key: str | None = None


class IntelligenceRuntimeEventService:
    EVENT_CONFIG: dict[str, EventRuntimeConfig] = {
        'job.created': EventRuntimeConfig(
            module_scope='jobs',
            source_module='jobs',
            source_entity_type='job_requisition',
            ai_use_case_key='job_enrichment',
        ),
        'job.published': EventRuntimeConfig(
            module_scope='jobs',
            source_module='jobs',
            source_entity_type='job_requisition',
            ai_use_case_key='candidate_matching',
        ),
        'application.created': EventRuntimeConfig(
            module_scope='pipeline',
            source_module='pipeline',
            source_entity_type='application',
            ai_use_case_key='candidate_ranking',
        ),
        'application.stage_changed': EventRuntimeConfig(
            module_scope='pipeline',
            source_module='pipeline',
            source_entity_type='application',
            ai_use_case_key='stage_recommendation',
        ),
        'application.shortlisted': EventRuntimeConfig(
            module_scope='pipeline',
            source_module='pipeline',
            source_entity_type='application',
            ai_use_case_key='shortlist_summary',
        ),
        'interview.scheduled': EventRuntimeConfig(
            module_scope='interviews',
            source_module='interviews',
            source_entity_type='interview',
            ai_use_case_key=None,
        ),
        'interview.completed': EventRuntimeConfig(
            module_scope='interviews',
            source_module='interviews',
            source_entity_type='interview',
            ai_use_case_key='interview_summary',
        ),
        'interview.feedback_submitted': EventRuntimeConfig(
            module_scope='interviews',
            source_module='interviews',
            source_entity_type='interview',
            ai_use_case_key='decision_assist',
        ),
        'interview.decision_recorded': EventRuntimeConfig(
            module_scope='interviews',
            source_module='interviews',
            source_entity_type='interview',
            ai_use_case_key='decision_quality_check',
        ),
        'agency.candidate_submitted': EventRuntimeConfig(
            module_scope='agencies',
            source_module='agencies',
            source_entity_type='application',
            ai_use_case_key='submission_intake_summary',
        ),
    }

    @classmethod
    def dispatch(
        cls,
        *,
        event_name: str,
        actor_id=None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        config = cls.EVENT_CONFIG.get(event_name)
        if not config:
            return {'event_name': event_name, 'skipped': ['unsupported_event']}

        payload = payload or {}
        tenant_id = payload.get('tenant_id')
        source_entity_id = str(payload.get('source_entity_id') or '')
        if not tenant_id or not source_entity_id:
            AuditService.log(
                tenant_id=tenant_id,
                actor_id=actor_id,
                actor_type='system',
                action_type='runtime_event.skipped',
                target_type='platform_event',
                target_id=None,
                metadata_json={'event_name': event_name, 'reason': 'missing_tenant_or_source_entity'},
            )
            return {'event_name': event_name, 'skipped': ['missing_tenant_or_source_entity']}

        settings, _ = TenantSettingsService.get_or_create(tenant_id, actor_id)
        connector = cls._get_connector(tenant_id=tenant_id, module_scope=config.module_scope)
        if not cls._connector_allows_event(connector=connector, event_name=event_name, settings=settings, module_scope=config.module_scope):
            AuditService.log(
                tenant_id=tenant_id,
                actor_id=actor_id,
                actor_type='system',
                action_type='runtime_event.skipped',
                target_type='platform_event',
                target_id=None,
                metadata_json={'event_name': event_name, 'reason': 'connector_disabled'},
            )
            return {'event_name': event_name, 'skipped': ['connector_disabled']}

        result = {
            'event_name': event_name,
            'tenant_id': str(tenant_id),
            'source_entity_id': source_entity_id,
            'ai_requests': [],
            'automation_runs': [],
            'skipped': [],
        }

        event_fingerprint = cls._event_fingerprint(event_name=event_name, payload=payload)

        if settings.ai_enabled and config.ai_use_case_key and cls._connector_allows_ai_action(connector, config.ai_use_case_key):
            try:
                request, created = AIExecutionService.create_request(
                    tenant_id=tenant_id,
                    created_by=actor_id,
                    module_scope=config.module_scope,
                    use_case_key=config.ai_use_case_key,
                    source_module=config.source_module,
                    source_entity_type=config.source_entity_type,
                    source_entity_id=source_entity_id,
                    source_event=event_name,
                    context_snapshot=payload,
                    mode=settings.default_approval_mode,
                    requires_review=settings.default_approval_mode == 'approval_required',
                    requires_approval=settings.default_approval_mode == 'approval_required',
                    idempotency_key=f'ai:{event_name}:{source_entity_id}:{event_fingerprint}:{config.ai_use_case_key}',
                )
            except ValueError:
                result['skipped'].append(f'ai_prompt_missing:{config.ai_use_case_key}')
            else:
                if created:
                    execute_ai_request.delay(str(request.id))
                result['ai_requests'].append(
                    {
                        'request_id': str(request.id),
                        'created': created,
                        'use_case_key': config.ai_use_case_key,
                    }
                )
        elif config.ai_use_case_key:
            result['skipped'].append('ai_disabled')

        if settings.automation_enabled:
            rules = AutomationRuleService.matching_rules(tenant_id, event_name)
            for rule in rules:
                if not cls._connector_allows_automation_action(connector, rule.rule_key):
                    continue
                run, created = AutomationRuleService.create_run(
                    tenant_id=tenant_id,
                    created_by=actor_id,
                    rule=rule,
                    source_event=event_name,
                    source_module=config.source_module,
                    source_entity_type=config.source_entity_type,
                    source_entity_id=source_entity_id,
                    payload=payload,
                    mode=rule.mode,
                    dedupe_key=f'automation:{event_name}:{rule.id}:{source_entity_id}:{event_fingerprint}',
                )
                if created:
                    execute_automation_rule.delay(str(run.id))
                result['automation_runs'].append(
                    {
                        'run_id': str(run.id),
                        'created': created,
                        'rule_key': rule.rule_key,
                    }
                )
        else:
            result['skipped'].append('automation_disabled')

        AuditService.log(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type='system',
            action_type='runtime_event.dispatched',
            target_type='platform_event',
            target_id=None,
            metadata_json=result,
        )
        return result

    @classmethod
    def build_payload(cls, *, event_name: str, **kwargs) -> dict[str, Any]:
        if event_name in {'job.created', 'job.published'}:
            requisition = kwargs.get('requisition')
            user = kwargs.get('user')
            return {
                'tenant_id': getattr(requisition, 'tenant_id', None),
                'source_entity_id': getattr(requisition, 'id', None),
                'job': {
                    'id': str(requisition.id),
                    'title': getattr(requisition, 'title', ''),
                    'status': getattr(requisition, 'status', ''),
                    'employment_type': getattr(requisition, 'employment_type', ''),
                    'work_mode': getattr(requisition, 'work_mode', ''),
                    'department': getattr(requisition, 'department', ''),
                },
                'actor_user_id': getattr(user, 'id', None),
            }
        if event_name in {'application.created', 'application.shortlisted', 'agency.candidate_submitted'}:
            application = kwargs.get('application')
            user = kwargs.get('user') or kwargs.get('agency_user')
            return {
                'tenant_id': getattr(application, 'tenant_id', None),
                'source_entity_id': getattr(application, 'id', None),
                'application': {
                    'id': str(application.id),
                    'status': getattr(application, 'status', ''),
                    'candidate_id': str(getattr(application, 'candidate_id', '') or ''),
                    'requisition_id': str(getattr(application, 'requisition_id', '') or ''),
                    'current_stage_id': str(getattr(application, 'current_stage_id', '') or ''),
                    'agency_id': str(getattr(application, 'agency_id', '') or ''),
                },
                'actor_user_id': getattr(user, 'id', None),
            }
        if event_name == 'application.stage_changed':
            application = kwargs.get('application')
            from_stage = kwargs.get('from_stage')
            to_stage = kwargs.get('to_stage')
            user = kwargs.get('user')
            return {
                'tenant_id': getattr(application, 'tenant_id', None),
                'source_entity_id': getattr(application, 'id', None),
                'application': {
                    'id': str(application.id),
                    'status': getattr(application, 'status', ''),
                    'candidate_id': str(getattr(application, 'candidate_id', '') or ''),
                    'requisition_id': str(getattr(application, 'requisition_id', '') or ''),
                    'current_stage_id': str(getattr(application, 'current_stage_id', '') or ''),
                },
                'from_stage': {
                    'id': str(getattr(from_stage, 'id', '') or ''),
                    'name': getattr(from_stage, 'name', ''),
                    'stage_type': getattr(from_stage, 'stage_type', ''),
                },
                'to_stage': {
                    'id': str(getattr(to_stage, 'id', '') or ''),
                    'name': getattr(to_stage, 'name', ''),
                    'stage_type': getattr(to_stage, 'stage_type', ''),
                },
                'actor_user_id': getattr(user, 'id', None),
            }
        if event_name in {'interview.scheduled', 'interview.completed'}:
            interview = kwargs.get('interview')
            return {
                'tenant_id': getattr(interview, 'tenant_id', None),
                'source_entity_id': getattr(interview, 'id', None),
                'interview': {
                    'id': str(interview.id),
                    'status': getattr(interview, 'status', ''),
                    'application_id': str(getattr(interview, 'application_id', '') or ''),
                    'interview_type': getattr(interview, 'interview_type', ''),
                    'scheduled_at': IntelligenceRuntimeEventService._serialize_datetime(getattr(interview, 'scheduled_at', None)),
                    'completed_at': IntelligenceRuntimeEventService._serialize_datetime(getattr(interview, 'completed_at', None)),
                    'recommendation': getattr(interview, 'recommendation', ''),
                },
            }
        if event_name == 'interview.feedback_submitted':
            interview = kwargs.get('interview')
            feedback = kwargs.get('feedback')
            return {
                'tenant_id': getattr(interview, 'tenant_id', None),
                'source_entity_id': getattr(interview, 'id', None),
                'interview': {
                    'id': str(interview.id),
                    'status': getattr(interview, 'status', ''),
                    'application_id': str(getattr(interview, 'application_id', '') or ''),
                },
                'feedback': {
                    'id': str(getattr(feedback, 'id', '') or ''),
                    'score': getattr(feedback, 'score', None),
                    'recommendation': getattr(feedback, 'recommendation', ''),
                },
            }
        if event_name == 'interview.decision_recorded':
            interview = kwargs.get('interview')
            decision = kwargs.get('decision')
            return {
                'tenant_id': getattr(interview, 'tenant_id', None),
                'source_entity_id': getattr(interview, 'id', None),
                'interview': {
                    'id': str(interview.id),
                    'status': getattr(interview, 'status', ''),
                    'application_id': str(getattr(interview, 'application_id', '') or ''),
                },
                'decision': {
                    'id': str(getattr(decision, 'id', '') or ''),
                    'recommendation': getattr(decision, 'recommendation', ''),
                    'decision': getattr(decision, 'decision', ''),
                },
            }
        return {}

    @staticmethod
    def _connector_allows_event(*, connector, event_name: str, settings, module_scope: str) -> bool:
        if settings.connector_enablement_json and settings.connector_enablement_json.get(module_scope) is False:
            return False
        if not connector:
            return True
        if connector.status not in {'active', 'testing'}:
            return False
        allowed_events = connector.events_consumed_json or []
        return not allowed_events or event_name in allowed_events

    @staticmethod
    def _connector_allows_ai_action(connector, use_case_key: str) -> bool:
        if not connector:
            return True
        allowed = connector.ai_actions_allowed_json or []
        return not allowed or use_case_key in allowed

    @staticmethod
    def _connector_allows_automation_action(connector, rule_key: str) -> bool:
        if not connector:
            return True
        allowed = connector.automation_actions_allowed_json or []
        return not allowed or rule_key in allowed

    @staticmethod
    def _get_connector(*, tenant_id, module_scope: str):
        return (
            IntelligenceConnector.objects.filter(
                tenant_id__in=[tenant_id, None],
                module_code=module_scope,
                is_deleted=False,
            )
            .order_by('-tenant_id')
            .first()
        )

    @staticmethod
    def _event_fingerprint(*, event_name: str, payload: dict[str, Any]) -> str:
        normalized = json.dumps(
            {
                'event_name': event_name,
                'source_entity_id': payload.get('source_entity_id'),
                'application': payload.get('application'),
                'interview': payload.get('interview'),
                'job': payload.get('job'),
                'from_stage': payload.get('from_stage'),
                'to_stage': payload.get('to_stage'),
                'feedback': payload.get('feedback'),
                'decision': payload.get('decision'),
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha1(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def _serialize_datetime(value):
        return value.isoformat() if value else None
