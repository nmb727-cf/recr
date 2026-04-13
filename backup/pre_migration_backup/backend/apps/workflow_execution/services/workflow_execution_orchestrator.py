from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.orchestration_center.models.workflow import WorkflowNode, WorkflowEdge
from apps.workflow_execution.models import (
    WorkflowActionDefinition,
    WorkflowExecutionContext,
    WorkflowExecutionDecision,
    WorkflowInstance,
    WorkflowOrchestratorLog,
    WorkflowStageExecution,
    WorkflowStageTransition,
    WorkflowHumanTask,
)
from apps.workflow_execution.services.workflow_cross_entity_routing_engine import (
    WorkflowCrossEntityRoutingEngine,
)
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.workflow_execution.services.workflow_sla_engine import WorkflowSLAEngine
from apps.workflow_execution.services.workflow_notification_engine import WorkflowNotificationEngine
from apps.workflow_execution.services.workflow_scheduler_engine import WorkflowSchedulerEngine
from apps.workflow_execution.services.workflow_conditional_logic_engine import WorkflowConditionalLogicEngine
from apps.workflow_execution.services.workflow_action_handlers_engine import WorkflowActionHandlersEngine
from apps.workflow_execution.services.workflow_failure_recovery_engine import WorkflowFailureRecoveryEngine
from apps.workflow_execution.services.workflow_human_task_engine import WorkflowHumanTaskEngine
from apps.workflow_execution.services.workflow_stage_engine import (
    ConditionEvaluator,
    WAIT_NODE_TYPES,
    WorkflowStageEngine,
)


@dataclass
class OrchestratorAction:
    decision_type: str
    decision_result: str
    decision_reason: str
    payload: dict[str, Any]


class WorkflowExecutionOrchestrator:
    """Main orchestration brain for runtime stage decisions."""

    @staticmethod
    def _log(instance: WorkflowInstance, log_type: str, message: str, *, stage_execution=None, metadata=None):
        log = WorkflowOrchestratorLog.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_execution,
            log_type=log_type,
            message=message,
            metadata=metadata or {},
        )
        event_map = {
            'start': 'transition',
            'stage_enter': 'stage_started',
            'stage_exit': 'stage_completed',
            'wait': 'waiting',
            'resume': 'resumed',
            'route': 'routing',
            'retry': 'retry',
            'fail': 'failure',
            'complete': 'transition',
            'debug': 'transition',
        }
        WorkflowInstanceTracker._timeline(
            instance=instance,
            event_type=event_map.get(log_type, 'transition'),
            event_label=f"Orchestrator {log_type}: {message}",
            stage_execution=stage_execution,
            actor_type='system',
            payload={'log_id': str(log.id), **(metadata or {})},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.create_trace(
            workflow_instance=instance,
            trace_key=f'orchestrator_{log_type}',
            trace_type='transition',
            source_module='workflow_execution_orchestrator',
            source_id=str(log.id),
            trace_message=message,
            severity='error' if log_type == 'fail' else 'info',
            metadata=metadata or {},
        )
        return log

    @staticmethod
    def _decision(instance: WorkflowInstance, action: OrchestratorAction, *, stage_execution=None):
        decision = WorkflowExecutionDecision.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_execution,
            decision_type=action.decision_type,
            decision_result=action.decision_result,
            decision_reason=action.decision_reason,
            metadata=action.payload,
        )
        WorkflowInstanceTracker._timeline(
            instance=instance,
            event_type='transition',
            event_label=f"Decision: {action.decision_type} -> {action.decision_result}",
            stage_execution=stage_execution,
            actor_type='system',
            payload={'decision_id': str(decision.id), 'reason': action.decision_reason, **(action.payload or {})},
        )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.create_trace(
            workflow_instance=instance,
            trace_key='decision',
            trace_type='condition',
            source_module='workflow_execution_orchestrator',
            source_id=str(decision.id),
            trace_message=f'{action.decision_type} => {action.decision_result}',
            severity='info',
            metadata={'reason': action.decision_reason, **(action.payload or {})},
        )
        return decision

    @staticmethod
    def initialize_execution_context(
        instance: WorkflowInstance,
        context: dict[str, Any] | None = None,
        source_type: str = 'workflow',
    ):
        for key, value in (context or {}).items():
            WorkflowExecutionContext.objects.update_or_create(
                workflow_instance=instance,
                context_key=key,
                defaults={
                    'tenant_id': instance.tenant_id,
                    'context_value': value,
                    'source_type': source_type,
                },
            )
        if context:
            merged = dict(instance.context_data)
            merged.update(context)
            instance.context_data = merged
            instance.save(update_fields=['context_data', 'updated_at'])

    @staticmethod
    def load_current_stage(instance: WorkflowInstance):
        if instance.current_stage_id:
            return instance.stage_executions.filter(stage_id=instance.current_stage_id).order_by('-created_at').first()
        return instance.stage_executions.order_by('-created_at').first()

    @staticmethod
    def evaluate_current_stage(instance: WorkflowInstance, stage_execution: WorkflowStageExecution | None, *, resume_event=None, context=None):
        return WorkflowExecutionOrchestrator.determine_next_action(
            instance,
            stage_execution,
            resume_event=resume_event,
            context=context,
        )

    @staticmethod
    def determine_next_action(instance: WorkflowInstance, stage_execution: WorkflowStageExecution | None, *, resume_event=None, context=None):
        if instance.status in {'completed', 'cancelled'}:
            return OrchestratorAction(
                decision_type='completion_check',
                decision_result='already_complete',
                decision_reason='Workflow already terminal.',
                payload={'status': instance.status},
            )

        if instance.status == 'failed':
            if WorkflowExecutionOrchestrator._can_retry(instance, stage_execution):
                return OrchestratorAction(
                    decision_type='retry_required',
                    decision_result='retry',
                    decision_reason='Workflow is failed but retry is allowed.',
                    payload={},
                )
            return OrchestratorAction(
                decision_type='failure_classification',
                decision_result='fail',
                decision_reason='Workflow failed and retry is not allowed.',
                payload={},
            )

        if instance.status == 'waiting':
            if resume_event or (context or {}).get('resume'):
                return OrchestratorAction(
                    decision_type='resume_allowed',
                    decision_result='resume',
                    decision_reason='Resume signal received for waiting instance.',
                    payload={'resume_event': resume_event or ''},
                )
            return OrchestratorAction(
                decision_type='wait_required',
                decision_result='wait',
                decision_reason='Instance is waiting and no resume signal is present.',
                payload={},
            )

        if stage_execution and stage_execution.status == 'failed':
            if WorkflowExecutionOrchestrator._can_retry(instance, stage_execution):
                return OrchestratorAction(
                    decision_type='retry_required',
                    decision_result='retry',
                    decision_reason='Current stage failed and retry is allowed.',
                    payload={'stage_execution_id': str(stage_execution.id)},
                )
            return OrchestratorAction(
                decision_type='failure_classification',
                decision_result='fail',
                decision_reason='Current stage failed and retry is not allowed.',
                payload={'stage_execution_id': str(stage_execution.id)},
            )

        wait_req = WorkflowExecutionOrchestrator.determine_wait_requirement(instance, stage_execution)
        if wait_req['required']:
            return OrchestratorAction(
                decision_type='wait_required',
                decision_result='wait',
                decision_reason=wait_req['reason'],
                payload=wait_req,
            )

        route_req = WorkflowExecutionOrchestrator.determine_routing_requirement(instance, stage_execution, context=context)
        if route_req['required']:
            return OrchestratorAction(
                decision_type='routing_required',
                decision_result='route',
                decision_reason=route_req['reason'],
                payload=route_req,
            )

        completion = WorkflowExecutionOrchestrator.determine_completion_status(instance, stage_execution)
        if completion['complete']:
            return OrchestratorAction(
                decision_type='completion_check',
                decision_result='complete',
                decision_reason=completion['reason'],
                payload=completion,
            )

        transition = WorkflowExecutionOrchestrator.determine_next_transition(instance, stage_execution, context=context)
        if transition:
            return OrchestratorAction(
                decision_type='transition_select',
                decision_result='move_forward',
                decision_reason=transition.get('reason', 'Transition selected.'),
                payload=transition,
            )

        return OrchestratorAction(
            decision_type='completion_check',
            decision_result='complete',
            decision_reason='No valid next transition found; completing.',
            payload={},
        )

    @staticmethod
    def _can_retry(instance: WorkflowInstance, stage_execution: WorkflowStageExecution | None):
        if not stage_execution:
            return False
        max_retries = (stage_execution.metadata or {}).get('max_retries', 1)
        current_retries = (stage_execution.metadata or {}).get('retry_count', 0)
        return current_retries < max_retries

    @staticmethod
    def determine_next_transition(instance: WorkflowInstance, stage_execution: WorkflowStageExecution | None, context=None):
        effective_context = dict(instance.context_data)
        effective_context.update(context or {})

        if instance.current_stage_id:
            try:
                from_node = WorkflowNode.objects.get(id=instance.current_stage_id)
            except WorkflowNode.DoesNotExist:
                return None
        else:
            from_node = None
            start_node = WorkflowNode.objects.filter(workflow_id=instance.workflow_id, node_type='start').first()
            if start_node:
                return {
                    'from_stage_id': None,
                    'to_stage_id': str(start_node.id),
                    'transition_type': 'automatic',
                    'label': 'start',
                    'reason': 'Workflow start node selected.',
                }
            return None

        transitions = WorkflowStageTransition.objects.filter(
            workflow_id=instance.workflow_id,
            from_stage_id=from_node.id,
            is_active=True,
        ).order_by('priority')

        conditional = WorkflowConditionalLogicEngine.determine_transition_from_conditions(
            workflow_instance=instance,
            stage_execution=stage_execution,
            stage_id=from_node.id,
            context=effective_context,
            write_log=True,
        )
        if conditional is not None:
            transition = conditional['transition']
            return {
                'from_stage_id': str(from_node.id),
                'to_stage_id': str(transition.to_stage_id),
                'transition_type': 'automatic' if transition.transition_type == 'auto' else transition.transition_type,
                'label': transition.label,
                'reason': conditional['reason'],
                'condition_result': {
                    'condition_group_id': str(conditional['group'].id),
                    'group_result': conditional['evaluation']['group_result'],
                    'rule_results': conditional['evaluation']['rule_results'],
                },
            }

        for transition in transitions:
            ok, reason, trace = ConditionEvaluator.evaluate(transition.condition_config, effective_context)
            if ok:
                return {
                    'from_stage_id': str(from_node.id),
                    'to_stage_id': str(transition.to_stage_id),
                    'transition_type': 'automatic' if transition.transition_type == 'auto' else transition.transition_type,
                    'label': transition.label,
                    'reason': reason,
                    'condition_result': trace,
                }

        for edge in WorkflowEdge.objects.filter(workflow_id=instance.workflow_id, source_node=from_node):
            ok, reason, trace = ConditionEvaluator.evaluate(edge.condition or {}, effective_context)
            if ok:
                return {
                    'from_stage_id': str(from_node.id),
                    'to_stage_id': str(edge.target_node_id),
                    'transition_type': 'automatic',
                    'label': '',
                    'reason': reason,
                    'condition_result': trace,
                }

        return None

    @staticmethod
    def determine_wait_requirement(instance: WorkflowInstance, stage_execution: WorkflowStageExecution | None):
        if instance.status == 'waiting':
            return {'required': True, 'reason': 'Instance is already waiting.'}
        pending_human_task = WorkflowHumanTask.objects.filter(
            workflow_instance=instance,
            status__in=['pending', 'in_progress'],
        ).order_by('-created_at').first()
        if pending_human_task is not None:
            return {
                'required': True,
                'reason': f'Pending human task requires wait: {pending_human_task.title}',
                'human_task_id': str(pending_human_task.id),
            }
        if not instance.current_stage_id:
            return {'required': False, 'reason': ''}
        try:
            node = WorkflowNode.objects.get(id=instance.current_stage_id)
        except WorkflowNode.DoesNotExist:
            return {'required': False, 'reason': ''}
        if node.node_type in WAIT_NODE_TYPES:
            return {
                'required': True,
                'reason': f'Stage type {node.node_type} requires wait.',
                'node_type': node.node_type,
                'wait_reason': (node.config or {}).get('wait_reason', ''),
            }
        return {'required': False, 'reason': ''}

    @staticmethod
    def determine_routing_requirement(instance: WorkflowInstance, stage_execution: WorkflowStageExecution | None, context=None):
        stage_id = None
        if stage_execution:
            stage_id = stage_execution.stage_id
        elif instance.current_stage_id:
            stage_id = instance.current_stage_id

        if not stage_id:
            return {'required': False, 'reason': ''}

        rule = WorkflowCrossEntityRoutingEngine.determine_next_route(
            instance,
            stage_id=stage_id,
            context=context,
        )
        if not rule:
            return {'required': False, 'reason': ''}
        return {
            'required': True,
            'reason': f'Routing rule matched: {rule.label or rule.id}',
            'rule_id': str(rule.id),
            'stage_id': str(stage_id),
        }

    @staticmethod
    def determine_completion_status(instance: WorkflowInstance, stage_execution: WorkflowStageExecution | None):
        if instance.status == 'completed':
            return {'complete': True, 'reason': 'Workflow already completed.'}

        if instance.current_stage_id:
            try:
                node = WorkflowNode.objects.get(id=instance.current_stage_id)
                if node.node_type == 'end':
                    return {'complete': True, 'reason': 'Current stage is end node.'}
            except WorkflowNode.DoesNotExist:
                pass

        if stage_execution and stage_execution.status in {'completed', 'skipped'}:
            transition = WorkflowExecutionOrchestrator.determine_next_transition(instance, stage_execution)
            if not transition:
                return {'complete': True, 'reason': 'No next transition from completed stage.'}

        return {'complete': False, 'reason': ''}

    @staticmethod
    def apply_transition(instance: WorkflowInstance, action_payload: dict[str, Any]):
        to_stage_id = action_payload.get('to_stage_id')
        if not to_stage_id:
            return None

        from_node = None
        if action_payload.get('from_stage_id'):
            try:
                from_node = WorkflowNode.objects.get(id=action_payload['from_stage_id'])
            except WorkflowNode.DoesNotExist:
                from_node = None

        try:
            to_node = WorkflowNode.objects.get(id=to_stage_id)
        except WorkflowNode.DoesNotExist:
            return None

        WorkflowExecutionOrchestrator._log(instance, 'stage_enter', f'Entering stage {to_node.node_type}', metadata={'stage_id': str(to_node.id)})
        if from_node is None:
            WorkflowStageEngine.complete_stage(instance, to_node, triggered_by='system')
        else:
            WorkflowStageEngine.execute_stage_transition(
                instance,
                from_node,
                to_node,
                transition_type=action_payload.get('transition_type', 'automatic'),
                label=action_payload.get('label', ''),
                triggered_by='system',
                reason=action_payload.get('reason', ''),
                condition_result=action_payload.get('condition_result', {}),
            )
        WorkflowExecutionOrchestrator._log(instance, 'stage_exit', f'Applied transition to {to_node.node_type}', metadata={'stage_id': str(to_node.id)})
        return to_node

    @staticmethod
    def apply_wait(instance: WorkflowInstance, stage_execution: WorkflowStageExecution | None, action_payload: dict[str, Any]):
        current_stage_id = instance.current_stage_id
        if not current_stage_id:
            return None
        try:
            node = WorkflowNode.objects.get(id=current_stage_id)
        except WorkflowNode.DoesNotExist:
            return None
        wait_state = WorkflowStageEngine.handle_wait_state(instance, node, triggered_by='system')
        WorkflowExecutionOrchestrator._log(
            instance,
            'wait',
            action_payload.get('reason', 'Workflow waiting.'),
            stage_execution=stage_execution,
            metadata={'wait_state_id': str(wait_state.id) if wait_state else None},
        )
        return wait_state

    @staticmethod
    def apply_routing(instance: WorkflowInstance, stage_execution: WorkflowStageExecution | None, action_payload: dict[str, Any], context=None):
        stage_id = stage_execution.stage_id if stage_execution else instance.current_stage_id
        if not stage_id:
            return None
        WorkflowCrossEntityRoutingEngine.apply_routing_rules(instance, stage_id=stage_id, context=context or {})
        WorkflowExecutionOrchestrator._log(
            instance,
            'route',
            action_payload.get('reason', 'Routing applied.'),
            stage_execution=stage_execution,
            metadata=action_payload,
        )
        return True

    @staticmethod
    def apply_retry(instance: WorkflowInstance, stage_execution: WorkflowStageExecution | None, action_payload: dict[str, Any]):
        retried = WorkflowInstanceTracker.retry_stage(instance, stage_execution=stage_execution, triggered_by='system', metadata=action_payload)
        WorkflowExecutionOrchestrator._log(
            instance,
            'retry',
            action_payload.get('reason', 'Retry applied.'),
            stage_execution=stage_execution,
            metadata={'retried_stage_execution_id': str(retried.id) if retried else None},
        )
        return retried

    @staticmethod
    def complete_workflow_instance(instance: WorkflowInstance, reason='Workflow completed by orchestrator'):
        WorkflowStageEngine._complete_workflow(instance, triggered_by='system')
        WorkflowExecutionOrchestrator._log(instance, 'complete', reason)
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.create_timeline_entry(
            workflow_instance=instance,
            entry_type='workflow_completed',
            entry_label='Workflow completed',
            entry_description=reason,
            actor_type='system',
            metadata={'source': 'orchestrator'},
        )
        if instance.started_at and instance.completed_at:
            WorkflowObservabilityEngine.record_metric(
                workflow_instance=instance,
                metric_name='workflow_total_duration_seconds',
                metric_value=(instance.completed_at - instance.started_at).total_seconds(),
                metric_type='duration',
                metadata={},
            )
        return instance

    @staticmethod
    def fail_workflow_instance(instance: WorkflowInstance, reason='Workflow failed by orchestrator'):
        WorkflowStageEngine.fail_stage(instance, reason=reason, triggered_by='system')
        WorkflowExecutionOrchestrator._log(instance, 'fail', reason)
        current_stage_execution = WorkflowExecutionOrchestrator.load_current_stage(instance)
        if current_stage_execution is not None:
            try:
                recovery_case = WorkflowFailureRecoveryEngine.create_recovery_case(
                    workflow_instance=instance,
                    stage_execution=current_stage_execution,
                    recovery_type='stage_failure',
                    failure_type='',
                    error_message=reason,
                    error_code='orchestrator_failure',
                    metadata={'source': 'workflow_execution_orchestrator'},
                )
                WorkflowExecutionOrchestrator._log(
                    instance,
                    'debug',
                    'Failure recovery case opened by orchestrator.',
                    stage_execution=current_stage_execution,
                    metadata={'recovery_case_id': str(recovery_case.id)},
                )
            except Exception as exc:
                WorkflowExecutionOrchestrator._log(
                    instance,
                    'debug',
                    'Failed to open recovery case from orchestrator.',
                    stage_execution=current_stage_execution,
                    metadata={'error': str(exc)},
                )
        from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

        WorkflowObservabilityEngine.create_timeline_entry(
            workflow_instance=instance,
            entry_type='workflow_failed',
            entry_label='Workflow failed',
            entry_description=reason,
            actor_type='system',
            metadata={'source': 'orchestrator'},
        )
        return instance

    @staticmethod
    @transaction.atomic
    def orchestrate_workflow_instance(
        instance_id,
        *,
        context: dict[str, Any] | None = None,
        resume_event: str | None = None,
        source_type: str = 'system',
    ):
        instance = WorkflowInstance.objects.select_for_update().get(id=instance_id)
        WorkflowExecutionOrchestrator.initialize_execution_context(instance, context=context, source_type=source_type)
        due_tasks = WorkflowSchedulerEngine.process_due_tasks(limit=100)
        if due_tasks:
            WorkflowExecutionOrchestrator._log(
                instance,
                'debug',
                'Scheduler processed due tasks in orchestration cycle.',
                metadata={'processed_task_count': len(due_tasks)},
            )
        sla_events = WorkflowSLAEngine.check_sla_status(workflow_instance=instance)
        if sla_events:
            WorkflowExecutionOrchestrator._log(
                instance,
                'debug',
                'SLA engine emitted events during orchestration cycle.',
                metadata={'sla_events': sla_events},
            )

        current_stage_execution = WorkflowExecutionOrchestrator.load_current_stage(instance)
        if not current_stage_execution:
            WorkflowExecutionOrchestrator._log(instance, 'start', 'Orchestrator started workflow runtime.')
        else:
            WorkflowExecutionOrchestrator._log(
                instance,
                'debug',
                'Orchestrator evaluation cycle started.',
                stage_execution=current_stage_execution,
                metadata={'instance_status': instance.status, 'stage_status': current_stage_execution.status},
            )

        overdue_human_tasks = list(
            WorkflowHumanTask.objects.filter(
                workflow_instance=instance,
                status__in=['pending', 'in_progress'],
                due_at__isnull=False,
                due_at__lte=timezone.now(),
            ).order_by('due_at')
        )
        for task in overdue_human_tasks:
            WorkflowHumanTaskEngine.expire_human_task(task=task)
        if overdue_human_tasks:
            WorkflowExecutionOrchestrator._log(
                instance,
                'debug',
                'Expired overdue human tasks in orchestrator cycle.',
                stage_execution=current_stage_execution,
                metadata={'expired_human_task_count': len(overdue_human_tasks)},
            )

        # Support deferred/scheduled action execution through orchestrator context.
        deferred_action_id = (context or {}).get('deferred_action_definition_id')
        if deferred_action_id:
            action_def = WorkflowActionDefinition.objects.filter(
                id=deferred_action_id,
                workflow_id=instance.workflow_id,
                is_active=True,
            ).first()
            if action_def is None:
                WorkflowExecutionOrchestrator._log(
                    instance,
                    'debug',
                    'Deferred action definition not found for orchestrator cycle.',
                    stage_execution=current_stage_execution,
                    metadata={'deferred_action_definition_id': str(deferred_action_id)},
                )
            else:
                action_stage_execution = (
                    current_stage_execution
                    if current_stage_execution and current_stage_execution.stage_id == action_def.stage_id
                    else instance.stage_executions.filter(stage_id=action_def.stage_id).order_by('-created_at').first()
                )
                deferred_log = WorkflowActionHandlersEngine.execute_action(
                    instance=instance,
                    stage_execution=action_stage_execution,
                    action_definition=action_def,
                    action_context=(context or {}).get('action_context', {}),
                )
                WorkflowExecutionOrchestrator._log(
                    instance,
                    'debug',
                    'Deferred action executed in orchestrator cycle.',
                    stage_execution=action_stage_execution,
                    metadata={
                        'deferred_action_definition_id': str(action_def.id),
                        'action_log_id': str(deferred_log.id),
                        'action_status': deferred_log.status,
                    },
                )

        action = WorkflowExecutionOrchestrator.evaluate_current_stage(
            instance,
            current_stage_execution,
            resume_event=resume_event,
            context=context,
        )
        decision = WorkflowExecutionOrchestrator._decision(instance, action, stage_execution=current_stage_execution)

        if action.decision_result == 'move_forward':
            WorkflowExecutionOrchestrator.apply_transition(instance, action.payload)
        elif action.decision_result == 'wait':
            WorkflowExecutionOrchestrator.apply_wait(instance, current_stage_execution, action.payload)
        elif action.decision_result == 'resume':
            resumed = WorkflowStageEngine.resume_instance(instance.id, triggered_by='event' if resume_event else 'system', context=context)
            WorkflowExecutionOrchestrator._log(
                instance,
                'resume',
                action.decision_reason,
                stage_execution=current_stage_execution,
                metadata={'resumed': bool(resumed), 'resume_event': resume_event or ''},
            )
        elif action.decision_result == 'route':
            WorkflowExecutionOrchestrator.apply_routing(instance, current_stage_execution, action.payload, context=context)
        elif action.decision_result == 'retry':
            WorkflowExecutionOrchestrator.apply_retry(instance, current_stage_execution, action.payload)
        elif action.decision_result in {'fail'}:
            WorkflowExecutionOrchestrator.fail_workflow_instance(instance, reason=action.decision_reason)
        elif action.decision_result in {'complete', 'already_complete'}:
            WorkflowExecutionOrchestrator.complete_workflow_instance(instance, reason=action.decision_reason)

        instance.refresh_from_db()
        processed_notifications = WorkflowNotificationEngine.process_notification_queue(limit=100)
        if processed_notifications:
            WorkflowExecutionOrchestrator._log(
                instance,
                'debug',
                'Workflow notifications processed in orchestration cycle.',
                metadata={'processed_notifications': processed_notifications[:20]},
            )
        return {
            'instance_id': str(instance.id),
            'version_id': str(instance.version_id) if instance.version_id else None,
            'status': instance.status,
            'current_stage_id': str(instance.current_stage_id) if instance.current_stage_id else None,
            'decision_id': str(decision.id),
            'decision_type': decision.decision_type,
            'decision_result': decision.decision_result,
            'decision_reason': decision.decision_reason,
            'processed_scheduler_tasks': len(due_tasks),
            'processed_notifications': len(processed_notifications),
        }


# Function-level exports as requested by prompt contract.
orchestrate_workflow_instance = WorkflowExecutionOrchestrator.orchestrate_workflow_instance
initialize_execution_context = WorkflowExecutionOrchestrator.initialize_execution_context
load_current_stage = WorkflowExecutionOrchestrator.load_current_stage
evaluate_current_stage = WorkflowExecutionOrchestrator.evaluate_current_stage
determine_next_action = WorkflowExecutionOrchestrator.determine_next_action
determine_next_transition = WorkflowExecutionOrchestrator.determine_next_transition
determine_wait_requirement = WorkflowExecutionOrchestrator.determine_wait_requirement
determine_routing_requirement = WorkflowExecutionOrchestrator.determine_routing_requirement
determine_completion_status = WorkflowExecutionOrchestrator.determine_completion_status
apply_transition = WorkflowExecutionOrchestrator.apply_transition
apply_wait = WorkflowExecutionOrchestrator.apply_wait
apply_routing = WorkflowExecutionOrchestrator.apply_routing
apply_retry = WorkflowExecutionOrchestrator.apply_retry
complete_workflow_instance = WorkflowExecutionOrchestrator.complete_workflow_instance
fail_workflow_instance = WorkflowExecutionOrchestrator.fail_workflow_instance
