"""
WorkflowTaskOrchestrator
─────────────────────────
Central engine for creating, assigning, tracking, escalating,
and completing workflow-driven tasks.

Usage (from AutomationActionExecutor):

    from apps.automation_tasks.services.workflow_task_orchestrator import (
        WorkflowTaskOrchestrator,
    )

    task = WorkflowTaskOrchestrator.create_task_from_workflow(
        tenant_id=run.tenant_id,
        workflow_id=run.rule_id,
        execution_id=run.id,
        rule=task_rule,
        context=run.trigger_payload_json or {},
    )
"""
from __future__ import annotations

import logging
import re
from datetime import timedelta
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from apps.automation_tasks.models import (
    AssigneeType,
    TaskPriority,
    TaskStatus,
    WorkflowTaskDependency,
    WorkflowTaskEscalation,
    WorkflowTaskExecution,
    WorkflowTaskRule,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ─── Escalation role ladder ───────────────────────────────────────────────────
_ESCALATION_ROLES = ['recruiter_manager', 'hr_manager', 'tenant_admin']


class WorkflowTaskOrchestrator:

    # ─── Main creation entry point ────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_task_from_workflow(
        *,
        tenant_id,
        workflow_id,
        execution_id=None,
        rule: WorkflowTaskRule,
        context: dict,
        depends_on_task_id=None,
    ) -> WorkflowTaskExecution:
        """
        Creates a WorkflowTaskExecution from a WorkflowTaskRule + execution context.
        If depends_on_task_id is given the task starts as PENDING and is only
        activated when that dependency completes.
        """
        title       = WorkflowTaskOrchestrator._render(rule.task_title_template, context)
        description = WorkflowTaskOrchestrator._render(rule.task_description_template, context)
        assignee_id = WorkflowTaskOrchestrator.assign_task(rule, context)
        due_at      = WorkflowTaskOrchestrator.calculate_due_time(rule)

        task = WorkflowTaskExecution.objects.create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            rule=rule,
            task_title=title,
            task_description=description,
            assignee_user_id=assignee_id,
            priority=rule.priority,
            due_at=due_at,
            status=TaskStatus.PENDING,
            context_snapshot=context,
        )

        if depends_on_task_id:
            WorkflowTaskDependency.objects.get_or_create(
                tenant_id=tenant_id,
                task_execution=task,
                depends_on_task_id=depends_on_task_id,
            )

        logger.info('Created workflow task %s (rule=%s)', task.id, rule.id)
        return task

    # ─── Assignee resolution ──────────────────────────────────────────────────

    @staticmethod
    def assign_task(rule: WorkflowTaskRule, context: dict):
        """
        Resolves the assignee user_id from the rule's assignee_type and context.
        Returns a UUID string or None.
        """
        at = rule.assignee_type

        if at == AssigneeType.ASSIGNED_RECRUITER:
            return context.get('recruiter_id') or context.get('assigned_recruiter_id')

        if at == AssigneeType.HIRING_MANAGER:
            return context.get('hiring_manager_id')

        if at == AssigneeType.RECRUITER_MANAGER:
            return context.get('recruiter_manager_id')

        if at == AssigneeType.WORKFLOW_OWNER:
            return context.get('workflow_owner_id') or context.get('created_by')

        if at == AssigneeType.SPECIFIC_USER:
            return rule.assignee_field or None

        if at == AssigneeType.DYNAMIC_FIELD:
            # assignee_field is a dot-path into context, e.g. "candidate.recruiter_id"
            return WorkflowTaskOrchestrator._resolve_field(context, rule.assignee_field)

        return None

    # ─── Due time calculation ─────────────────────────────────────────────────

    @staticmethod
    def calculate_due_time(rule: WorkflowTaskRule):
        return timezone.now() + timedelta(minutes=rule.due_in_minutes)

    # ─── Escalation ───────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def escalate_task(task: WorkflowTaskExecution, *, reason: str = '') -> WorkflowTaskEscalation:
        """
        Escalates a task to the next role in the escalation ladder.
        Notifies via the notification orchestrator if available.
        """
        current_level = task.escalations.count()
        new_level     = current_level + 1

        if new_level > len(_ESCALATION_ROLES):
            new_level = len(_ESCALATION_ROLES)     # cap at highest level

        target_role = _ESCALATION_ROLES[min(new_level - 1, len(_ESCALATION_ROLES) - 1)]
        target_uid  = WorkflowTaskOrchestrator._resolve_escalation_target(
            task, target_role
        )

        escalation = WorkflowTaskEscalation.objects.create(
            tenant_id=task.tenant_id,
            task_execution=task,
            escalation_level=new_level,
            escalated_to=target_uid,
            escalated_to_role=target_role,
            reason=reason or f'SLA exceeded — task overdue since {task.due_at}',
        )

        task.status    = TaskStatus.ESCALATED
        task.escalated = True
        task.save(update_fields=['status', 'escalated', 'updated_at'])

        # Fire notification through orchestration layer
        WorkflowTaskOrchestrator._send_escalation_notification(task, escalation)

        logger.info('Task %s escalated to L%s (%s)', task.id, new_level, target_role)
        return escalation

    @staticmethod
    def _resolve_escalation_target(task: WorkflowTaskExecution, role: str):
        ctx = task.context_snapshot or {}
        role_key_map = {
            'recruiter_manager': ['recruiter_manager_id', 'manager_id'],
            'hr_manager':        ['hr_manager_id', 'manager_id'],
            'tenant_admin':      ['admin_id', 'tenant_admin_id'],
        }
        for key in role_key_map.get(role, []):
            if ctx.get(key):
                return ctx[key]
        return None

    @staticmethod
    def _send_escalation_notification(task: WorkflowTaskExecution, esc: WorkflowTaskEscalation):
        try:
            from apps.automation_notifications.services.workflow_notification_orchestrator import (
                WorkflowNotificationOrchestrator,
            )
            ctx = {
                **(task.context_snapshot or {}),
                'task_title': task.task_title,
                'escalation_level': esc.escalation_level,
                'due_at': str(task.due_at),
            }
            WorkflowNotificationOrchestrator.send_escalation_notification(
                tenant_id=task.tenant_id,
                workflow_id=task.workflow_id,
                execution_id=task.execution_id,
                reason=f'Task escalated: {task.task_title}',
                context=ctx,
                level=esc.escalation_level,
            )
        except Exception:
            logger.exception('Failed to send escalation notification for task %s', task.id)

    # ─── Dependency resolution ────────────────────────────────────────────────

    @staticmethod
    def resolve_dependencies(task: WorkflowTaskExecution) -> bool:
        """
        Returns True if all dependencies of this task are completed.
        Activates the task if so.
        """
        deps = WorkflowTaskDependency.objects.filter(task_execution=task).select_related('depends_on_task')
        if not deps.exists():
            return True

        all_done = all(
            d.depends_on_task.status == TaskStatus.COMPLETED
            for d in deps
        )
        if all_done and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.IN_PROGRESS
            task.save(update_fields=['status', 'updated_at'])
        return all_done

    # ─── Task completion ──────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def complete_task_trigger(task: WorkflowTaskExecution) -> dict:
        """
        Marks a task as completed and:
        1. Unlocks dependent tasks
        2. Fires any configured next-step triggers
        Returns a result dict.
        """
        task.status       = TaskStatus.COMPLETED
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'completed_at', 'updated_at'])

        unlocked = WorkflowTaskOrchestrator._unlock_dependent_tasks(task)
        logger.info('Task %s completed, unlocked %d dependents', task.id, len(unlocked))

        return {
            'task_id':           str(task.id),
            'status':            TaskStatus.COMPLETED,
            'unlocked_tasks':    [str(t.id) for t in unlocked],
        }

    @staticmethod
    def _unlock_dependent_tasks(completed_task: WorkflowTaskExecution) -> list[WorkflowTaskExecution]:
        """Activate any tasks that were waiting on this one."""
        unlocked = []
        for dep in WorkflowTaskDependency.objects.filter(depends_on_task=completed_task).select_related('task_execution'):
            child = dep.task_execution
            if WorkflowTaskOrchestrator.resolve_dependencies(child):
                unlocked.append(child)
        return unlocked

    # ─── SLA tracking ─────────────────────────────────────────────────────────

    @staticmethod
    def track_task_status(tenant_id) -> dict:
        """
        Scans all non-terminal tasks for this tenant, marks overdue ones,
        and auto-escalates tasks that have exceeded the escalation SLA.
        Designed to be called from a periodic Celery beat task.
        """
        now         = timezone.now()
        overdue_ids = []
        escalated   = []

        active_tasks = WorkflowTaskExecution.objects.filter(
            tenant_id=tenant_id,
            status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS],
        ).select_related('rule')

        for task in active_tasks:
            if task.due_at and task.due_at < now and task.status != TaskStatus.OVERDUE:
                task.status = TaskStatus.OVERDUE
                task.save(update_fields=['status', 'updated_at'])
                overdue_ids.append(str(task.id))

                # Check escalation threshold
                rule = task.rule
                if rule and rule.escalate_after_minutes:
                    elapsed = (now - task.created_at).total_seconds() / 60
                    if elapsed >= rule.escalate_after_minutes and not task.escalated:
                        esc = WorkflowTaskOrchestrator.escalate_task(
                            task, reason='Escalation SLA exceeded'
                        )
                        escalated.append(str(task.id))

        return {
            'scanned': active_tasks.count(),
            'overdue': overdue_ids,
            'escalated': escalated,
        }

    # ─── Analytics ────────────────────────────────────────────────────────────

    @staticmethod
    def get_analytics(tenant_id) -> dict:
        from django.db.models import Count, Q
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=7)
        qs     = WorkflowTaskExecution.objects.filter(
            tenant_id=tenant_id, created_at__gte=cutoff
        )

        total     = qs.count()
        completed = qs.filter(status=TaskStatus.COMPLETED).count()
        overdue   = qs.filter(status__in=[TaskStatus.OVERDUE, TaskStatus.ESCALATED]).count()
        escalated = qs.filter(escalated=True).count()

        by_priority = dict(
            qs.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
        )
        by_status = dict(
            qs.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )

        return {
            'total':             total,
            'completed':         completed,
            'overdue':           overdue,
            'escalated':         escalated,
            'completion_rate':   round(completed / total * 100, 1) if total else 0.0,
            'escalation_rate':   round(escalated / total * 100, 1) if total else 0.0,
            'by_priority':       by_priority,
            'by_status':         by_status,
        }

    # ─── Utilities ────────────────────────────────────────────────────────────

    @staticmethod
    def _render(template_str: str, context: dict) -> str:
        """Replace {{key}} placeholders with context values."""
        def replacer(match):
            key = match.group(1).strip()
            return str(context.get(key, match.group(0)))
        return re.sub(r'\{\{(\w+)\}\}', replacer, template_str or '')

    @staticmethod
    def _resolve_field(obj: dict, path: str):
        """Resolve a dot-path like 'candidate.recruiter_id' into a dict."""
        current = obj
        for part in (path or '').split('.'):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current
