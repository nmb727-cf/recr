from __future__ import annotations

from typing import Any

from django.db.models import Q
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowActorAssignment,
    WorkflowInstance,
    WorkflowNotificationLog,
    WorkflowNotificationQueue,
    WorkflowNotificationRule,
    WorkflowOrchestratorLog,
    WorkflowStageExecution,
    WorkflowTimeline,
)
from apps.workflow_execution.services.workflow_scheduler_engine import WorkflowSchedulerEngine


class WorkflowNotificationEngine:
    DEFAULT_TEMPLATE_MAP = {
        'workflow_stage_started': 'Stage started: {stage_name}',
        'workflow_stage_completed': 'Stage completed: {stage_name}',
        'workflow_wait_started': 'Workflow is waiting at {stage_name}',
        'workflow_wait_resumed': 'Wait resumed at {stage_name}',
        'workflow_sla_warning': 'SLA warning for {stage_name}. Deadline: {deadline_time}',
        'workflow_sla_breach': 'SLA breached for {stage_name}.',
        'workflow_escalation': 'Workflow escalated to {escalation_target}.',
        'workflow_failure': 'Workflow failed at {stage_name}.',
        'workflow_completed': 'Workflow completed successfully.',
    }

    @staticmethod
    def _build_payload(
        instance: WorkflowInstance,
        stage_execution: WorkflowStageExecution | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = dict(instance.context_data or {})
        stage_name = ''
        if stage_execution is not None:
            stage_name = stage_execution.stage_name or str(stage_execution.stage_id)
        merged = {
            'workflow_id': str(instance.workflow_id),
            'workflow_name': str(context.get('workflow_name', '')),
            'stage_name': stage_name,
            'actor_name': str(context.get('actor_name', '')),
            'candidate_name': str(context.get('candidate_name', '')),
            'job_title': str(context.get('job_title', '')),
            'deadline_time': str(context.get('deadline_time', '')),
            'escalation_target': str(context.get('escalation_target', '')),
        }
        merged.update(context)
        merged.update(payload or {})
        return merged

    @staticmethod
    def render_template(template_key: str, payload: dict[str, Any]) -> str:
        template = WorkflowNotificationEngine.DEFAULT_TEMPLATE_MAP.get(
            template_key,
            '{workflow_name} {stage_name} {job_title}',
        )
        try:
            return template.format(**payload).strip()
        except Exception:
            return template

    @staticmethod
    def resolve_recipients(
        instance: WorkflowInstance,
        *,
        recipient_type: str,
        stage_execution: WorkflowStageExecution | None = None,
    ) -> list[dict[str, Any]]:
        context = dict(instance.context_data or {})
        recipients: list[dict[str, Any]] = []

        if recipient_type == 'workflow_owner':
            owner_id = context.get('workflow_owner_id') or context.get('owner_id')
            if owner_id:
                recipients.append({'recipient_id': owner_id})

        elif recipient_type == 'assigned_actor':
            stage_id = stage_execution.stage_id if stage_execution else instance.current_stage_id
            assignments = WorkflowActorAssignment.objects.filter(
                workflow_instance=instance,
                status='active',
            )
            if stage_id:
                assignments = assignments.filter(stage_id=stage_id)
            for assignment in assignments:
                if assignment.actor_id:
                    recipients.append({'recipient_id': assignment.actor_id})

        elif recipient_type in {'recruiter', 'hiring_manager', 'hr', 'candidate', 'agency_recruiter', 'admin'}:
            key_map = {
                'recruiter': ['recruiter_id', 'assigned_recruiter_id'],
                'hiring_manager': ['hiring_manager_id', 'manager_id'],
                'hr': ['hr_id', 'hr_owner_id'],
                'candidate': ['candidate_id', 'current_candidate_id'],
                'agency_recruiter': ['agency_recruiter_id'],
                'admin': ['admin_id', 'escalation_admin_id'],
            }
            for key in key_map.get(recipient_type, []):
                value = context.get(key)
                if value:
                    recipients.append({'recipient_id': value})
                    break

        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for recipient in recipients:
            rid = str(recipient.get('recipient_id') or '')
            if not rid or rid in seen:
                continue
            seen.add(rid)
            unique.append(recipient)
        return unique

    @staticmethod
    def queue_notification(
        *,
        workflow_instance: WorkflowInstance,
        stage_execution: WorkflowStageExecution | None,
        recipient_type: str,
        recipient_id,
        channel: str,
        template_key: str,
        payload: dict[str, Any] | None = None,
        scheduled_at=None,
    ) -> WorkflowNotificationQueue:
        payload_data = WorkflowNotificationEngine._build_payload(
            workflow_instance,
            stage_execution=stage_execution,
            payload=payload,
        )
        queue_item = WorkflowNotificationQueue.objects.create(
            tenant_id=workflow_instance.tenant_id,
            workflow_instance=workflow_instance,
            stage_execution=stage_execution,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            channel=channel,
            template_key=template_key,
            payload=payload_data,
            status='pending',
            scheduled_at=scheduled_at or timezone.now(),
        )
        WorkflowNotificationEngine.log_notification_result(
            queue_item,
            status='queued',
            message_preview=WorkflowNotificationEngine.render_template(template_key, payload_data),
        )
        return queue_item

    @staticmethod
    def send_notification(queue_item: WorkflowNotificationQueue) -> dict[str, Any]:
        if queue_item.status == 'cancelled':
            return {'status': 'skipped', 'reason': 'Notification queue item is cancelled.'}

        queue_item.status = 'processing'
        queue_item.save(update_fields=['status', 'updated_at'])

        message_preview = WorkflowNotificationEngine.render_template(queue_item.template_key, queue_item.payload or {})
        # Channel transports are stubbed here; workflow log and timeline stay authoritative.
        send_ok = bool(queue_item.recipient_id)
        status_value = 'sent' if send_ok else 'failed'
        queue_item.status = status_value
        queue_item.processed_at = timezone.now()
        queue_item.save(update_fields=['status', 'processed_at', 'updated_at'])

        log = WorkflowNotificationEngine.log_notification_result(
            queue_item,
            status=status_value,
            message_preview=message_preview,
        )
        if status_value == 'sent':
            from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

            WorkflowObservabilityEngine.create_timeline_entry(
                workflow_instance=queue_item.workflow_instance,
                stage_execution=queue_item.stage_execution,
                entry_type='notification_sent',
                entry_label='Notification sent',
                entry_description=message_preview,
                actor_type='system',
                metadata={
                    'channel': queue_item.channel,
                    'recipient_type': queue_item.recipient_type,
                    'template_key': queue_item.template_key,
                    'notification_log_id': str(log.id),
                },
            )
            WorkflowObservabilityEngine.create_trace(
                workflow_instance=queue_item.workflow_instance,
                trace_key='notification',
                trace_type='notification',
                source_module='workflow_notification_engine',
                source_id=str(log.id),
                trace_message=message_preview,
                severity='info',
                metadata={'channel': queue_item.channel, 'recipient_id': str(queue_item.recipient_id or '')},
            )
            WorkflowObservabilityEngine.record_metric(
                workflow_instance=queue_item.workflow_instance,
                metric_name='notification_count',
                metric_value=1,
                metric_type='action_count',
                metadata={'channel': queue_item.channel},
            )
        else:
            from apps.workflow_execution.services.workflow_failure_recovery_engine import WorkflowFailureRecoveryEngine

            WorkflowFailureRecoveryEngine.create_recovery_case(
                workflow_instance=queue_item.workflow_instance,
                stage_execution=queue_item.stage_execution,
                recovery_type='notification_failure',
                error_message='Notification delivery failed',
                error_code='notification_send_failed',
                metadata={
                    'queue_id': str(queue_item.id),
                    'channel': queue_item.channel,
                    'template_key': queue_item.template_key,
                },
            )
        return {'status': status_value, 'notification_log_id': str(log.id), 'message_preview': message_preview}

    @staticmethod
    def process_notification_queue(*, limit: int = 100) -> list[dict[str, Any]]:
        now = timezone.now()
        items = WorkflowNotificationQueue.objects.filter(
            status='pending',
            scheduled_at__lte=now,
        ).order_by('scheduled_at')[:limit]
        results: list[dict[str, Any]] = []
        for item in items:
            results.append(
                {
                    'queue_id': str(item.id),
                    **WorkflowNotificationEngine.send_notification(item),
                }
            )
        return results

    @staticmethod
    def log_notification_result(
        queue_item: WorkflowNotificationQueue,
        *,
        status: str,
        message_preview: str,
    ) -> WorkflowNotificationLog:
        return WorkflowNotificationLog.objects.create(
            tenant_id=queue_item.tenant_id,
            workflow_instance=queue_item.workflow_instance,
            stage_execution=queue_item.stage_execution,
            recipient_type=queue_item.recipient_type,
            recipient_id=queue_item.recipient_id,
            channel=queue_item.channel,
            template_key=queue_item.template_key,
            message_preview=message_preview,
            status=status,
            sent_at=timezone.now() if status == 'sent' else None,
            metadata={
                'queue_id': str(queue_item.id),
            },
        )

    @staticmethod
    def cancel_notification(queue_item_id) -> WorkflowNotificationQueue | None:
        queue_item = WorkflowNotificationQueue.objects.filter(id=queue_item_id).first()
        if not queue_item:
            return None
        queue_item.status = 'cancelled'
        queue_item.processed_at = timezone.now()
        queue_item.save(update_fields=['status', 'processed_at', 'updated_at'])
        return queue_item

    @staticmethod
    def trigger_notifications(
        *,
        workflow_instance: WorkflowInstance,
        trigger_type: str,
        stage_execution: WorkflowStageExecution | None = None,
        payload: dict[str, Any] | None = None,
    ) -> list[WorkflowNotificationQueue]:
        stage_id = stage_execution.stage_id if stage_execution else None
        rules = WorkflowNotificationRule.objects.filter(
            workflow_id=workflow_instance.workflow_id,
            trigger_type=trigger_type,
            is_active=True,
        ).filter(Q(stage_id__isnull=True) | Q(stage_id=stage_id))

        queued: list[WorkflowNotificationQueue] = []
        for rule in rules:
            recipients = WorkflowNotificationEngine.resolve_recipients(
                workflow_instance,
                recipient_type=rule.recipient_type,
                stage_execution=stage_execution,
            )
            if not recipients:
                continue
            for recipient in recipients:
                queued.append(
                    WorkflowNotificationEngine.queue_notification(
                        workflow_instance=workflow_instance,
                        stage_execution=stage_execution,
                        recipient_type=rule.recipient_type,
                        recipient_id=recipient.get('recipient_id'),
                        channel=rule.channel,
                        template_key=rule.template_key,
                        payload=payload,
                    )
                )

        if queued:
            WorkflowSchedulerEngine.schedule_task(
                workflow_instance=workflow_instance,
                stage_execution=stage_execution,
                task_type='notification_dispatch',
                scheduled_at=timezone.now(),
                payload={'limit': len(queued), 'trigger_type': trigger_type},
            )
            WorkflowTimeline.objects.create(
                tenant_id=workflow_instance.tenant_id,
                workflow_instance=workflow_instance,
                stage_execution=stage_execution,
                event_type='transition',
                event_label=f'Notifications queued: {trigger_type}',
                actor_type='system',
                occurred_at=timezone.now(),
                payload={'queued_count': len(queued), 'trigger_type': trigger_type},
            )
            WorkflowOrchestratorLog.objects.create(
                tenant_id=workflow_instance.tenant_id,
                workflow_instance=workflow_instance,
                stage_execution=stage_execution,
                log_type='debug',
                message='Workflow notification rules matched.',
                metadata={'trigger_type': trigger_type, 'queued_count': len(queued)},
            )
        return queued


# Function-style exports required by prompt contract.
queue_notification = WorkflowNotificationEngine.queue_notification
send_notification = WorkflowNotificationEngine.send_notification
resolve_recipients = WorkflowNotificationEngine.resolve_recipients
render_template = WorkflowNotificationEngine.render_template
process_notification_queue = WorkflowNotificationEngine.process_notification_queue
log_notification_result = WorkflowNotificationEngine.log_notification_result
cancel_notification = WorkflowNotificationEngine.cancel_notification
