from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone

from apps.orchestration_center.models.workflow import WorkflowNode
from apps.workflow_execution.models import (
    WorkflowActionDefinition,
    WorkflowActionDependency,
    WorkflowActionExecutionLog,
    WorkflowActorAssignment,
)
from apps.workflow_execution.services.workflow_cross_entity_routing_engine import WorkflowCrossEntityRoutingEngine
from apps.workflow_execution.services.workflow_notification_engine import WorkflowNotificationEngine
from apps.workflow_execution.services.workflow_scheduler_engine import WorkflowSchedulerEngine
from apps.workflow_execution.services.workflow_sla_engine import WorkflowSLAEngine
from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine


class WorkflowActionHandlersEngine:
    @staticmethod
    def _context(instance) -> dict[str, Any]:
        return dict(instance.context_data or {})

    @staticmethod
    def _persist_context(instance, context: dict[str, Any]):
        instance.context_data = context
        instance.save(update_fields=['context_data', 'updated_at'])

    @staticmethod
    def _force_error(config: dict[str, Any] | None):
        if bool((config or {}).get('force_error')):
            raise ValueError((config or {}).get('force_error_message', 'Forced action failure for testing.'))

    @staticmethod
    def _dependency_satisfied(
        *,
        dependency: WorkflowActionDependency,
        action_results: dict[str, WorkflowActionExecutionLog],
    ) -> bool:
        depended = action_results.get(str(dependency.depends_on_action_id))
        if depended is None:
            return False
        if dependency.dependency_type == 'must_complete_first':
            return depended.status in {'completed', 'deferred'}
        if dependency.dependency_type == 'run_if_success':
            return depended.status == 'completed'
        if dependency.dependency_type == 'run_if_failed':
            return depended.status == 'failed'
        return False

    @staticmethod
    def _apply_failure_policy(instance, stage_execution, action_definition, action_log, exc: Exception):
        config = action_definition.action_config or {}
        retry_on_error = bool(config.get('retry_on_error'))
        continue_on_error = bool(config.get('continue_on_error', True))
        fail_workflow_on_error = bool(config.get('fail_workflow_on_error'))

        if retry_on_error:
            WorkflowSchedulerEngine.schedule_task(
                workflow_instance=instance,
                stage_execution=stage_execution,
                task_type='workflow_resume',
                scheduled_at=timezone.now() + timedelta(seconds=int(config.get('retry_delay_seconds', 300))),
                payload={
                    'context': {
                        'action_retry': True,
                        'action_definition_id': str(action_definition.id),
                        'action_log_id': str(action_log.id),
                        'error': str(exc),
                    },
                    'max_retries': int(config.get('max_retries', 1)),
                    'retry_delay_seconds': int(config.get('retry_delay_seconds', 300)),
                },
            )
        from apps.workflow_execution.services.workflow_failure_recovery_engine import WorkflowFailureRecoveryEngine
        recovery_case = WorkflowFailureRecoveryEngine.create_recovery_case(
            workflow_instance=instance,
            stage_execution=stage_execution,
            action_execution_log=action_log,
            recovery_type='action_failure',
            failure_type='',
            error_message=str(exc),
            error_code='action_execution',
            metadata={
                'action_definition_id': str(action_definition.id),
                'action_type': action_definition.action_type,
                'retry_on_error': retry_on_error,
                'continue_on_error': continue_on_error,
                'fail_workflow_on_error': fail_workflow_on_error,
            },
        )

        if fail_workflow_on_error and not continue_on_error:
            from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker

            WorkflowInstanceTracker.log_failure(
                instance,
                stage_execution=stage_execution,
                error_message=str(exc),
                error_type='action_execution',
                retry_count=0,
                status='failed',
                actor_type='system',
                metadata={
                    'action_definition_id': str(action_definition.id),
                    'action_type': action_definition.action_type,
                    'recovery_case_id': str(recovery_case.id),
                },
            )
            instance.status = 'failed'
            instance.failed_at = timezone.now()
            instance.completed_at = timezone.now()
            instance.save(update_fields=['status', 'failed_at', 'completed_at', 'updated_at'])
            return True
        return False

    @staticmethod
    def log_action_execution_result(
        *,
        action_log: WorkflowActionExecutionLog,
        status: str,
        execution_result: dict[str, Any] | None = None,
        error_message: str = '',
    ) -> WorkflowActionExecutionLog:
        action_log.status = status
        action_log.completed_at = timezone.now()
        action_log.execution_result = execution_result or {}
        action_log.error_message = error_message
        action_log.save(update_fields=['status', 'completed_at', 'execution_result', 'error_message', 'updated_at'])

        from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker

        WorkflowInstanceTracker._timeline(
            instance=action_log.workflow_instance,
            event_type='transition',
            event_label=f"Action {action_log.action_type}: {status}",
            stage_execution=action_log.stage_execution,
            actor_type='system',
            payload={
                'action_log_id': str(action_log.id),
                'action_definition_id': str(action_log.action_definition_id) if action_log.action_definition_id else None,
                'result': action_log.execution_result,
                'error_message': error_message,
            },
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.create_timeline_entry(
            workflow_instance=action_log.workflow_instance,
            stage_execution=action_log.stage_execution,
            entry_type='action_executed',
            entry_label=f'Action executed: {action_log.action_type}',
            entry_description=status,
            actor_type='system',
            metadata={'action_log_id': str(action_log.id), 'status': status},
        )
        WorkflowObservabilityEngine.create_trace(
            workflow_instance=action_log.workflow_instance,
            trace_key='action_execution',
            trace_type='action',
            source_module='workflow_action_handlers_engine',
            source_id=str(action_log.id),
            trace_message=f'{action_log.action_type} -> {status}',
            severity='error' if status == 'failed' else 'info',
            metadata={'result': action_log.execution_result, 'error_message': error_message},
        )
        WorkflowObservabilityEngine.record_metric(
            workflow_instance=action_log.workflow_instance,
            metric_name='action_count',
            metric_value=1,
            metric_type='action_count',
            metadata={'action_type': action_log.action_type},
        )
        return action_log

    @staticmethod
    def execute_assign_actor(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        assignment = WorkflowCrossEntityRoutingEngine.assign_actor_for_stage(
            instance=instance,
            stage_id=stage_execution.stage_id if stage_execution else action_definition.stage_id,
            actor_type=config.get('actor_type', 'recruiter'),
            actor_id=config.get('actor_id'),
            assignment_type=config.get('assignment_type', 'responsible'),
            notes=config.get('notes', ''),
        )
        return {'assignment_id': str(assignment.id), 'actor_type': assignment.actor_type}

    @staticmethod
    def execute_create_task(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        ctx = WorkflowActionHandlersEngine._context(instance)
        tasks = list(ctx.get('action_tasks') or [])
        task_entry = {
            'id': str(timezone.now().timestamp()).replace('.', ''),
            'title': config.get('title', action_definition.action_name),
            'description': config.get('description', ''),
            'status': config.get('status', 'pending'),
            'stage_id': str(stage_execution.stage_id) if stage_execution else str(action_definition.stage_id),
            'assignee_id': config.get('assignee_id'),
            'created_at': timezone.now().isoformat(),
        }
        tasks.append(task_entry)
        ctx['action_tasks'] = tasks
        WorkflowActionHandlersEngine._persist_context(instance, ctx)
        return {'task': task_entry}

    @staticmethod
    def execute_send_notification(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)

        trigger_type = config.get('trigger_type')
        if trigger_type:
            queued = WorkflowNotificationEngine.trigger_notifications(
                workflow_instance=instance,
                trigger_type=trigger_type,
                stage_execution=stage_execution,
                payload=config.get('payload', {}),
            )
            return {'queued_count': len(queued), 'mode': 'rule_trigger'}

        recipient_id = config.get('recipient_id')
        if not recipient_id and config.get('recipient_from_assignment', True):
            assignment = WorkflowActorAssignment.objects.filter(
                workflow_instance=instance,
                stage_id=stage_execution.stage_id if stage_execution else action_definition.stage_id,
                status='active',
            ).order_by('-assigned_at').first()
            recipient_id = assignment.actor_id if assignment else None

        queue_item = WorkflowNotificationEngine.queue_notification(
            workflow_instance=instance,
            stage_execution=stage_execution,
            recipient_type=config.get('recipient_type', 'assigned_actor'),
            recipient_id=recipient_id,
            channel=config.get('channel', 'in_app'),
            template_key=config.get('template_key', 'workflow_stage_started'),
            payload=config.get('payload', {}),
        )
        result = WorkflowNotificationEngine.send_notification(queue_item)
        return {'queue_id': str(queue_item.id), 'send_result': result}

    @staticmethod
    def execute_update_entity_status(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        field_name = config.get('field_name', 'entity_status')
        status_value = config.get('status_value', 'updated')

        if field_name == 'workflow.status':
            instance.status = status_value
            instance.save(update_fields=['status', 'updated_at'])
            return {'workflow_status': status_value}

        ctx = WorkflowActionHandlersEngine._context(instance)
        ctx[field_name] = status_value
        WorkflowActionHandlersEngine._persist_context(instance, ctx)
        return {'field_name': field_name, 'status_value': status_value}

    @staticmethod
    def execute_move_stage(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        to_stage_id = config.get('to_stage_id')
        if not to_stage_id:
            raise ValueError('to_stage_id is required for move_stage action')

        from_node = WorkflowNode.objects.filter(id=instance.current_stage_id).first()
        to_node = WorkflowNode.objects.filter(id=to_stage_id).first()
        if to_node is None:
            raise ValueError('Target stage node not found')

        WorkflowStageEngine.execute_stage_transition(
            instance=instance,
            from_node=from_node,
            to_node=to_node,
            transition_type='manual',
            label='action_move_stage',
            triggered_by='automation',
            reason='Action handler move_stage executed.',
            condition_result={'action_definition_id': str(action_definition.id)},
        )
        return {'to_stage_id': str(to_node.id)}

    @staticmethod
    def execute_create_interview(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        ctx = WorkflowActionHandlersEngine._context(instance)
        interviews = list(ctx.get('interviews') or [])
        interview = {
            'id': config.get('interview_id') or f"iv_{int(timezone.now().timestamp())}",
            'status': config.get('status', 'scheduled'),
            'type': config.get('interview_type', 'panel'),
            'stage_id': str(stage_execution.stage_id) if stage_execution else str(action_definition.stage_id),
        }
        interviews.append(interview)
        ctx['interviews'] = interviews
        WorkflowActionHandlersEngine._persist_context(instance, ctx)
        return {'interview': interview}

    @staticmethod
    def execute_update_interview(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        ctx = WorkflowActionHandlersEngine._context(instance)
        interviews = list(ctx.get('interviews') or [])
        interview_id = config.get('interview_id')
        updated = None
        for interview in interviews:
            if interview_id and str(interview.get('id')) != str(interview_id):
                continue
            interview['status'] = config.get('status', interview.get('status', 'updated'))
            interview.update(config.get('fields', {}))
            updated = interview
            break
        if updated is None:
            raise ValueError('Interview not found to update')
        ctx['interviews'] = interviews
        WorkflowActionHandlersEngine._persist_context(instance, ctx)
        return {'interview': updated}

    @staticmethod
    def execute_create_offer(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        ctx = WorkflowActionHandlersEngine._context(instance)
        offer = {
            'id': config.get('offer_id') or f"of_{int(timezone.now().timestamp())}",
            'amount': config.get('amount'),
            'status': config.get('status', 'draft'),
            'stage_id': str(stage_execution.stage_id) if stage_execution else str(action_definition.stage_id),
        }
        ctx['offer'] = offer
        WorkflowActionHandlersEngine._persist_context(instance, ctx)
        return {'offer': offer}

    @staticmethod
    def execute_update_offer(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        ctx = WorkflowActionHandlersEngine._context(instance)
        offer = dict(ctx.get('offer') or {})
        if not offer:
            raise ValueError('Offer not found to update')
        offer['status'] = config.get('status', offer.get('status', 'updated'))
        offer.update(config.get('fields', {}))
        ctx['offer'] = offer
        WorkflowActionHandlersEngine._persist_context(instance, ctx)
        return {'offer': offer}

    @staticmethod
    def execute_generate_document(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        ctx = WorkflowActionHandlersEngine._context(instance)
        docs = list(ctx.get('generated_documents') or [])
        document = {
            'id': config.get('document_id') or f"doc_{int(timezone.now().timestamp())}",
            'template_key': config.get('template_key', 'default_document_template'),
            'status': 'generated',
            'stage_id': str(stage_execution.stage_id) if stage_execution else str(action_definition.stage_id),
            'generated_at': timezone.now().isoformat(),
        }
        docs.append(document)
        ctx['generated_documents'] = docs
        WorkflowActionHandlersEngine._persist_context(instance, ctx)
        return {'document': document}

    @staticmethod
    def execute_create_sla(instance, stage_execution, action_definition):
        if stage_execution is None:
            raise ValueError('create_sla action requires stage_execution')
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        tracker = WorkflowSLAEngine.initialize_sla(instance, stage_execution)
        return {'sla_tracker_id': str(tracker.id) if tracker else None}

    @staticmethod
    def execute_create_handoff(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        checkpoint, route = WorkflowCrossEntityRoutingEngine.handoff_stage_control(
            instance=instance,
            stage_execution=stage_execution,
            from_entity=config.get('from_entity', 'company'),
            to_entity=config.get('to_entity', 'hr'),
            handoff_type=config.get('handoff_type', 'company_to_hr'),
            payload=config.get('payload', {}),
            expected_response_event=config.get('expected_response_event', ''),
            route_type=config.get('route_type', 'action_handoff'),
            reason=config.get('reason', 'Action-triggered handoff'),
        )
        return {
            'handoff_checkpoint_id': str(checkpoint.id) if checkpoint else None,
            'route_id': str(route.id) if route else None,
        }

    @staticmethod
    def execute_schedule_action(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)

        delay_seconds = int(config.get('delay_seconds', 300))
        task = WorkflowSchedulerEngine.schedule_task(
            workflow_instance=instance,
            stage_execution=stage_execution,
            task_type=config.get('task_type', 'workflow_resume'),
            scheduled_at=timezone.now() + timedelta(seconds=delay_seconds),
            payload=config.get('payload', {'source': 'action_handler'}),
        )
        return {'scheduled_task_id': str(task.id), 'scheduled_at': task.scheduled_at.isoformat()}

    @staticmethod
    def execute_request_approval(instance, stage_execution, action_definition):
        config = action_definition.action_config or {}
        WorkflowActionHandlersEngine._force_error(config)
        from apps.workflow_execution.services.workflow_human_task_engine import WorkflowHumanTaskEngine

        task = WorkflowHumanTaskEngine.create_human_task(
            workflow_instance=instance,
            stage_execution=stage_execution,
            task_type='approval',
            title=config.get('title', action_definition.action_name or 'Approval Required'),
            description=config.get('description', ''),
            assigned_to_type=config.get('assigned_to_type', 'hiring_manager'),
            assigned_to_id=config.get('assigned_to_id'),
            priority=config.get('priority', 'high'),
            due_at=timezone.now() + timedelta(hours=int(config.get('timeout_hours', 24))),
            metadata={'source_action_definition_id': str(action_definition.id), **config.get('payload', {})},
            wait_for_completion=True,
        )
        return {'human_task_id': str(task.id)}

    @staticmethod
    def execute_action(
        *,
        instance,
        stage_execution,
        action_definition: WorkflowActionDefinition,
        action_context: dict[str, Any] | None = None,
    ) -> WorkflowActionExecutionLog:
        action_log = WorkflowActionExecutionLog.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_execution,
            action_definition=action_definition,
            action_type=action_definition.action_type,
            status='pending',
            started_at=timezone.now(),
            metadata={'action_context': action_context or {}},
        )

        action_log.status = 'running'
        action_log.save(update_fields=['status', 'started_at', 'updated_at'])

        config = action_definition.action_config or {}
        run_mode = action_definition.run_mode

        if run_mode in {'deferred', 'async'} and action_definition.action_type != 'schedule_action':
            task = WorkflowSchedulerEngine.schedule_task(
                workflow_instance=instance,
                stage_execution=stage_execution,
                task_type='workflow_resume',
                scheduled_at=timezone.now() + timedelta(seconds=int(config.get('delay_seconds', 60))),
                payload={
                    'context': {
                        'deferred_action_definition_id': str(action_definition.id),
                        'action_context': action_context or {},
                    },
                    'max_retries': int(config.get('max_retries', 1)),
                    'retry_delay_seconds': int(config.get('retry_delay_seconds', 300)),
                },
            )
            return WorkflowActionHandlersEngine.log_action_execution_result(
                action_log=action_log,
                status='deferred',
                execution_result={'scheduled_task_id': str(task.id), 'run_mode': run_mode},
            )

        handler_map = {
            'assign_actor': WorkflowActionHandlersEngine.execute_assign_actor,
            'create_task': WorkflowActionHandlersEngine.execute_create_task,
            'send_notification': WorkflowActionHandlersEngine.execute_send_notification,
            'update_entity_status': WorkflowActionHandlersEngine.execute_update_entity_status,
            'move_stage': WorkflowActionHandlersEngine.execute_move_stage,
            'create_interview': WorkflowActionHandlersEngine.execute_create_interview,
            'update_interview': WorkflowActionHandlersEngine.execute_update_interview,
            'create_offer': WorkflowActionHandlersEngine.execute_create_offer,
            'update_offer': WorkflowActionHandlersEngine.execute_update_offer,
            'generate_document': WorkflowActionHandlersEngine.execute_generate_document,
            'create_sla': WorkflowActionHandlersEngine.execute_create_sla,
            'create_handoff': WorkflowActionHandlersEngine.execute_create_handoff,
            'schedule_action': WorkflowActionHandlersEngine.execute_schedule_action,
            'request_approval': WorkflowActionHandlersEngine.execute_request_approval,
            'create_note': WorkflowActionHandlersEngine.execute_create_task,
            'add_tag': WorkflowActionHandlersEngine.execute_update_entity_status,
        }

        handler = handler_map.get(action_definition.action_type)
        if handler is None:
            return WorkflowActionHandlersEngine.log_action_execution_result(
                action_log=action_log,
                status='skipped',
                execution_result={'reason': 'No handler available for action type.'},
            )

        try:
            execution_result = handler(instance, stage_execution, action_definition)
            success_status = 'completed'
            if action_definition.action_type == 'schedule_action':
                success_status = 'deferred'
            return WorkflowActionHandlersEngine.log_action_execution_result(
                action_log=action_log,
                status=success_status,
                execution_result=execution_result,
            )
        except Exception as exc:
            WorkflowActionHandlersEngine.log_action_execution_result(
                action_log=action_log,
                status='failed',
                execution_result={'exception_type': exc.__class__.__name__},
                error_message=str(exc),
            )
            WorkflowActionHandlersEngine._apply_failure_policy(instance, stage_execution, action_definition, action_log, exc)
            return action_log

    @staticmethod
    def execute_stage_actions(
        *,
        instance,
        stage_execution,
        stage_id=None,
        stage_event: str = 'stage_enter',
        action_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        sid = stage_id or (stage_execution.stage_id if stage_execution else instance.current_stage_id)
        if not sid:
            return {'executed': 0, 'failed': 0, 'deferred': 0, 'skipped': 0, 'stage_event': stage_event}

        actions = list(
            WorkflowActionDefinition.objects.filter(
                workflow_id=instance.workflow_id,
                stage_id=sid,
                is_active=True,
            )
            .order_by('execution_order', 'created_at')
        )
        actions = [
            action for action in actions
            if (action.action_config or {}).get('stage_event', 'stage_enter') == stage_event
        ]
        if not actions:
            return {'executed': 0, 'failed': 0, 'deferred': 0, 'skipped': 0, 'stage_event': stage_event}

        action_results: dict[str, WorkflowActionExecutionLog] = {}
        pending = list(actions)
        stalled_rounds = 0

        while pending:
            executed_in_round = 0
            next_pending = []
            for action in pending:
                dependencies = list(
                    WorkflowActionDependency.objects.filter(action_definition=action).select_related('depends_on_action')
                )
                if dependencies and not all(
                    WorkflowActionHandlersEngine._dependency_satisfied(
                        dependency=dependency,
                        action_results=action_results,
                    )
                    for dependency in dependencies
                ):
                    next_pending.append(action)
                    continue

                log = WorkflowActionHandlersEngine.execute_action(
                    instance=instance,
                    stage_execution=stage_execution,
                    action_definition=action,
                    action_context=action_context,
                )
                action_results[str(action.id)] = log
                executed_in_round += 1

                if log.status == 'failed':
                    cfg = action.action_config or {}
                    if bool(cfg.get('fail_workflow_on_error')) and not bool(cfg.get('continue_on_error', True)):
                        # Stop further actions for this stage event.
                        pending = []
                        next_pending = []
                        break

            if executed_in_round == 0:
                stalled_rounds += 1
            else:
                stalled_rounds = 0

            if stalled_rounds > 1:
                # Dependency deadlock/unmet requirements.
                for action in next_pending:
                    skip_log = WorkflowActionExecutionLog.objects.create(
                        tenant_id=instance.tenant_id,
                        workflow_instance=instance,
                        stage_execution=stage_execution,
                        action_definition=action,
                        action_type=action.action_type,
                        status='skipped',
                        started_at=timezone.now(),
                        completed_at=timezone.now(),
                        error_message='Unmet dependency conditions',
                        execution_result={'stage_event': stage_event},
                    )
                    action_results[str(action.id)] = skip_log
                break

            pending = next_pending

        statuses = [log.status for log in action_results.values()]
        return {
            'executed': len(statuses),
            'failed': len([s for s in statuses if s == 'failed']),
            'deferred': len([s for s in statuses if s == 'deferred']),
            'skipped': len([s for s in statuses if s == 'skipped']),
            'stage_event': stage_event,
            'logs': [
                {
                    'action_definition_id': str(log.action_definition_id) if log.action_definition_id else None,
                    'action_type': log.action_type,
                    'status': log.status,
                    'error_message': log.error_message,
                }
                for log in action_results.values()
            ],
        }


# Function-style exports requested by prompt contract.
execute_stage_actions = WorkflowActionHandlersEngine.execute_stage_actions
execute_action = WorkflowActionHandlersEngine.execute_action
execute_assign_actor = WorkflowActionHandlersEngine.execute_assign_actor
execute_create_task = WorkflowActionHandlersEngine.execute_create_task
execute_send_notification = WorkflowActionHandlersEngine.execute_send_notification
execute_update_entity_status = WorkflowActionHandlersEngine.execute_update_entity_status
execute_move_stage = WorkflowActionHandlersEngine.execute_move_stage
execute_create_interview = WorkflowActionHandlersEngine.execute_create_interview
execute_update_interview = WorkflowActionHandlersEngine.execute_update_interview
execute_create_offer = WorkflowActionHandlersEngine.execute_create_offer
execute_update_offer = WorkflowActionHandlersEngine.execute_update_offer
execute_generate_document = WorkflowActionHandlersEngine.execute_generate_document
execute_create_sla = WorkflowActionHandlersEngine.execute_create_sla
execute_create_handoff = WorkflowActionHandlersEngine.execute_create_handoff
execute_schedule_action = WorkflowActionHandlersEngine.execute_schedule_action
execute_request_approval = WorkflowActionHandlersEngine.execute_request_approval
log_action_execution_result = WorkflowActionHandlersEngine.log_action_execution_result
