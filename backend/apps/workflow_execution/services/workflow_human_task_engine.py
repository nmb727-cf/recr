from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowApprovalLog,
    WorkflowApprovalRule,
    WorkflowHumanTask,
)
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.workflow_execution.services.workflow_notification_engine import WorkflowNotificationEngine
from apps.workflow_execution.services.workflow_scheduler_engine import WorkflowSchedulerEngine
from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine


class WorkflowHumanTaskEngine:
    @staticmethod
    def log_human_task_event(
        *,
        task: WorkflowHumanTask,
        event_label: str,
        payload: dict[str, Any] | None = None,
    ):
        WorkflowInstanceTracker._timeline(
            instance=task.workflow_instance,
            event_type='transition',
            event_label=event_label,
            stage_execution=task.stage_execution,
            actor_type='system',
            payload={
                'human_task_id': str(task.id),
                **(payload or {}),
            },
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        lower = event_label.lower()
        entry_type = 'human_task_created'
        if 'completed' in lower:
            entry_type = 'human_task_completed'
        elif 'approval' in lower and ('finalized' in lower or 'rejected' in lower):
            entry_type = 'approval_completed'
        elif 'approval' in lower:
            entry_type = 'approval_requested'

        WorkflowObservabilityEngine.create_timeline_entry(
            workflow_instance=task.workflow_instance,
            stage_execution=task.stage_execution,
            entry_type=entry_type,
            entry_label=event_label,
            entry_description='',
            actor_type='system',
            metadata={'human_task_id': str(task.id), **(payload or {})},
        )
        WorkflowObservabilityEngine.create_trace(
            workflow_instance=task.workflow_instance,
            trace_key='human_task',
            trace_type='human_task' if 'approval' not in lower else 'approval',
            source_module='workflow_human_task_engine',
            source_id=str(task.id),
            trace_message=event_label,
            severity='warning' if 'rejected' in lower or 'expired' in lower else 'info',
            metadata=payload or {},
        )

    @staticmethod
    def create_human_task(
        *,
        workflow_instance,
        stage_execution=None,
        task_type: str,
        title: str,
        description: str = '',
        assigned_to_type: str = '',
        assigned_to_id=None,
        priority: str = 'medium',
        due_at=None,
        metadata: dict[str, Any] | None = None,
        wait_for_completion: bool = True,
    ) -> WorkflowHumanTask:
        task = WorkflowHumanTask.objects.create(
            tenant_id=workflow_instance.tenant_id,
            workflow_instance=workflow_instance,
            stage_execution=stage_execution,
            task_type=task_type,
            assigned_to_type=assigned_to_type,
            assigned_to_id=assigned_to_id,
            title=title,
            description=description,
            priority=priority,
            due_at=due_at,
            status='pending',
            metadata=metadata or {},
        )

        WorkflowHumanTaskEngine.log_human_task_event(
            task=task,
            event_label=f'Human task created: {title}',
            payload={'task_type': task_type, 'priority': priority},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.record_metric(
            workflow_instance=workflow_instance,
            metric_name='human_task_count',
            metric_value=1,
            metric_type='action_count',
            metadata={'human_task_id': str(task.id), 'task_type': task.task_type},
        )

        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=workflow_instance,
            trigger_type='wait_started',
            stage_execution=stage_execution,
            payload={
                'human_task_id': str(task.id),
                'task_type': task.task_type,
                'task_title': task.title,
            },
        )

        if wait_for_completion and workflow_instance.status != 'waiting':
            wait_state = WorkflowInstanceTracker.create_wait_state(
                instance=workflow_instance,
                stage_execution=stage_execution,
                wait_type='manual',
                wait_reason=f'Waiting for human task: {task.title}',
                timeout_at=due_at,
                metadata={'human_task_id': str(task.id), 'resume_event': 'human_task_completed'},
            )
            wait_state.resume_event = 'human_task_completed'
            wait_state.save(update_fields=['resume_event', 'updated_at'])

        if due_at:
            WorkflowSchedulerEngine.schedule_task(
                workflow_instance=workflow_instance,
                stage_execution=stage_execution,
                task_type='escalation_check',
                scheduled_at=due_at,
                payload={
                    'human_task_id': str(task.id),
                    'human_task_event': 'expire',
                    'source': 'human_task_due_at',
                    'max_retries': 2,
                    'retry_delay_seconds': 300,
                },
            )
        return task

    @staticmethod
    def assign_human_task(*, task: WorkflowHumanTask, assigned_to_type: str, assigned_to_id=None):
        task.assigned_to_type = assigned_to_type
        task.assigned_to_id = assigned_to_id
        if task.status == 'pending':
            task.status = 'in_progress'
        task.save(update_fields=['assigned_to_type', 'assigned_to_id', 'status', 'updated_at'])

        WorkflowHumanTaskEngine.log_human_task_event(
            task=task,
            event_label='Human task assigned',
            payload={
                'assigned_to_type': assigned_to_type,
                'assigned_to_id': str(assigned_to_id) if assigned_to_id else None,
            },
        )
        return task

    @staticmethod
    def evaluate_approval_rules(*, workflow_instance, task: WorkflowHumanTask) -> dict[str, Any]:
        stage_id = task.stage_execution.stage_id if task.stage_execution else workflow_instance.current_stage_id
        rule = WorkflowApprovalRule.objects.filter(
            workflow_id=workflow_instance.workflow_id,
            stage_id=stage_id,
            is_active=True,
        ).order_by('-created_at').first()

        approvals = task.approval_logs.filter(decision='approved').count()
        rejections = task.approval_logs.filter(decision='rejected').count()
        requested_changes = task.approval_logs.filter(decision='requested_changes').count()

        if rule is None:
            return {
                'approved': approvals > 0 or task.task_type not in {'approval', 'decision'},
                'rejected': rejections > 0,
                'rule': None,
                'approvals': approvals,
                'required_approvals': 1,
                'requested_changes': requested_changes,
            }

        required = max(1, int(rule.required_approvals or 1))
        if rule.approval_type == 'single':
            approved = approvals >= 1
        elif rule.approval_type in {'multiple', 'parallel', 'sequential'}:
            approved = approvals >= required
        else:
            approved = approvals >= required

        return {
            'approved': approved and rejections == 0,
            'rejected': rejections > 0,
            'rule': {
                'id': str(rule.id),
                'approval_type': rule.approval_type,
                'required_approvals': required,
                'approval_role': rule.approval_role,
                'escalation_role': rule.escalation_role,
                'timeout_hours': rule.timeout_hours,
            },
            'approvals': approvals,
            'required_approvals': required,
            'requested_changes': requested_changes,
        }

    @staticmethod
    def finalize_approval(*, workflow_instance, task: WorkflowHumanTask) -> dict[str, Any]:
        evaluation = WorkflowHumanTaskEngine.evaluate_approval_rules(
            workflow_instance=workflow_instance,
            task=task,
        )

        if evaluation['rejected']:
            task.status = 'rejected'
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'completed_at', 'updated_at'])
            WorkflowHumanTaskEngine.log_human_task_event(
                task=task,
                event_label='Approval rejected',
                payload=evaluation,
            )
            WorkflowStageEngine.fail_stage(
                workflow_instance,
                reason=f'Approval rejected for task {task.title}',
                triggered_by='user',
            )
            return {'finalized': True, 'outcome': 'rejected', **evaluation}

        if evaluation['approved']:
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'completed_at', 'updated_at'])
            WorkflowHumanTaskEngine.log_human_task_event(
                task=task,
                event_label='Approval finalized',
                payload=evaluation,
            )
            if workflow_instance.status == 'waiting':
                WorkflowStageEngine.resume_instance(
                    workflow_instance.id,
                    triggered_by='user',
                    context={
                        'human_task_id': str(task.id),
                        'approval_outcome': 'approved',
                    },
                )
            return {'finalized': True, 'outcome': 'approved', **evaluation}

        task.status = 'in_progress'
        task.save(update_fields=['status', 'updated_at'])
        WorkflowHumanTaskEngine.log_human_task_event(
            task=task,
            event_label='Approval pending more responses',
            payload=evaluation,
        )
        return {'finalized': False, 'outcome': 'pending', **evaluation}

    @staticmethod
    def complete_human_task(
        *,
        task: WorkflowHumanTask,
        completed_by_type: str = 'user',
        completed_by_id=None,
        comments: str = '',
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if task.status in {'completed', 'rejected', 'expired', 'cancelled'}:
            return {'status': task.status, 'message': 'Task already terminal.'}

        if task.task_type in {'approval', 'decision'}:
            WorkflowApprovalLog.objects.create(
                tenant_id=task.tenant_id,
                workflow_instance=task.workflow_instance,
                task=task,
                approver_type=completed_by_type if completed_by_type in dict(WorkflowApprovalLog.APPROVER_TYPES) else 'system',
                approver_id=completed_by_id,
                decision='approved',
                comments=comments,
                metadata=metadata or {},
            )
            result = WorkflowHumanTaskEngine.finalize_approval(
                workflow_instance=task.workflow_instance,
                task=task,
            )
        else:
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'completed_at', 'updated_at'])
            WorkflowHumanTaskEngine.log_human_task_event(
                task=task,
                event_label='Human task completed',
                payload={'completed_by_type': completed_by_type, 'comments': comments},
            )
            if task.workflow_instance.status == 'waiting':
                WorkflowStageEngine.resume_instance(
                    task.workflow_instance.id,
                    triggered_by='user',
                    context={'human_task_id': str(task.id), 'task_outcome': 'completed'},
                )
            result = {'finalized': True, 'outcome': 'completed'}

        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=task.workflow_instance,
            trigger_type='wait_resumed',
            stage_execution=task.stage_execution,
            payload={
                'human_task_id': str(task.id),
                'task_status': task.status,
                'outcome': result.get('outcome'),
            },
        )
        return result

    @staticmethod
    def reject_human_task(
        *,
        task: WorkflowHumanTask,
        rejected_by_type: str = 'user',
        rejected_by_id=None,
        comments: str = '',
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if task.status in {'completed', 'rejected', 'expired', 'cancelled'}:
            return {'status': task.status, 'message': 'Task already terminal.'}

        WorkflowApprovalLog.objects.create(
            tenant_id=task.tenant_id,
            workflow_instance=task.workflow_instance,
            task=task,
            approver_type=rejected_by_type if rejected_by_type in dict(WorkflowApprovalLog.APPROVER_TYPES) else 'system',
            approver_id=rejected_by_id,
            decision='rejected',
            comments=comments,
            metadata=metadata or {},
        )
        result = WorkflowHumanTaskEngine.finalize_approval(
            workflow_instance=task.workflow_instance,
            task=task,
        )
        return result

    @staticmethod
    def escalate_human_task(*, task: WorkflowHumanTask, reason: str = 'Escalated') -> WorkflowHumanTask:
        task.metadata = {
            **(task.metadata or {}),
            'escalated': True,
            'escalated_at': timezone.now().isoformat(),
            'escalation_reason': reason,
        }
        task.save(update_fields=['metadata', 'updated_at'])

        WorkflowHumanTaskEngine.log_human_task_event(
            task=task,
            event_label='Human task escalated',
            payload={'reason': reason},
        )

        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=task.workflow_instance,
            trigger_type='escalation',
            stage_execution=task.stage_execution,
            payload={
                'human_task_id': str(task.id),
                'reason': reason,
            },
        )
        return task

    @staticmethod
    def expire_human_task(*, task: WorkflowHumanTask) -> WorkflowHumanTask:
        if task.status in {'completed', 'rejected', 'expired', 'cancelled'}:
            return task
        if task.due_at and task.due_at > timezone.now():
            return task
        task.status = 'expired'
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'completed_at', 'updated_at'])

        WorkflowHumanTaskEngine.log_human_task_event(
            task=task,
            event_label='Human task expired',
            payload={'due_at': task.due_at.isoformat() if task.due_at else None},
        )
        WorkflowHumanTaskEngine.escalate_human_task(task=task, reason='Task expired')
        return task


# Function-style exports requested by prompt contract.
create_human_task = WorkflowHumanTaskEngine.create_human_task
assign_human_task = WorkflowHumanTaskEngine.assign_human_task
complete_human_task = WorkflowHumanTaskEngine.complete_human_task
reject_human_task = WorkflowHumanTaskEngine.reject_human_task
escalate_human_task = WorkflowHumanTaskEngine.escalate_human_task
evaluate_approval_rules = WorkflowHumanTaskEngine.evaluate_approval_rules
finalize_approval = WorkflowHumanTaskEngine.finalize_approval
expire_human_task = WorkflowHumanTaskEngine.expire_human_task
log_human_task_event = WorkflowHumanTaskEngine.log_human_task_event
