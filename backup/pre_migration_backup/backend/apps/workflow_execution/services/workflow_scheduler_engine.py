from __future__ import annotations

from typing import Any
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowScheduledTask,
    WorkflowSchedulerLog,
)


class WorkflowSchedulerEngine:
    @staticmethod
    def schedule_task(
        *,
        workflow_instance,
        task_type: str,
        scheduled_at,
        stage_execution=None,
        payload: dict[str, Any] | None = None,
    ) -> WorkflowScheduledTask:
        return WorkflowScheduledTask.objects.create(
            tenant_id=workflow_instance.tenant_id,
            workflow_instance=workflow_instance,
            stage_execution=stage_execution,
            task_type=task_type,
            scheduled_at=scheduled_at,
            status='scheduled',
            payload=payload or {},
        )

    @staticmethod
    def cancel_task(task_id) -> WorkflowScheduledTask | None:
        task = WorkflowScheduledTask.objects.filter(id=task_id).first()
        if not task:
            return None
        task.status = 'cancelled'
        task.save(update_fields=['status', 'updated_at'])
        WorkflowSchedulerEngine.log_scheduler_event(
            task=task,
            status='completed',
            message='Task cancelled.',
        )
        return task

    @staticmethod
    def log_scheduler_event(*, task: WorkflowScheduledTask, status: str, message: str) -> WorkflowSchedulerLog:
        log = WorkflowSchedulerLog.objects.create(
            tenant_id=task.tenant_id,
            task=task,
            workflow_instance=task.workflow_instance,
            task_type=task.task_type,
            status=status,
            message=message,
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        severity = 'info'
        if status == 'failed':
            severity = 'error'
        elif status == 'started' and task.task_type in {'sla_check', 'escalation_check'}:
            severity = 'warning'
        WorkflowObservabilityEngine.create_trace(
            workflow_instance=task.workflow_instance,
            trace_key='scheduler',
            trace_type='scheduler',
            source_module='workflow_scheduler_engine',
            source_id=str(log.id),
            trace_message=f'{task.task_type}: {message}',
            severity=severity,
            metadata={'task_id': str(task.id), 'status': status},
        )
        return log

    @staticmethod
    def retry_task(task: WorkflowScheduledTask, *, reason: str = '') -> WorkflowScheduledTask:
        delay_seconds = int((task.payload or {}).get('retry_delay_seconds', 300))
        task.retry_count += 1
        task.status = 'scheduled'
        task.scheduled_at = timezone.now() + timedelta(seconds=delay_seconds)
        task.payload = {**(task.payload or {}), 'last_retry_reason': reason}
        task.save(update_fields=['retry_count', 'status', 'scheduled_at', 'payload', 'updated_at'])
        WorkflowSchedulerEngine.log_scheduler_event(
            task=task,
            status='started',
            message=f'Task retried and rescheduled in {delay_seconds} seconds.',
        )
        return task

    @staticmethod
    def reschedule_task(task: WorkflowScheduledTask, *, scheduled_at) -> WorkflowScheduledTask:
        task.status = 'scheduled'
        task.scheduled_at = scheduled_at
        task.save(update_fields=['status', 'scheduled_at', 'updated_at'])
        WorkflowSchedulerEngine.log_scheduler_event(
            task=task,
            status='started',
            message='Task rescheduled.',
        )
        return task

    @staticmethod
    def _execute_task_action(task: WorkflowScheduledTask) -> dict[str, Any]:
        payload = task.payload or {}
        workflow_instance = task.workflow_instance

        if task.task_type == 'stage_transition':
            from apps.workflow_execution.services.workflow_execution_orchestrator import WorkflowExecutionOrchestrator

            return WorkflowExecutionOrchestrator.orchestrate_workflow_instance(
                workflow_instance.id,
                context=payload.get('context', {}),
                source_type='system',
            )

        if task.task_type in {'wait_resume', 'workflow_resume'}:
            deferred_action_log_id = None
            deferred_action_status = None
            deferred_action_definition_id = payload.get('context', {}).get('deferred_action_definition_id')
            if deferred_action_definition_id:
                from apps.workflow_execution.models import WorkflowActionDefinition
                from apps.workflow_execution.services.workflow_action_handlers_engine import WorkflowActionHandlersEngine

                action_def = WorkflowActionDefinition.objects.filter(
                    id=deferred_action_definition_id,
                    workflow_id=workflow_instance.workflow_id,
                    is_active=True,
                ).first()
                if action_def is None:
                    raise ValueError('Deferred action definition not found')

                action_stage_execution = (
                    task.stage_execution
                    if task.stage_execution and task.stage_execution.stage_id == action_def.stage_id
                    else workflow_instance.stage_executions.filter(stage_id=action_def.stage_id).order_by('-created_at').first()
                )
                action_log = WorkflowActionHandlersEngine.execute_action(
                    instance=workflow_instance,
                    stage_execution=action_stage_execution,
                    action_definition=action_def,
                    action_context=payload.get('context', {}).get('action_context', {}),
                )
                deferred_action_log_id = str(action_log.id)
                deferred_action_status = action_log.status

            from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine

            instance = WorkflowStageEngine.resume_instance(
                workflow_instance.id,
                triggered_by='system',
                context=payload.get('context', {}),
            )
            return {
                'instance_id': str(instance.id),
                'status': instance.status,
                'deferred_action_log_id': deferred_action_log_id,
                'deferred_action_status': deferred_action_status,
            }

        if task.task_type == 'retry_stage':
            from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
            from apps.workflow_execution.models import WorkflowStageExecution

            stage_execution = task.stage_execution
            if stage_execution is None and payload.get('stage_execution_id'):
                stage_execution = WorkflowStageExecution.objects.filter(id=payload.get('stage_execution_id')).first()
            result = WorkflowInstanceTracker.retry_stage(
                workflow_instance,
                stage_execution=stage_execution,
                triggered_by='system',
                metadata=payload.get('context', {}),
            )
            return {'retried_stage_execution_id': str(result.id) if result else None}

        if task.task_type == 'recovery_retry':
            from apps.workflow_execution.models import WorkflowRecoveryCase
            from apps.workflow_execution.services.workflow_failure_recovery_engine import WorkflowFailureRecoveryEngine

            case_id = payload.get('recovery_case_id')
            if not case_id:
                raise ValueError('Missing recovery_case_id for recovery_retry task')
            case = WorkflowRecoveryCase.objects.filter(id=case_id).first()
            if case is None:
                raise ValueError('Recovery case not found')
            attempt = WorkflowFailureRecoveryEngine.run_retry_attempt(case)
            return {'recovery_case_id': str(case.id), 'attempt_id': str(attempt.id), 'attempt_status': attempt.status}

        if task.task_type in {'sla_check', 'escalation_check'}:
            if payload.get('human_task_id'):
                from apps.workflow_execution.models import WorkflowHumanTask
                from apps.workflow_execution.services.workflow_human_task_engine import WorkflowHumanTaskEngine

                human_task = WorkflowHumanTask.objects.filter(id=payload.get('human_task_id')).first()
                if human_task is None:
                    return {'events': [], 'human_task': None}
                event_type = payload.get('human_task_event', 'expire')
                if event_type == 'escalate':
                    human_task = WorkflowHumanTaskEngine.escalate_human_task(
                        task=human_task,
                        reason=str(payload.get('reason', 'Scheduler escalation check')),
                    )
                else:
                    human_task = WorkflowHumanTaskEngine.expire_human_task(task=human_task)
                return {'events': [event_type], 'human_task': str(human_task.id)}

            from apps.workflow_execution.services.workflow_sla_engine import WorkflowSLAEngine

            events = WorkflowSLAEngine.check_sla_status(workflow_instance=workflow_instance)
            return {'events': events}

        if task.task_type == 'notification_dispatch':
            from apps.workflow_execution.services.workflow_notification_engine import WorkflowNotificationEngine

            limit = int(payload.get('limit', 100))
            results = WorkflowNotificationEngine.process_notification_queue(limit=limit)
            return {'processed': results}

        if task.task_type == 'analytics_rollup':
            from apps.workflow_execution.services.workflow_metrics_analytics_engine import WorkflowMetricsAnalyticsEngine

            workflow_id = payload.get('workflow_id') or workflow_instance.workflow_id
            metric_date = payload.get('metric_date')
            return WorkflowMetricsAnalyticsEngine.run_analytics_rollup(
                workflow_id=workflow_id,
                metric_date=metric_date,
            )

        raise ValueError(f'Unsupported task_type: {task.task_type}')

    @staticmethod
    @transaction.atomic
    def execute_scheduled_task(task_id) -> WorkflowScheduledTask | None:
        task = WorkflowScheduledTask.objects.select_for_update().filter(id=task_id).first()
        if task is None:
            return None
        if task.status not in {'scheduled', 'failed'}:
            return task

        task.status = 'running'
        task.save(update_fields=['status', 'updated_at'])
        WorkflowSchedulerEngine.log_scheduler_event(task=task, status='started', message='Task execution started.')

        try:
            result = WorkflowSchedulerEngine._execute_task_action(task)
            task.status = 'completed'
            task.executed_at = timezone.now()
            task.payload = {**(task.payload or {}), 'last_result': result}
            task.save(update_fields=['status', 'executed_at', 'payload', 'updated_at'])
            WorkflowSchedulerEngine.log_scheduler_event(
                task=task,
                status='completed',
                message='Task execution completed.',
            )
            return task
        except Exception as exc:
            task.status = 'failed'
            task.executed_at = timezone.now()
            task.payload = {**(task.payload or {}), 'last_error': str(exc)}
            task.save(update_fields=['status', 'executed_at', 'payload', 'updated_at'])
            WorkflowSchedulerEngine.log_scheduler_event(
                task=task,
                status='failed',
                message=f'Task execution failed: {exc}',
            )
            max_retries = int((task.payload or {}).get('max_retries', 1))
            if task.retry_count < max_retries:
                WorkflowSchedulerEngine.retry_task(task, reason=str(exc))
            return task

    @staticmethod
    def process_due_tasks(*, limit: int = 100) -> list[WorkflowScheduledTask]:
        now = timezone.now()
        tasks = list(
            WorkflowScheduledTask.objects.filter(
                status='scheduled',
                scheduled_at__lte=now,
            )
            .order_by('scheduled_at')[:limit]
        )
        processed: list[WorkflowScheduledTask] = []
        for task in tasks:
            executed = WorkflowSchedulerEngine.execute_scheduled_task(task.id)
            if executed is not None:
                processed.append(executed)
        return processed


# Function-style exports required by prompt contract.
schedule_task = WorkflowSchedulerEngine.schedule_task
cancel_task = WorkflowSchedulerEngine.cancel_task
execute_scheduled_task = WorkflowSchedulerEngine.execute_scheduled_task
process_due_tasks = WorkflowSchedulerEngine.process_due_tasks
retry_task = WorkflowSchedulerEngine.retry_task
log_scheduler_event = WorkflowSchedulerEngine.log_scheduler_event
reschedule_task = WorkflowSchedulerEngine.reschedule_task
