from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowSLAEvent,
    WorkflowSLATracker,
    WorkflowStageExecution,
    WorkflowStageSLA,
    WorkflowTimeline,
    WorkflowOrchestratorLog,
)
from apps.workflow_execution.services.workflow_notification_engine import WorkflowNotificationEngine
from apps.workflow_execution.services.workflow_scheduler_engine import WorkflowSchedulerEngine


class WorkflowSLAEngine:
    """Stage SLA + deadline + escalation engine for workflow runtime."""

    @staticmethod
    def _notify_channels() -> list[str]:
        return ['system_notification', 'email', 'alert_badge', 'timeline_log']

    @staticmethod
    def _timeline(instance, stage_execution, label: str, metadata: dict[str, Any] | None = None):
        WorkflowTimeline.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_execution,
            event_type='transition',
            event_label=label,
            actor_type='system',
            occurred_at=timezone.now(),
            payload=metadata or {},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        lower = label.lower()
        if 'initialized' in lower:
            entry_type = 'sla_started'
        elif 'warning' in lower:
            entry_type = 'sla_warning'
        elif 'breach' in lower:
            entry_type = 'sla_breached'
        else:
            entry_type = 'transition_taken'
        WorkflowObservabilityEngine.create_timeline_entry(
            workflow_instance=instance,
            stage_execution=stage_execution,
            entry_type=entry_type,
            entry_label=label,
            entry_description='',
            actor_type='system',
            metadata=metadata or {},
        )
        WorkflowObservabilityEngine.create_trace(
            workflow_instance=instance,
            trace_key='sla',
            trace_type='sla',
            source_module='workflow_sla_engine',
            source_id=str((metadata or {}).get('tracker_id', '')),
            trace_message=label,
            severity='warning' if 'warning' in lower else ('error' if 'breach' in lower else 'info'),
            metadata=metadata or {},
        )

    @staticmethod
    def _orchestrator_log(instance, stage_execution, log_type: str, message: str, metadata: dict[str, Any] | None = None):
        WorkflowOrchestratorLog.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_execution,
            log_type=log_type,
            message=message,
            metadata=metadata or {},
        )

    @staticmethod
    def initialize_sla(instance, stage_execution: WorkflowStageExecution):
        stage_sla = WorkflowStageSLA.objects.filter(
            workflow_id=instance.workflow_id,
            stage_id=stage_execution.stage_id,
            is_active=True,
        ).order_by('-created_at').first()
        if not stage_sla:
            return None

        now = timezone.now()
        tracker, _ = WorkflowSLATracker.objects.update_or_create(
            workflow_instance=instance,
            stage_execution=stage_execution,
            defaults={
                'tenant_id': instance.tenant_id,
                'stage_sla': stage_sla,
                'sla_start': now,
                'warning_at': now + stage_sla.warning_duration,
                'breach_at': now + stage_sla.sla_duration,
                'status': 'active',
                'escalated_at': None,
            },
        )

        WorkflowSLAEngine._timeline(
            instance,
            stage_execution,
            'SLA initialized',
            {
                'tracker_id': str(tracker.id),
                'warning_at': tracker.warning_at.isoformat(),
                'breach_at': tracker.breach_at.isoformat(),
            },
        )
        WorkflowSchedulerEngine.schedule_task(
            workflow_instance=instance,
            stage_execution=stage_execution,
            task_type='sla_check',
            scheduled_at=now + timedelta(minutes=30),
            payload={'source': 'sla_initialize', 'max_retries': 3, 'retry_delay_seconds': 300},
        )
        escalation_at = tracker.breach_at
        if stage_sla.escalation_duration:
            escalation_at = now + stage_sla.escalation_duration
        WorkflowSchedulerEngine.schedule_task(
            workflow_instance=instance,
            stage_execution=stage_execution,
            task_type='escalation_check',
            scheduled_at=escalation_at,
            payload={'source': 'sla_initialize', 'max_retries': 3, 'retry_delay_seconds': 300},
        )
        return tracker

    @staticmethod
    def update_sla_tracker(tracker: WorkflowSLATracker, *, status: str, escalated_at=None):
        tracker.status = status
        if escalated_at is not None:
            tracker.escalated_at = escalated_at
        tracker.save(update_fields=['status', 'escalated_at', 'updated_at'])
        return tracker

    @staticmethod
    def trigger_warning(tracker: WorkflowSLATracker):
        if tracker.status in {'resolved', 'breached', 'escalated'}:
            return tracker

        WorkflowSLAEngine.update_sla_tracker(tracker, status='warning')
        WorkflowSLAEvent.objects.create(
            tenant_id=tracker.tenant_id,
            workflow_instance=tracker.workflow_instance,
            stage_execution=tracker.stage_execution,
            event_type='warning',
            metadata={
                'channels': WorkflowSLAEngine._notify_channels(),
                'message': 'SLA warning threshold reached.',
            },
        )
        WorkflowSLAEngine._orchestrator_log(
            tracker.workflow_instance,
            tracker.stage_execution,
            'debug',
            'SLA warning triggered',
            {'tracker_id': str(tracker.id)},
        )
        WorkflowSLAEngine._timeline(
            tracker.workflow_instance,
            tracker.stage_execution,
            'SLA warning triggered',
            {'tracker_id': str(tracker.id)},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine
        WorkflowObservabilityEngine.update_snapshot(tracker.workflow_instance)
        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=tracker.workflow_instance,
            trigger_type='sla_warning',
            stage_execution=tracker.stage_execution,
            payload={'tracker_id': str(tracker.id)},
        )
        return tracker

    @staticmethod
    def trigger_breach(tracker: WorkflowSLATracker):
        if tracker.status in {'resolved', 'breached', 'escalated'}:
            return tracker

        WorkflowSLAEngine.update_sla_tracker(tracker, status='breached')
        WorkflowSLAEvent.objects.create(
            tenant_id=tracker.tenant_id,
            workflow_instance=tracker.workflow_instance,
            stage_execution=tracker.stage_execution,
            event_type='breach',
            metadata={
                'channels': WorkflowSLAEngine._notify_channels(),
                'message': 'SLA breached.',
            },
        )
        WorkflowSLAEngine._orchestrator_log(
            tracker.workflow_instance,
            tracker.stage_execution,
            'debug',
            'SLA breach triggered',
            {'tracker_id': str(tracker.id)},
        )
        WorkflowSLAEngine._timeline(
            tracker.workflow_instance,
            tracker.stage_execution,
            'SLA breach triggered',
            {'tracker_id': str(tracker.id)},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine
        WorkflowObservabilityEngine.record_metric(
            workflow_instance=tracker.workflow_instance,
            metric_name='sla_breach_count',
            metric_value=1,
            metric_type='failure_count',
            metadata={'tracker_id': str(tracker.id)},
        )
        WorkflowObservabilityEngine.update_snapshot(tracker.workflow_instance)
        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=tracker.workflow_instance,
            trigger_type='sla_breach',
            stage_execution=tracker.stage_execution,
            payload={'tracker_id': str(tracker.id)},
        )
        return tracker

    @staticmethod
    def trigger_escalation(tracker: WorkflowSLATracker):
        if tracker.status == 'resolved':
            return tracker

        stage_sla = tracker.stage_sla
        now = timezone.now()
        WorkflowSLAEngine.update_sla_tracker(tracker, status='escalated', escalated_at=now)
        WorkflowSLAEvent.objects.create(
            tenant_id=tracker.tenant_id,
            workflow_instance=tracker.workflow_instance,
            stage_execution=tracker.stage_execution,
            event_type='escalation',
            metadata={
                'channels': WorkflowSLAEngine._notify_channels(),
                'message': 'SLA escalated.',
                'escalation_role': stage_sla.escalation_role if stage_sla else '',
                'escalation_user': str(stage_sla.escalation_user) if stage_sla and stage_sla.escalation_user else None,
            },
        )
        WorkflowSLAEngine._orchestrator_log(
            tracker.workflow_instance,
            tracker.stage_execution,
            'route',
            'SLA escalation triggered',
            {
                'tracker_id': str(tracker.id),
                'escalation_role': stage_sla.escalation_role if stage_sla else '',
            },
        )
        WorkflowSLAEngine._timeline(
            tracker.workflow_instance,
            tracker.stage_execution,
            'SLA escalation triggered',
            {
                'tracker_id': str(tracker.id),
                'escalation_role': stage_sla.escalation_role if stage_sla else '',
            },
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine
        WorkflowObservabilityEngine.update_snapshot(tracker.workflow_instance)
        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=tracker.workflow_instance,
            trigger_type='escalation',
            stage_execution=tracker.stage_execution,
            payload={
                'tracker_id': str(tracker.id),
                'escalation_role': stage_sla.escalation_role if stage_sla else '',
                'escalation_target': stage_sla.escalation_role if stage_sla else '',
            },
        )
        return tracker

    @staticmethod
    def resolve_sla(instance, stage_execution: WorkflowStageExecution):
        tracker = WorkflowSLATracker.objects.filter(
            workflow_instance=instance,
            stage_execution=stage_execution,
            status__in=['active', 'warning', 'breached', 'escalated'],
        ).order_by('-created_at').first()
        if not tracker:
            return None

        WorkflowSLAEngine.update_sla_tracker(tracker, status='resolved')
        WorkflowSLAEvent.objects.create(
            tenant_id=tracker.tenant_id,
            workflow_instance=tracker.workflow_instance,
            stage_execution=tracker.stage_execution,
            event_type='resolved',
            metadata={
                'channels': WorkflowSLAEngine._notify_channels(),
                'message': 'SLA resolved.',
            },
        )
        WorkflowSLAEngine._timeline(
            tracker.workflow_instance,
            tracker.stage_execution,
            'SLA resolved',
            {'tracker_id': str(tracker.id)},
        )
        return tracker

    @staticmethod
    def check_sla_status(*, tracker: WorkflowSLATracker | None = None, workflow_instance=None):
        now = timezone.now()
        trackers = []
        if tracker:
            trackers = [tracker]
        else:
            qs = WorkflowSLATracker.objects.filter(status__in=['active', 'warning', 'breached'])
            if workflow_instance is not None:
                qs = qs.filter(workflow_instance=workflow_instance)
            trackers = list(qs)

        events: list[dict[str, Any]] = []
        for trk in trackers:
            if trk.status == 'active' and now >= trk.warning_at:
                WorkflowSLAEngine.trigger_warning(trk)
                events.append({'tracker_id': str(trk.id), 'event': 'warning'})

            if trk.status in {'active', 'warning'} and now >= trk.breach_at:
                WorkflowSLAEngine.trigger_breach(trk)
                events.append({'tracker_id': str(trk.id), 'event': 'breach'})

            escalation_at = trk.breach_at
            if trk.stage_sla and trk.stage_sla.escalation_duration:
                escalation_at = trk.sla_start + trk.stage_sla.escalation_duration
            if trk.status in {'breached', 'warning', 'active'} and now >= escalation_at:
                WorkflowSLAEngine.trigger_escalation(trk)
                events.append({'tracker_id': str(trk.id), 'event': 'escalation'})

        return events


# Function-style exports required by prompt contract.
initialize_sla = WorkflowSLAEngine.initialize_sla
check_sla_status = WorkflowSLAEngine.check_sla_status
trigger_warning = WorkflowSLAEngine.trigger_warning
trigger_breach = WorkflowSLAEngine.trigger_breach
trigger_escalation = WorkflowSLAEngine.trigger_escalation
resolve_sla = WorkflowSLAEngine.resolve_sla
update_sla_tracker = WorkflowSLAEngine.update_sla_tracker
