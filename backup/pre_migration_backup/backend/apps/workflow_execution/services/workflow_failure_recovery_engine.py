from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db import transaction
from django.db.models import Model
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowActionExecutionLog,
    WorkflowRecoveryActionLog,
    WorkflowRecoveryCase,
    WorkflowRecoveryPolicy,
    WorkflowRetryAttempt,
)
from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine


class WorkflowFailureRecoveryEngine:
    @staticmethod
    def _json_safe(value):
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, Model):
            return {'model': value.__class__.__name__, 'id': str(getattr(value, 'id', ''))}
        if isinstance(value, dict):
            return {str(k): WorkflowFailureRecoveryEngine._json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [WorkflowFailureRecoveryEngine._json_safe(v) for v in value]
        return str(value)

    @staticmethod
    def classify_failure(*, error_message: str = '', error_type: str = '', metadata: dict[str, Any] | None = None) -> str:
        text = f'{error_type} {error_message} {metadata or {}}'.lower()
        if any(word in text for word in ['timeout', 'temporar', 'connection reset', 'unavailable', 'rate limit']):
            return 'transient'
        if any(word in text for word in ['external', 'provider', 'smtp', 'gateway', 'network']):
            return 'external_dependency'
        if any(word in text for word in ['validation', 'invalid', 'missing field', 'bad request']):
            return 'validation'
        if any(word in text for word in ['permission', 'forbidden', 'unauthorized']):
            return 'permission'
        if any(word in text for word in ['integrity', 'duplicate key', 'foreign key', 'constraint']):
            return 'data_integrity'
        if any(word in text for word in ['logic', 'assert', 'unexpected state']):
            return 'logic_error'
        if 'timeout' in text:
            return 'timeout'
        return 'unknown'

    @staticmethod
    def resolve_recovery_policy(
        *,
        workflow_id,
        stage_id=None,
        action_type: str = '',
        failure_type: str = 'unknown',
    ) -> WorkflowRecoveryPolicy | None:
        qs = WorkflowRecoveryPolicy.objects.filter(
            workflow_id=workflow_id,
            is_active=True,
            failure_type=failure_type,
        ).order_by('-created_at')
        if stage_id:
            direct = qs.filter(stage_id=stage_id).first()
            if direct:
                if direct.action_type and action_type and direct.action_type != action_type:
                    pass
                else:
                    return direct
        if action_type:
            action_match = qs.filter(action_type=action_type, stage_id__isnull=True).first()
            if action_match:
                return action_match
        return qs.filter(stage_id__isnull=True, action_type='').first()

    @staticmethod
    def log_recovery_event(
        *,
        workflow_instance,
        recovery_case: WorkflowRecoveryCase | None,
        action_type: str,
        action_taken_by: str = 'system',
        action_summary: str = '',
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowRecoveryActionLog:
        log = WorkflowRecoveryActionLog.objects.create(
            tenant_id=workflow_instance.tenant_id,
            workflow_instance=workflow_instance,
            recovery_case=recovery_case,
            action_type=action_type,
            action_taken_by=action_taken_by,
            action_summary=action_summary,
            metadata=metadata or {},
        )
        label_map = {
            'retry_started': 'Temporary issue - retry scheduled',
            'retry_succeeded': 'Workflow recovered successfully',
            'retry_failed': 'Action failed again - needs attention',
            'escalated': 'Escalated due to repeated failures',
            'manual_resume': 'Manual resume performed',
            'manual_skip': 'Manual skip performed',
            'manual_fail': 'Manual fail performed',
            'workflow_recovered': 'Workflow recovered successfully',
            'permanent_failure': 'Workflow marked as permanently failed',
        }
        WorkflowObservabilityEngine.create_timeline_entry(
            workflow_instance=workflow_instance,
            stage_execution=recovery_case.stage_execution if recovery_case else None,
            entry_type='retry_started' if action_type.startswith('retry') else (
                'workflow_failed' if action_type in {'manual_fail', 'permanent_failure'} else 'transition_taken'
            ),
            entry_label=label_map.get(action_type, action_summary or action_type),
            entry_description=action_summary,
            actor_type='system' if action_taken_by == 'system' else 'user',
            metadata={'recovery_case_id': str(recovery_case.id) if recovery_case else None, **(metadata or {})},
        )
        WorkflowObservabilityEngine.create_trace(
            workflow_instance=workflow_instance,
            trace_key='recovery',
            trace_type='failure',
            source_module='workflow_failure_recovery_engine',
            source_id=str(log.id),
            trace_message=action_summary or action_type,
            severity='warning' if action_type in {'retry_failed', 'escalated'} else (
                'error' if action_type in {'manual_fail', 'permanent_failure'} else 'info'
            ),
            metadata={'action_type': action_type, **(metadata or {})},
        )
        return log

    @staticmethod
    @transaction.atomic
    def create_recovery_case(
        *,
        workflow_instance,
        recovery_type: str,
        error_message: str,
        error_code: str = '',
        failure_type: str = '',
        stage_execution=None,
        action_execution_log=None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowRecoveryCase:
        classified = failure_type or WorkflowFailureRecoveryEngine.classify_failure(
            error_message=error_message,
            error_type=error_code,
            metadata=metadata,
        )
        policy = WorkflowFailureRecoveryEngine.resolve_recovery_policy(
            workflow_id=workflow_instance.workflow_id,
            stage_id=stage_execution.stage_id if stage_execution else None,
            action_type=(action_execution_log.action_type if action_execution_log else ''),
            failure_type=classified,
        )

        retry_strategy = policy.retry_strategy if policy else ('immediate' if classified in {'transient', 'external_dependency', 'timeout'} else 'manual_only')
        retry_limit = int(policy.retry_limit if policy else (2 if retry_strategy in {'immediate', 'delayed', 'exponential_backoff'} else 0))

        case = WorkflowRecoveryCase.objects.create(
            tenant_id=workflow_instance.tenant_id,
            workflow_instance=workflow_instance,
            stage_execution=stage_execution,
            action_execution_log=action_execution_log,
            recovery_type=recovery_type,
            failure_type=classified,
            error_message=error_message,
            error_code=error_code,
            status='open',
            retry_strategy=retry_strategy,
            retry_limit=retry_limit,
            retry_count=0,
            metadata={**(metadata or {}), 'policy_id': str(policy.id) if policy else None},
        )

        WorkflowFailureRecoveryEngine.log_recovery_event(
            workflow_instance=workflow_instance,
            recovery_case=case,
            action_type='retry_started' if retry_strategy not in {'manual_only', 'no_retry'} else 'retry_failed',
            action_summary='Recovery case created',
            metadata={'recovery_type': recovery_type, 'failure_type': classified, 'retry_strategy': retry_strategy},
        )

        if retry_strategy in {'immediate', 'delayed', 'exponential_backoff'} and retry_limit > 0:
            WorkflowFailureRecoveryEngine.schedule_retry(case, policy=policy)
        elif retry_strategy == 'manual_only' or (policy and policy.requires_manual_review):
            WorkflowFailureRecoveryEngine.require_manual_intervention(case, reason='Manual review required by policy.')
        elif retry_strategy == 'no_retry':
            WorkflowFailureRecoveryEngine.close_recovery_case(case, final_status='failed_permanently', summary='No-retry policy applied.')
        return case

    @staticmethod
    def schedule_retry(case: WorkflowRecoveryCase, *, policy: WorkflowRecoveryPolicy | None = None) -> WorkflowRecoveryCase:
        now = timezone.now()
        delay_seconds = int(policy.retry_delay_seconds if policy else 0)
        if case.retry_strategy == 'immediate':
            delay_seconds = 0
        elif case.retry_strategy == 'delayed':
            delay_seconds = delay_seconds or 300
        elif case.retry_strategy == 'exponential_backoff':
            base = delay_seconds or 120
            delay_seconds = base * (2 ** max(case.retry_count, 0))
        next_retry_at = now + timedelta(seconds=delay_seconds)
        case.status = 'retry_scheduled'
        case.next_retry_at = next_retry_at
        case.save(update_fields=['status', 'next_retry_at', 'updated_at'])

        from apps.workflow_execution.services.workflow_scheduler_engine import WorkflowSchedulerEngine

        WorkflowSchedulerEngine.schedule_task(
            workflow_instance=case.workflow_instance,
            stage_execution=case.stage_execution,
            task_type='recovery_retry',
            scheduled_at=next_retry_at,
            payload={
                'recovery_case_id': str(case.id),
                'max_retries': max(case.retry_limit, 1),
                'retry_delay_seconds': delay_seconds or 60,
            },
        )
        WorkflowFailureRecoveryEngine.log_recovery_event(
            workflow_instance=case.workflow_instance,
            recovery_case=case,
            action_type='retry_started',
            action_summary='Temporary issue - retry scheduled',
            metadata={'next_retry_at': next_retry_at.isoformat(), 'retry_strategy': case.retry_strategy},
        )
        return case

    @staticmethod
    @transaction.atomic
    def run_retry_attempt(case: WorkflowRecoveryCase) -> WorkflowRetryAttempt:
        case.refresh_from_db()
        if case.status in {'failed_permanently', 'closed', 'recovered'}:
            return WorkflowRetryAttempt.objects.create(
                tenant_id=case.tenant_id,
                recovery_case=case,
                attempt_number=case.retry_count + 1,
                started_at=timezone.now(),
                completed_at=timezone.now(),
                status='cancelled',
                error_message='Recovery case is already terminal.',
                result_summary={},
            )
        case.status = 'retrying'
        case.save(update_fields=['status', 'updated_at'])
        attempt = WorkflowRetryAttempt.objects.create(
            tenant_id=case.tenant_id,
            recovery_case=case,
            attempt_number=case.retry_count + 1,
            started_at=timezone.now(),
            status='running',
            metadata={},
        )
        WorkflowFailureRecoveryEngine.log_recovery_event(
            workflow_instance=case.workflow_instance,
            recovery_case=case,
            action_type='retry_started',
            action_summary=f'Retry attempt {attempt.attempt_number} started',
        )
        try:
            result = None
            if case.recovery_type in {'stage_failure', 'transition_failure', 'routing_failure', 'sla_failure', 'scheduler_failure', 'human_task_failure'}:
                result = WorkflowFailureRecoveryEngine.retry_stage_execution(case)
            elif case.recovery_type in {'action_failure', 'notification_failure'}:
                result = WorkflowFailureRecoveryEngine.retry_action_execution(case)
            else:
                result = WorkflowFailureRecoveryEngine.retry_stage_execution(case)

            attempt.status = 'succeeded'
            attempt.completed_at = timezone.now()
            attempt.result_summary = {'result': WorkflowFailureRecoveryEngine._json_safe(result)}
            attempt.save(update_fields=['status', 'completed_at', 'result_summary', 'updated_at'])
            WorkflowFailureRecoveryEngine.mark_recovered(case, summary=f'Retry attempt {attempt.attempt_number} succeeded')
            return attempt
        except Exception as exc:
            case.retry_count += 1
            case.save(update_fields=['retry_count', 'updated_at'])
            attempt.status = 'failed'
            attempt.completed_at = timezone.now()
            attempt.error_message = str(exc)
            attempt.result_summary = {'error': str(exc)}
            attempt.save(update_fields=['status', 'completed_at', 'error_message', 'result_summary', 'updated_at'])
            WorkflowFailureRecoveryEngine.log_recovery_event(
                workflow_instance=case.workflow_instance,
                recovery_case=case,
                action_type='retry_failed',
                action_summary=f'Retry attempt {attempt.attempt_number} failed',
                metadata={'error_message': str(exc)},
            )
            if case.retry_count >= case.retry_limit:
                return WorkflowFailureRecoveryEngine._handle_retry_exhausted(case, reason=str(exc)) or attempt
            WorkflowFailureRecoveryEngine.schedule_retry(case)
            return attempt

    @staticmethod
    def _handle_retry_exhausted(case: WorkflowRecoveryCase, *, reason: str = ''):
        policy_id = (case.metadata or {}).get('policy_id')
        policy = WorkflowRecoveryPolicy.objects.filter(id=policy_id).first() if policy_id else None
        if policy and policy.requires_manual_review:
            WorkflowFailureRecoveryEngine.require_manual_intervention(case, reason='Retry limit exceeded - manual review required.')
            return None
        if policy and policy.escalate_after_failures and case.retry_count >= policy.escalate_after_failures:
            WorkflowFailureRecoveryEngine.escalate_recovery_case(case, reason='Retry limit exceeded.')
            return None
        WorkflowFailureRecoveryEngine.close_recovery_case(case, final_status='failed_permanently', summary=reason or 'Retry limit exceeded.')
        return None

    @staticmethod
    def retry_stage_execution(case: WorkflowRecoveryCase):
        from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker

        return WorkflowInstanceTracker.retry_stage(
            case.workflow_instance,
            stage_execution=case.stage_execution,
            triggered_by='system',
            metadata={'recovery_case_id': str(case.id), 'recovery_retry': True},
        )

    @staticmethod
    def retry_action_execution(case: WorkflowRecoveryCase):
        if case.action_execution_log is None:
            raise ValueError('No action execution log associated with this recovery case.')
        action_log: WorkflowActionExecutionLog = case.action_execution_log
        action_def = action_log.action_definition
        if action_def is None:
            raise ValueError('Action definition not found for failed action.')
        from apps.workflow_execution.services.workflow_action_handlers_engine import WorkflowActionHandlersEngine

        return WorkflowActionHandlersEngine.execute_action(
            instance=case.workflow_instance,
            stage_execution=case.stage_execution,
            action_definition=action_def,
            action_context={'recovery_case_id': str(case.id), 'recovery_retry': True},
        )

    @staticmethod
    def mark_recovered(case: WorkflowRecoveryCase, *, summary: str = 'Recovered') -> WorkflowRecoveryCase:
        case.status = 'recovered'
        case.resolved_at = timezone.now()
        case.next_retry_at = None
        case.save(update_fields=['status', 'resolved_at', 'next_retry_at', 'updated_at'])
        WorkflowFailureRecoveryEngine.log_recovery_event(
            workflow_instance=case.workflow_instance,
            recovery_case=case,
            action_type='workflow_recovered',
            action_summary=summary,
        )
        WorkflowObservabilityEngine.update_snapshot(case.workflow_instance)
        return case

    @staticmethod
    def escalate_recovery_case(case: WorkflowRecoveryCase, *, reason: str = 'Escalated') -> WorkflowRecoveryCase:
        case.status = 'escalated'
        case.next_retry_at = None
        case.save(update_fields=['status', 'next_retry_at', 'updated_at'])
        WorkflowFailureRecoveryEngine.log_recovery_event(
            workflow_instance=case.workflow_instance,
            recovery_case=case,
            action_type='escalated',
            action_summary=reason,
        )
        return case

    @staticmethod
    def require_manual_intervention(case: WorkflowRecoveryCase, *, reason: str = 'Manual intervention required') -> WorkflowRecoveryCase:
        case.status = 'manual_intervention_required'
        case.next_retry_at = None
        case.save(update_fields=['status', 'next_retry_at', 'updated_at'])
        WorkflowFailureRecoveryEngine.log_recovery_event(
            workflow_instance=case.workflow_instance,
            recovery_case=case,
            action_type='retry_failed',
            action_summary=reason,
        )
        return case

    @staticmethod
    def close_recovery_case(case: WorkflowRecoveryCase, *, final_status: str = 'closed', summary: str = '') -> WorkflowRecoveryCase:
        case.status = final_status
        case.resolved_at = timezone.now()
        case.next_retry_at = None
        case.save(update_fields=['status', 'resolved_at', 'next_retry_at', 'updated_at'])
        action_type = 'permanent_failure' if final_status == 'failed_permanently' else 'workflow_recovered'
        WorkflowFailureRecoveryEngine.log_recovery_event(
            workflow_instance=case.workflow_instance,
            recovery_case=case,
            action_type=action_type,
            action_summary=summary or final_status,
        )
        return case

    @staticmethod
    def manual_resume(case: WorkflowRecoveryCase, *, action_taken_by: str = 'user') -> WorkflowRecoveryCase:
        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine

        WorkflowFailureRecoveryEngine.log_recovery_event(
            workflow_instance=case.workflow_instance,
            recovery_case=case,
            action_type='manual_resume',
            action_taken_by=action_taken_by,
            action_summary='Manual resume requested.',
        )
        WorkflowStageEngine.resume_instance(
            case.workflow_instance.id,
            triggered_by='user',
            context={'recovery_case_id': str(case.id), 'manual_resume': True},
        )
        return WorkflowFailureRecoveryEngine.mark_recovered(case, summary='Manual resume completed.')

    @staticmethod
    def manual_skip(case: WorkflowRecoveryCase, *, action_taken_by: str = 'user') -> WorkflowRecoveryCase:
        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine

        WorkflowFailureRecoveryEngine.log_recovery_event(
            workflow_instance=case.workflow_instance,
            recovery_case=case,
            action_type='manual_skip',
            action_taken_by=action_taken_by,
            action_summary='Manual skip requested.',
        )
        stage_id = case.workflow_instance.current_stage_id
        if stage_id:
            WorkflowStageEngine.skip_stage(
                case.workflow_instance,
                stage_id=stage_id,
                reason='Manual skip from recovery case',
                triggered_by='user',
            )
        return WorkflowFailureRecoveryEngine.mark_recovered(case, summary='Manual skip completed.')

    @staticmethod
    def manual_fail(case: WorkflowRecoveryCase, *, action_taken_by: str = 'user') -> WorkflowRecoveryCase:
        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine

        WorkflowFailureRecoveryEngine.log_recovery_event(
            workflow_instance=case.workflow_instance,
            recovery_case=case,
            action_type='manual_fail',
            action_taken_by=action_taken_by,
            action_summary='Manual fail requested.',
        )
        WorkflowStageEngine.fail_stage(
            case.workflow_instance,
            reason='Manual fail from recovery case',
            triggered_by='user',
        )
        return WorkflowFailureRecoveryEngine.close_recovery_case(case, final_status='failed_permanently', summary='Manual fail completed.')


# Function-style exports required by prompt contract.
classify_failure = WorkflowFailureRecoveryEngine.classify_failure
create_recovery_case = WorkflowFailureRecoveryEngine.create_recovery_case
resolve_recovery_policy = WorkflowFailureRecoveryEngine.resolve_recovery_policy
schedule_retry = WorkflowFailureRecoveryEngine.schedule_retry
run_retry_attempt = WorkflowFailureRecoveryEngine.run_retry_attempt
retry_stage_execution = WorkflowFailureRecoveryEngine.retry_stage_execution
retry_action_execution = WorkflowFailureRecoveryEngine.retry_action_execution
mark_recovered = WorkflowFailureRecoveryEngine.mark_recovered
escalate_recovery_case = WorkflowFailureRecoveryEngine.escalate_recovery_case
require_manual_intervention = WorkflowFailureRecoveryEngine.require_manual_intervention
close_recovery_case = WorkflowFailureRecoveryEngine.close_recovery_case
log_recovery_event = WorkflowFailureRecoveryEngine.log_recovery_event
