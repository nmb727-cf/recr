from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowInstance,
    WorkflowStageExecution,
    WorkflowTransitionLog,
    WorkflowWaitState,
    WorkflowFailureLog,
    WorkflowTimeline,
)
from apps.workflow_execution.services.workflow_notification_engine import WorkflowNotificationEngine
from apps.workflow_execution.services.workflow_scheduler_engine import WorkflowSchedulerEngine


class WorkflowInstanceTracker:
    """Workflow execution tracker and unified audit timeline orchestrator."""

    @staticmethod
    def _timeline(
        instance: WorkflowInstance,
        event_type: str,
        event_label: str,
        *,
        stage_execution: WorkflowStageExecution | None = None,
        wait_state: WorkflowWaitState | None = None,
        transition_log: WorkflowTransitionLog | None = None,
        failure_log: WorkflowFailureLog | None = None,
        actor_type: str = "",
        actor_id=None,
        payload: dict[str, Any] | None = None,
    ) -> WorkflowTimeline:
        payload_data = payload or {}
        if instance.version_id and 'workflow_version_id' not in payload_data:
            payload_data = {**payload_data, 'workflow_version_id': str(instance.version_id)}
        timeline = WorkflowTimeline.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_execution,
            wait_state=wait_state,
            transition_log=transition_log,
            failure_log=failure_log,
            event_type=event_type,
            event_label=event_label,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=payload_data,
            occurred_at=timezone.now(),
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.mirror_legacy_timeline_event(
            workflow_instance=instance,
            event_type=event_type,
            event_label=event_label,
            stage_execution=stage_execution,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=payload_data,
        )
        return timeline

    @staticmethod
    def create_workflow_instance(
        *,
        tenant_id,
        workflow_id,
        entity_type: str,
        entity_id,
        created_by=None,
        metadata: dict[str, Any] | None = None,
        status: str = "pending",
    ) -> WorkflowInstance:
        resolved_version_id = (metadata or {}).get('workflow_version_id')
        if not resolved_version_id:
            from apps.workflow_execution.services.workflow_versioning_engine import WorkflowVersioningEngine

            published_version = WorkflowVersioningEngine.get_latest_published_version(workflow_id)
            resolved_version_id = str(published_version.id) if published_version else None
        instance = WorkflowInstance.objects.create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            version_id=resolved_version_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            created_by=created_by,
            metadata=metadata or {},
            context_data=(metadata or {}).get("context_data", {}),
        )
        WorkflowInstanceTracker._timeline(
            instance,
            "transition",
            "Workflow instance created",
            actor_type="system",
            payload={"status": status, "workflow_version_id": resolved_version_id},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.record_metric(
            workflow_instance=instance,
            metric_name='stage_count',
            metric_value=0,
            metric_type='stage_count',
            metadata={'event': 'instance_created'},
        )
        return instance

    @staticmethod
    def start_stage_execution(
        instance: WorkflowInstance,
        *,
        stage_id,
        stage_name: str = "",
        actor_type: str = "system",
        actor_id=None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowStageExecution:
        stage_execution = WorkflowStageExecution.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_id=stage_id,
            stage_name=stage_name,
            status="running",
            actor_type=actor_type,
            actor_id=actor_id,
            metadata=metadata or {},
        )
        instance.current_stage_id = stage_id
        if instance.status in {"pending", "waiting"}:
            instance.status = "running"
        instance.save(update_fields=["current_stage_id", "status", "updated_at"])

        WorkflowInstanceTracker._timeline(
            instance,
            "stage_started",
            f"Stage started: {stage_name or stage_id}",
            stage_execution=stage_execution,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=metadata or {},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.record_metric(
            workflow_instance=instance,
            metric_name='stage_count',
            metric_value=1,
            metric_type='stage_count',
            metadata={'stage_execution_id': str(stage_execution.id)},
        )
        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=instance,
            trigger_type='stage_started',
            stage_execution=stage_execution,
            payload=metadata or {},
        )
        from apps.workflow_execution.services.workflow_action_handlers_engine import WorkflowActionHandlersEngine
        action_summary = WorkflowActionHandlersEngine.execute_stage_actions(
            instance=instance,
            stage_execution=stage_execution,
            stage_event='stage_enter',
            action_context=metadata or {},
        )
        WorkflowInstanceTracker._timeline(
            instance,
            "transition",
            "Stage enter actions executed",
            stage_execution=stage_execution,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=action_summary,
        )
        return stage_execution

    @staticmethod
    def complete_stage_execution(
        stage_execution: WorkflowStageExecution,
        *,
        actor_type: str = "system",
        actor_id=None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowStageExecution:
        stage_execution.status = "completed"
        stage_execution.completed_at = timezone.now()
        if metadata:
            stage_execution.metadata = {**(stage_execution.metadata or {}), **metadata}
        stage_execution.save(update_fields=["status", "completed_at", "metadata", "updated_at"])

        WorkflowInstanceTracker._timeline(
            stage_execution.workflow_instance,
            "stage_completed",
            f"Stage completed: {stage_execution.stage_name or stage_execution.stage_id}",
            stage_execution=stage_execution,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=metadata or {},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        if stage_execution.started_at and stage_execution.completed_at:
            WorkflowObservabilityEngine.record_metric(
                workflow_instance=stage_execution.workflow_instance,
                metric_name='stage_duration_seconds',
                metric_value=(stage_execution.completed_at - stage_execution.started_at).total_seconds(),
                metric_type='duration',
                metadata={'stage_execution_id': str(stage_execution.id)},
            )
        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=stage_execution.workflow_instance,
            trigger_type='stage_completed',
            stage_execution=stage_execution,
            payload=metadata or {},
        )
        from apps.workflow_execution.services.workflow_action_handlers_engine import WorkflowActionHandlersEngine
        action_summary = WorkflowActionHandlersEngine.execute_stage_actions(
            instance=stage_execution.workflow_instance,
            stage_execution=stage_execution,
            stage_event='stage_exit',
            action_context=metadata or {},
        )
        WorkflowInstanceTracker._timeline(
            stage_execution.workflow_instance,
            "transition",
            "Stage exit actions executed",
            stage_execution=stage_execution,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=action_summary,
        )
        return stage_execution

    @staticmethod
    def fail_stage_execution(
        stage_execution: WorkflowStageExecution,
        *,
        error_message: str,
        error_type: str = "",
        actor_type: str = "system",
        actor_id=None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowFailureLog:
        now = timezone.now()
        stage_execution.status = "failed"
        stage_execution.failed_at = now
        stage_execution.completed_at = now
        if metadata:
            stage_execution.metadata = {**(stage_execution.metadata or {}), **metadata}
        stage_execution.save(update_fields=["status", "failed_at", "completed_at", "metadata", "updated_at"])

        return WorkflowInstanceTracker.log_failure(
            stage_execution.workflow_instance,
            stage_execution=stage_execution,
            error_message=error_message,
            error_type=error_type,
            retry_count=0,
            status="failed",
            actor_type=actor_type,
            actor_id=actor_id,
            metadata=metadata,
        )

    @staticmethod
    def move_to_next_stage(
        instance: WorkflowInstance,
        *,
        from_stage: str | None,
        to_stage: str | None,
        transition_type: str = "automatic",
        triggered_by: str = "system",
        actor_id=None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowTransitionLog:
        return WorkflowInstanceTracker.log_transition(
            instance,
            from_stage=from_stage,
            to_stage=to_stage,
            transition_type=transition_type,
            triggered_by=triggered_by,
            actor_id=actor_id,
            metadata=metadata,
        )

    @staticmethod
    def create_wait_state(
        instance: WorkflowInstance,
        *,
        stage_execution: WorkflowStageExecution | None,
        wait_type: str,
        wait_reason: str,
        timeout_at=None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowWaitState:
        wait_state = WorkflowWaitState.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_execution,
            wait_type=wait_type,
            wait_reason=wait_reason,
            timeout_at=timeout_at,
            status="waiting",
            metadata=metadata or {},
        )
        instance.status = "waiting"
        instance.save(update_fields=["status", "updated_at"])

        WorkflowInstanceTracker._timeline(
            instance,
            "waiting",
            f"Waiting: {wait_reason}",
            stage_execution=stage_execution,
            wait_state=wait_state,
            payload={"wait_type": wait_type, **(metadata or {})},
        )
        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=instance,
            trigger_type='wait_started',
            stage_execution=stage_execution,
            payload={"wait_type": wait_type, **(metadata or {})},
        )
        if timeout_at is not None:
            WorkflowSchedulerEngine.schedule_task(
                workflow_instance=instance,
                stage_execution=stage_execution,
                task_type='wait_resume',
                scheduled_at=timeout_at,
                payload={
                    'reason': 'wait_state_timeout',
                    'wait_state_id': str(wait_state.id),
                    'context': metadata or {},
                },
            )
        return wait_state

    @staticmethod
    def resume_wait_state(
        wait_state: WorkflowWaitState,
        *,
        actor_type: str = "system",
        actor_id=None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowWaitState:
        wait_state.status = "resumed"
        wait_state.resumed_at = timezone.now()
        wait_state.resumed_by = actor_type
        wait_state.resume_context = metadata or {}
        wait_state.save(update_fields=["status", "resumed_at", "resumed_by", "resume_context", "updated_at"])

        WorkflowInstanceTracker._timeline(
            wait_state.workflow_instance,
            "resumed",
            "Wait state resumed",
            stage_execution=wait_state.stage_execution,
            wait_state=wait_state,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=metadata or {},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        if wait_state.created_at and wait_state.resumed_at:
            WorkflowObservabilityEngine.record_metric(
                workflow_instance=wait_state.workflow_instance,
                metric_name='wait_time_seconds',
                metric_value=(wait_state.resumed_at - wait_state.created_at).total_seconds(),
                metric_type='wait_time',
                metadata={'wait_state_id': str(wait_state.id)},
            )
        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=wait_state.workflow_instance,
            trigger_type='wait_resumed',
            stage_execution=wait_state.stage_execution,
            payload=metadata or {},
        )
        return wait_state

    @staticmethod
    def log_transition(
        instance: WorkflowInstance,
        *,
        from_stage: str | None,
        to_stage: str | None,
        transition_type: str,
        triggered_by: str,
        actor_id=None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowTransitionLog:
        transition_log = WorkflowTransitionLog.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            from_stage=from_stage or "",
            to_stage=to_stage or "",
            from_stage_name=from_stage or "",
            to_stage_name=to_stage or "",
            transition_type=transition_type,
            triggered_by=triggered_by,
            actor_id=actor_id,
            condition_result=metadata or {},
        )
        WorkflowInstanceTracker._timeline(
            instance,
            "transition",
            f"Transition: {from_stage or 'start'} -> {to_stage or 'end'}",
            transition_log=transition_log,
            actor_type=triggered_by,
            actor_id=actor_id,
            payload=metadata or {},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.create_trace(
            workflow_instance=instance,
            trace_key='transition',
            trace_type='transition',
            source_module='workflow_instance_tracker',
            source_id=str(transition_log.id),
            trace_message=f'Transition from {from_stage or "start"} to {to_stage or "end"}',
            severity='info',
            metadata=metadata or {},
        )
        return transition_log

    @staticmethod
    def log_failure(
        instance: WorkflowInstance,
        *,
        stage_execution: WorkflowStageExecution | None,
        error_message: str,
        error_type: str = "",
        retry_count: int = 0,
        status: str = "failed",
        actor_type: str = "system",
        actor_id=None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowFailureLog:
        failure_log = WorkflowFailureLog.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_execution,
            error_message=error_message,
            error_type=error_type,
            retry_count=retry_count,
            status=status,
            metadata=metadata or {},
        )

        if status == "failed":
            instance.status = "failed"
            instance.failed_at = timezone.now()
            instance.save(update_fields=["status", "failed_at", "updated_at"])

        WorkflowInstanceTracker._timeline(
            instance,
            "failure",
            f"Failure: {error_message}",
            stage_execution=stage_execution,
            failure_log=failure_log,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=metadata or {"error_type": error_type, "retry_count": retry_count},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.create_trace(
            workflow_instance=instance,
            trace_key='failure',
            trace_type='failure',
            source_module='workflow_instance_tracker',
            source_id=str(failure_log.id),
            trace_message=error_message,
            severity='error' if status == 'failed' else 'warning',
            metadata={'error_type': error_type, 'retry_count': retry_count, **(metadata or {})},
        )
        WorkflowObservabilityEngine.record_metric(
            workflow_instance=instance,
            metric_name='failure_count',
            metric_value=1,
            metric_type='failure_count',
            metadata={'failure_log_id': str(failure_log.id)},
        )
        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=instance,
            trigger_type='workflow_failed',
            stage_execution=stage_execution,
            payload=metadata or {"error_type": error_type, "retry_count": retry_count},
        )
        if not (metadata or {}).get('recovery_case_id'):
            from apps.workflow_execution.services.workflow_failure_recovery_engine import WorkflowFailureRecoveryEngine

            WorkflowFailureRecoveryEngine.create_recovery_case(
                workflow_instance=instance,
                stage_execution=stage_execution,
                recovery_type='stage_failure',
                failure_type=error_type or '',
                error_message=error_message,
                error_code=error_type or '',
                metadata=metadata or {},
            )
        return failure_log

    @staticmethod
    @transaction.atomic
    def retry_stage(
        instance: WorkflowInstance,
        *,
        stage_execution: WorkflowStageExecution | None = None,
        triggered_by: str = "manual",
        actor_id=None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowStageExecution | None:
        stage_execution = stage_execution or instance.stage_executions.order_by("-created_at").first()
        if not stage_execution:
            return None

        latest_failure = WorkflowFailureLog.objects.filter(
            workflow_instance=instance,
            stage_execution=stage_execution,
        ).order_by("-created_at").first()
        retry_count = (latest_failure.retry_count + 1) if latest_failure else 1
        if latest_failure and latest_failure.status == "failed":
            latest_failure.status = "retrying"
            latest_failure.retry_count = retry_count
            latest_failure.save(update_fields=["status", "retry_count", "updated_at"])

        stage_execution.status = "running"
        stage_execution.failed_at = None
        stage_execution.completed_at = None
        stage_execution.save(update_fields=["status", "failed_at", "completed_at", "updated_at"])

        instance.status = "running"
        instance.failed_at = None
        instance.save(update_fields=["status", "failed_at", "updated_at"])

        WorkflowInstanceTracker._timeline(
            instance,
            "retry",
            f"Retry started: {stage_execution.stage_name or stage_execution.stage_id}",
            stage_execution=stage_execution,
            actor_type=triggered_by,
            actor_id=actor_id,
            payload={"retry_count": retry_count, **(metadata or {})},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.record_metric(
            workflow_instance=instance,
            metric_name='retry_count',
            metric_value=retry_count,
            metric_type='retry_count',
            metadata={'stage_execution_id': str(stage_execution.id)},
        )

        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine
        from apps.orchestration_center.models.workflow import WorkflowNode

        try:
            retry_node = WorkflowNode.objects.get(id=stage_execution.stage_id)
        except WorkflowNode.DoesNotExist:
            return stage_execution

        WorkflowStageEngine.move_to_next_stage(
            instance,
            retry_node,
            context=metadata or {},
            triggered_by=triggered_by,
            actor_id=actor_id,
        )
        return stage_execution


# Function-style exports required by prompt contract.
create_workflow_instance = WorkflowInstanceTracker.create_workflow_instance
start_stage_execution = WorkflowInstanceTracker.start_stage_execution
complete_stage_execution = WorkflowInstanceTracker.complete_stage_execution
fail_stage_execution = WorkflowInstanceTracker.fail_stage_execution
move_to_next_stage = WorkflowInstanceTracker.move_to_next_stage
create_wait_state = WorkflowInstanceTracker.create_wait_state
resume_wait_state = WorkflowInstanceTracker.resume_wait_state
log_transition = WorkflowInstanceTracker.log_transition
log_failure = WorkflowInstanceTracker.log_failure
retry_stage = WorkflowInstanceTracker.retry_stage
