from __future__ import annotations

from typing import Any

from django.db.models import Count
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowExecutionMetric,
    WorkflowExecutionTimelineEntry,
    WorkflowExecutionTrace,
    WorkflowFailureLog,
    WorkflowHumanTask,
    WorkflowInstance,
    WorkflowNotificationQueue,
    WorkflowObservabilitySnapshot,
    WorkflowSLATracker,
    WorkflowStageExecution,
    WorkflowWaitState,
)


class WorkflowObservabilityEngine:
    @staticmethod
    def _friendly_label(default_label: str, entry_type: str, metadata: dict[str, Any] | None = None) -> str:
        metadata = metadata or {}
        stage_name = str(metadata.get('stage_name') or '')
        if entry_type == 'stage_started' and stage_name:
            return f'{stage_name} started'
        if entry_type == 'stage_completed' and stage_name:
            return f'{stage_name} completed'
        if entry_type == 'wait_started':
            reason = str(metadata.get('wait_reason') or metadata.get('reason') or 'Waiting')
            return f'Waiting: {reason}'
        if entry_type == 'wait_resumed':
            return 'Workflow resumed from wait'
        if entry_type == 'notification_sent':
            channel = str(metadata.get('channel') or 'notification')
            return f'Notification sent via {channel}'
        if entry_type == 'workflow_completed':
            return 'Workflow completed'
        if entry_type == 'workflow_failed':
            return 'Workflow failed'
        return default_label

    @staticmethod
    def _infer_entry_type(event_type: str, event_label: str) -> str:
        et = (event_type or '').lower()
        label = (event_label or '').lower()
        if 'workflow' in label and 'created' in label:
            return 'workflow_started'
        if et == 'stage_started':
            return 'stage_started'
        if et == 'stage_completed':
            return 'stage_completed'
        if et == 'waiting':
            return 'wait_started'
        if et == 'resumed':
            return 'wait_resumed'
        if et == 'routing':
            return 'routing_started'
        if et == 'failure':
            return 'failure_logged'
        if et == 'retry':
            return 'retry_started'
        if 'decision' in label:
            return 'decision_evaluated'
        if 'action' in label:
            return 'action_executed'
        if 'notification' in label:
            return 'notification_sent'
        if 'sla warning' in label:
            return 'sla_warning'
        if 'sla breach' in label or 'sla breached' in label:
            return 'sla_breached'
        if 'sla initialized' in label:
            return 'sla_started'
        if 'transition' in label:
            return 'transition_taken'
        if 'completed' in label:
            return 'workflow_completed'
        return 'transition_taken'

    @staticmethod
    def create_timeline_entry(
        *,
        workflow_instance: WorkflowInstance,
        stage_execution: WorkflowStageExecution | None = None,
        entry_type: str,
        entry_label: str,
        entry_description: str = '',
        actor_type: str = '',
        actor_id=None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowExecutionTimelineEntry:
        timeline = WorkflowExecutionTimelineEntry.objects.create(
            tenant_id=workflow_instance.tenant_id,
            workflow_instance=workflow_instance,
            stage_execution=stage_execution,
            entry_type=entry_type,
            entry_label=WorkflowObservabilityEngine._friendly_label(entry_label, entry_type, metadata),
            entry_description=entry_description,
            actor_type=actor_type,
            actor_id=actor_id,
            metadata=metadata or {},
        )
        WorkflowObservabilityEngine.update_snapshot(workflow_instance)
        return timeline

    @staticmethod
    def create_trace(
        *,
        workflow_instance: WorkflowInstance,
        trace_key: str,
        trace_type: str,
        source_module: str,
        trace_message: str,
        source_id: str = '',
        severity: str = 'info',
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowExecutionTrace:
        return WorkflowExecutionTrace.objects.create(
            tenant_id=workflow_instance.tenant_id,
            workflow_instance=workflow_instance,
            trace_key=trace_key,
            trace_type=trace_type,
            source_module=source_module,
            source_id=source_id,
            trace_message=trace_message,
            severity=severity,
            metadata=metadata or {},
        )

    @staticmethod
    def update_snapshot(workflow_instance: WorkflowInstance) -> WorkflowObservabilitySnapshot:
        active_stage = workflow_instance.stage_executions.filter(status='running').order_by('-created_at').first()
        pending_tasks = WorkflowHumanTask.objects.filter(
            workflow_instance=workflow_instance,
            status__in=['pending', 'in_progress'],
        ).count()
        pending_notifications = WorkflowNotificationQueue.objects.filter(
            workflow_instance=workflow_instance,
            status__in=['pending', 'processing'],
        ).count()
        has_failure = WorkflowFailureLog.objects.filter(
            workflow_instance=workflow_instance,
            status__in=['failed', 'retrying'],
        ).exists() or workflow_instance.status == 'failed'
        has_sla_risk = WorkflowSLATracker.objects.filter(
            workflow_instance=workflow_instance,
            status__in=['warning', 'breached', 'escalated'],
        ).exists()

        snapshot, _ = WorkflowObservabilitySnapshot.objects.update_or_create(
            workflow_instance=workflow_instance,
            defaults={
                'tenant_id': workflow_instance.tenant_id,
                'current_stage_id': workflow_instance.current_stage_id,
                'current_status': workflow_instance.status,
                'wait_reason': str(workflow_instance.wait_reason or ''),
                'active_actor_type': active_stage.actor_type if active_stage else '',
                'active_actor_id': active_stage.actor_id if active_stage else None,
                'pending_task_count': pending_tasks,
                'pending_notification_count': pending_notifications,
                'has_failure': has_failure,
                'has_sla_risk': has_sla_risk,
            },
        )
        return snapshot

    @staticmethod
    def record_metric(
        *,
        workflow_instance: WorkflowInstance,
        metric_name: str,
        metric_value: float,
        metric_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowExecutionMetric:
        return WorkflowExecutionMetric.objects.create(
            tenant_id=workflow_instance.tenant_id,
            workflow_instance=workflow_instance,
            metric_name=metric_name,
            metric_value=float(metric_value),
            metric_type=metric_type,
            recorded_at=timezone.now(),
            metadata=metadata or {},
        )

    @staticmethod
    def mirror_legacy_timeline_event(
        *,
        workflow_instance: WorkflowInstance,
        event_type: str,
        event_label: str,
        stage_execution: WorkflowStageExecution | None = None,
        actor_type: str = '',
        actor_id=None,
        payload: dict[str, Any] | None = None,
    ) -> WorkflowExecutionTimelineEntry:
        entry_type = WorkflowObservabilityEngine._infer_entry_type(event_type, event_label)
        return WorkflowObservabilityEngine.create_timeline_entry(
            workflow_instance=workflow_instance,
            stage_execution=stage_execution,
            entry_type=entry_type,
            entry_label=event_label,
            entry_description='',
            actor_type=actor_type,
            actor_id=actor_id,
            metadata=payload or {},
        )

    @staticmethod
    def get_instance_timeline(instance_id):
        return WorkflowExecutionTimelineEntry.objects.filter(
            workflow_instance_id=instance_id
        ).order_by('created_at')

    @staticmethod
    def get_instance_trace(instance_id):
        return WorkflowExecutionTrace.objects.filter(
            workflow_instance_id=instance_id
        ).order_by('created_at')

    @staticmethod
    def get_instance_snapshot(instance_id):
        snapshot = WorkflowObservabilitySnapshot.objects.filter(workflow_instance_id=instance_id).first()
        if snapshot is None:
            instance = WorkflowInstance.objects.filter(id=instance_id).first()
            if instance is None:
                return None
            snapshot = WorkflowObservabilityEngine.update_snapshot(instance)
        return snapshot

    @staticmethod
    def summarize_execution_health(instance_id):
        instance = WorkflowInstance.objects.filter(id=instance_id).first()
        if instance is None:
            return None
        snapshot = WorkflowObservabilityEngine.get_instance_snapshot(instance_id)
        latest_failure = WorkflowFailureLog.objects.filter(workflow_instance=instance).order_by('-created_at').first()
        waiting_for = WorkflowWaitState.objects.filter(
            workflow_instance=instance,
            status='waiting',
        ).order_by('-created_at').first()
        return {
            'workflow_instance_id': str(instance.id),
            'status': instance.status,
            'has_failure': bool(snapshot and snapshot.has_failure),
            'has_sla_risk': bool(snapshot and snapshot.has_sla_risk),
            'pending_tasks': int(snapshot.pending_task_count if snapshot else 0),
            'pending_notifications': int(snapshot.pending_notification_count if snapshot else 0),
            'wait_reason': str(snapshot.wait_reason if snapshot else ''),
            'waiting_for': str(waiting_for.wait_reason if waiting_for else ''),
            'latest_failure': {
                'message': latest_failure.error_message,
                'type': latest_failure.error_type,
                'retry_count': latest_failure.retry_count,
            } if latest_failure else None,
        }

    @staticmethod
    def get_stage_observability(instance_id):
        rows = WorkflowStageExecution.objects.filter(workflow_instance_id=instance_id).order_by('started_at')
        result = []
        for stage in rows:
            duration = None
            if stage.completed_at:
                duration = (stage.completed_at - stage.started_at).total_seconds()
            result.append(
                {
                    'stage_execution_id': str(stage.id),
                    'stage_id': str(stage.stage_id),
                    'stage_name': stage.stage_name,
                    'status': stage.status,
                    'started_at': stage.started_at,
                    'completed_at': stage.completed_at,
                    'duration_seconds': duration,
                }
            )
        return result

    @staticmethod
    def get_failure_summary(instance_id):
        failures = WorkflowFailureLog.objects.filter(workflow_instance_id=instance_id).order_by('-created_at')
        latest = failures.first()
        return {
            'failure_count': failures.count(),
            'latest_failure': {
                'error_message': latest.error_message,
                'error_type': latest.error_type,
                'retry_count': latest.retry_count,
                'status': latest.status,
                'created_at': latest.created_at,
            } if latest else None,
            'retry_history': [
                {
                    'id': str(f.id),
                    'retry_count': f.retry_count,
                    'status': f.status,
                    'created_at': f.created_at,
                }
                for f in failures[:20]
            ],
        }

    @staticmethod
    def get_workflow_summary(workflow_id):
        instances = WorkflowInstance.objects.filter(workflow_id=workflow_id)
        by_status = dict(instances.values('status').annotate(count=Count('id')).values_list('status', 'count'))
        return {
            'workflow_id': str(workflow_id),
            'total_instances': instances.count(),
            'status_breakdown': by_status,
            'failed_instances': by_status.get('failed', 0),
            'waiting_instances': by_status.get('waiting', 0),
            'completed_instances': by_status.get('completed', 0),
        }

    @staticmethod
    def get_workflow_failures(workflow_id):
        return WorkflowFailureLog.objects.filter(
            workflow_instance__workflow_id=workflow_id
        ).order_by('-created_at')

    @staticmethod
    def get_workflow_sla_risks(workflow_id):
        return WorkflowSLATracker.objects.filter(
            workflow_instance__workflow_id=workflow_id,
            status__in=['warning', 'breached', 'escalated'],
        ).order_by('-updated_at')


# Function-style exports required by prompt contract.
create_timeline_entry = WorkflowObservabilityEngine.create_timeline_entry
create_trace = WorkflowObservabilityEngine.create_trace
update_snapshot = WorkflowObservabilityEngine.update_snapshot
record_metric = WorkflowObservabilityEngine.record_metric
get_instance_timeline = WorkflowObservabilityEngine.get_instance_timeline
get_instance_trace = WorkflowObservabilityEngine.get_instance_trace
get_instance_snapshot = WorkflowObservabilityEngine.get_instance_snapshot
summarize_execution_health = WorkflowObservabilityEngine.summarize_execution_health
get_stage_observability = WorkflowObservabilityEngine.get_stage_observability
get_failure_summary = WorkflowObservabilityEngine.get_failure_summary
