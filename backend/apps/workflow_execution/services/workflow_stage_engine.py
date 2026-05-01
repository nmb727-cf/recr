"""
WorkflowStageEngine
====================
Full stage-transition engine for the workflow execution layer.

Responsibilities:
  • move_to_next_stage()          — evaluate transitions, route to next node
  • evaluate_transition_conditions() — AND/OR numeric/string/boolean evaluation
  • execute_stage_transition()    — log + dispatch (complete / wait / end)
  • handle_wait_state()           — create WorkflowWaitState, pause instance
  • resume_wait_state()           — mark state resumed, continue execution
  • complete_stage()              — run a stage node and advance
  • fail_stage()                  — mark stage failed, fail instance
  • skip_stage()                  — mark stage skipped, advance from it

Decision routing uses WorkflowStageTransition rows (if defined for the workflow)
and falls back to raw WorkflowEdge.condition when none exist.

condition_config schema (WorkflowStageTransition):
  Single:  {"field": "score", "op": "gt", "value": 70}
  Grouped: {"operator": "and", "conditions": [...single...]}
  ops:     eq | ne | gt | gte | lt | lte | contains | not_contains | in | not_in
"""
import logging
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowInstance,
    WorkflowStageExecution,
    WorkflowExecutionTimeline,
    WorkflowStageTransition,
    WorkflowWaitState,
    WorkflowTransitionLog,
    NODE_TYPE_TO_WAIT_TYPE,
    WAIT_TYPE_TO_WAIT_REASON,
    WAIT_NODE_TYPES,
    WAIT_REASON_RESUME_EVENTS,
)
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.workflow_execution.services.workflow_conditional_logic_engine import WorkflowConditionalLogicEngine
from apps.orchestration_center.models.workflow import WorkflowNode

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------#
# Internal helpers                                                             #
# ---------------------------------------------------------------------------#

def _timeline(instance, action, stage_id=None, actor='system', metadata=None):
    WorkflowExecutionTimeline.objects.create(
        tenant_id=instance.tenant_id,
        workflow_instance=instance,
        stage_id=stage_id,
        action=action,
        actor=actor,
        metadata=metadata or {},
    )


def _transition_log(instance, from_node, to_node, transition_type='auto',
                    label='', triggered_by='system', actor_id=None,
                    reason='', condition_result=None):
    normalized_transition = 'automatic' if transition_type == 'auto' else transition_type
    log = WorkflowTransitionLog.objects.create(
        tenant_id=instance.tenant_id,
        workflow_instance=instance,
        from_stage=from_node.node_type if from_node else '',
        to_stage=to_node.node_type if to_node else '',
        from_stage_id=from_node.id if from_node else None,
        to_stage_id=to_node.id if to_node else None,
        from_stage_name=from_node.node_type if from_node else '',
        to_stage_name=to_node.node_type if to_node else '',
        transition_type=normalized_transition,
        label=label,
        triggered_by=triggered_by,
        actor_id=actor_id,
        reason=reason,
        condition_result=condition_result or {},
    )
    WorkflowInstanceTracker._timeline(
        instance=instance,
        event_type='transition',
        event_label=f"Transition: {(from_node.node_type if from_node else 'start')} -> {(to_node.node_type if to_node else 'end')}",
        transition_log=log,
        actor_type=triggered_by,
        actor_id=actor_id,
        payload={'transition_type': normalized_transition, 'reason': reason, **(condition_result or {})},
    )


# ---------------------------------------------------------------------------#
# Condition evaluator                                                          #
# ---------------------------------------------------------------------------#

class ConditionEvaluator:
    """Evaluates condition_config dicts against a context dict."""

    OPS = {
        'eq':          lambda a, b: str(a) == str(b),
        'ne':          lambda a, b: str(a) != str(b),
        'gt':          lambda a, b: ConditionEvaluator._num(a) > ConditionEvaluator._num(b),
        'gte':         lambda a, b: ConditionEvaluator._num(a) >= ConditionEvaluator._num(b),
        'lt':          lambda a, b: ConditionEvaluator._num(a) < ConditionEvaluator._num(b),
        'lte':         lambda a, b: ConditionEvaluator._num(a) <= ConditionEvaluator._num(b),
        'contains':    lambda a, b: str(b) in str(a or ''),
        'not_contains': lambda a, b: str(b) not in str(a or ''),
        'in':          lambda a, b: str(a) in [str(x) for x in (b if isinstance(b, list) else [b])],
        'not_in':      lambda a, b: str(a) not in [str(x) for x in (b if isinstance(b, list) else [b])],
        # Legacy aliases from WorkflowEdge.condition format
        'equals':      lambda a, b: str(a) == str(b),
        'greater_than': lambda a, b: ConditionEvaluator._num(a) > ConditionEvaluator._num(b),
        'less_than':   lambda a, b: ConditionEvaluator._num(a) < ConditionEvaluator._num(b),
    }

    @staticmethod
    def _num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def evaluate_single(cls, condition, context):
        """
        Evaluate one condition dict: {field, op, value}.
        Returns (bool, trace_str).
        """
        if not condition:
            return True, 'no condition'

        field = condition.get('field') or condition.get('key')
        op    = condition.get('op') or condition.get('operator', 'eq')
        value = condition.get('value')

        actual = context.get(field)
        evaluator = cls.OPS.get(op)
        if evaluator is None:
            return False, f"unknown op '{op}'"

        try:
            result = evaluator(actual, value)
        except Exception as exc:
            return False, f"eval error: {exc}"

        trace = f"{field}({actual!r}) {op} {value!r} → {result}"
        return result, trace

    @classmethod
    def evaluate(cls, condition_config, context):
        """
        Evaluate a condition_config (single or grouped) against context.
        Returns (is_match: bool, reason: str, trace: dict).
        """
        if not condition_config:
            return True, 'no conditions defined', {}

        trace = {}

        # Grouped: {"operator": "and"|"or", "conditions": [...]}
        if 'conditions' in condition_config:
            logical_op = condition_config.get('operator', 'and').lower()
            sub_conditions = condition_config['conditions']
            results = []
            for i, sub in enumerate(sub_conditions):
                ok, msg = cls.evaluate_single(sub, context)
                results.append(ok)
                trace[f'condition_{i}'] = msg

            if logical_op == 'or':
                final = any(results)
                reason = f"OR({', '.join(str(r) for r in results)}) = {final}"
            else:  # and
                final = all(results)
                reason = f"AND({', '.join(str(r) for r in results)}) = {final}"

            return final, reason, trace

        # Single condition
        ok, msg = cls.evaluate_single(condition_config, context)
        trace['condition_0'] = msg
        return ok, msg, trace


# ---------------------------------------------------------------------------#
# WorkflowStageEngine                                                          #
# ---------------------------------------------------------------------------#

class WorkflowStageEngine:

    # ------------------------------------------------------------------ #
    # Stage execution                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def complete_stage(instance, node, context=None, triggered_by='system', actor_id=None):
        """
        Run a normal (non-wait) stage node: create execution record, log, then move on.
        context is merged into instance.context_data.
        """
        if context:
            instance.context_data.update(context)
            instance.save(update_fields=['context_data', 'updated_at'])

        stage_exec = WorkflowInstanceTracker.start_stage_execution(
            instance=instance,
            stage_id=node.id,
            stage_name=node.node_type,
            actor_type=triggered_by,
            actor_id=actor_id,
            metadata={},
        )
        from apps.workflow_execution.services.workflow_sla_engine import WorkflowSLAEngine
        WorkflowSLAEngine.initialize_sla(instance, stage_exec)

        _timeline(instance, f"Started execution of {node.node_type} stage",
                  stage_id=node.id, actor=triggered_by)

        # Mark completed
        WorkflowInstanceTracker.complete_stage_execution(
            stage_exec,
            actor_type=triggered_by,
            actor_id=actor_id,
            metadata={},
        )
        WorkflowSLAEngine.resolve_sla(instance, stage_exec)

        _timeline(instance, f"Completed {node.node_type} stage",
                  stage_id=node.id, actor=triggered_by)

        WorkflowStageEngine.move_to_next_stage(
            instance, node, triggered_by=triggered_by, actor_id=actor_id
        )

    @staticmethod
    def fail_stage(instance, stage_id=None, reason='Stage failed',
                   triggered_by='system', actor_id=None):
        """Mark the current (or specified) stage as failed and fail the workflow."""
        sid = stage_id or instance.current_stage_id
        stage_exec = instance.stage_executions.filter(
            stage_id=sid, status__in=['running', 'waiting']
        ).first()
        if stage_exec:
            stage_exec.status = 'failed'
            stage_exec.failed_at = timezone.now()
            stage_exec.completed_at = timezone.now()
            stage_exec.save(update_fields=['status', 'failed_at', 'completed_at', 'updated_at'])
            WorkflowInstanceTracker.log_failure(
                instance,
                stage_execution=stage_exec,
                error_message=reason,
                error_type='stage_failure',
                retry_count=0,
                status='failed',
                actor_type=triggered_by,
                actor_id=actor_id,
                metadata={'stage_id': str(sid) if sid else None},
            )

        _timeline(instance, f"Stage failed: {reason}", stage_id=sid,
                  actor=triggered_by, metadata={'reason': reason})

        # Log transition with no target
        try:
            from_node = WorkflowNode.objects.get(id=sid) if sid else None
        except WorkflowNode.DoesNotExist:
            from_node = None

        _transition_log(
            instance, from_node, None,
            transition_type='manual', label='fail',
            triggered_by=triggered_by, actor_id=actor_id, reason=reason,
        )

        instance.status = 'failed'
        instance.failed_at = timezone.now()
        instance.completed_at = timezone.now()
        instance.save(update_fields=['status', 'failed_at', 'completed_at', 'updated_at'])

    @staticmethod
    def skip_stage(instance, stage_id, reason='Skipped manually',
                   triggered_by='user', actor_id=None):
        """
        Mark a stage as skipped and continue from it to the next stage.
        Works on waiting or running stages.
        """
        stage_exec = instance.stage_executions.filter(
            stage_id=stage_id, status__in=['running', 'waiting', 'pending']
        ).first()
        if stage_exec:
            stage_exec.status = 'skipped'
            stage_exec.completed_at = timezone.now()
            stage_exec.save(update_fields=['status', 'completed_at', 'updated_at'])

        # Cancel any open wait state for this stage
        WorkflowWaitState.objects.filter(
            workflow_instance=instance,
            stage_execution=stage_exec,
            status='waiting',
        ).update(status='cancelled')

        try:
            node = WorkflowNode.objects.get(id=stage_id)
        except WorkflowNode.DoesNotExist:
            logger.error("skip_stage: node %s not found for instance %s", stage_id, instance.id)
            return

        _timeline(instance, f"Stage skipped: {reason}", stage_id=node.id,
                  actor=triggered_by, metadata={'reason': reason})

        _transition_log(
            instance, node, None,
            transition_type='manual', label='skip',
            triggered_by=triggered_by, actor_id=actor_id, reason=reason,
        )

        # Clear wait state from instance if this was the waiting stage
        if instance.status == 'waiting' and instance.current_stage_id == stage_id:
            instance.status = 'running'
            instance.wait_reason = None
            instance.save(update_fields=['status', 'wait_reason', 'updated_at'])

        WorkflowStageEngine.move_to_next_stage(
            instance, node, triggered_by=triggered_by, actor_id=actor_id
        )

    # ------------------------------------------------------------------ #
    # Transition routing                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def move_to_next_stage(instance, current_node, context=None,
                           triggered_by='system', actor_id=None):
        """
        Evaluate transitions from current_node and dispatch to the next node.

        Priority order:
          1. WorkflowStageTransition rows (typed, prioritised, condition-aware)
          2. Raw WorkflowEdge rows with condition JSON (legacy fallback)
          3. Complete the workflow if no outgoing path found.
        """
        effective_context = dict(instance.context_data)
        if context:
            effective_context.update(context)

        # 1. Try defined WorkflowStageTransition rows
        transitions = WorkflowStageTransition.objects.filter(
            workflow_id=instance.workflow_id,
            from_stage_id=current_node.id,
            is_active=True,
        ).order_by('priority')

        if transitions.exists():
            conditional = WorkflowConditionalLogicEngine.determine_transition_from_conditions(
                workflow_instance=instance,
                stage_execution=instance.stage_executions.filter(stage_id=current_node.id).order_by('-created_at').first(),
                stage_id=current_node.id,
                context=effective_context,
                write_log=True,
            )
            if conditional is not None:
                transition = conditional['transition']
                try:
                    next_node = WorkflowNode.objects.get(id=transition.to_stage_id)
                    WorkflowStageEngine.execute_stage_transition(
                        instance, current_node, next_node,
                        transition_type=transition.transition_type,
                        label=transition.label,
                        triggered_by=triggered_by,
                        actor_id=actor_id,
                        reason=conditional['reason'],
                        condition_result={
                            'condition_group_id': str(conditional['group'].id),
                            'group_result': conditional['evaluation']['group_result'],
                            'rule_results': conditional['evaluation']['rule_results'],
                        },
                    )
                    return
                except WorkflowNode.DoesNotExist:
                    logger.error(
                        "move_to_next_stage: condition transition target %s not found (group %s)",
                        transition.to_stage_id,
                        conditional['group'].id,
                    )
            for transition in transitions:
                is_match, reason, cond_result = ConditionEvaluator.evaluate(
                    transition.condition_config, effective_context
                )
                if is_match:
                    try:
                        next_node = WorkflowNode.objects.get(id=transition.to_stage_id)
                        WorkflowStageEngine.execute_stage_transition(
                            instance, current_node, next_node,
                            transition_type=transition.transition_type,
                            label=transition.label,
                            triggered_by=triggered_by,
                            actor_id=actor_id,
                            reason=reason,
                            condition_result=cond_result,
                        )
                        return
                    except WorkflowNode.DoesNotExist:
                        logger.error(
                            "move_to_next_stage: to_stage_id %s not found (transition %s)",
                            transition.to_stage_id, transition.id,
                        )
                        continue
            # All transitions evaluated but none matched → fall through to complete
            _timeline(instance, "No matching transition found; completing workflow",
                      stage_id=current_node.id, actor=triggered_by)
            WorkflowStageEngine._complete_workflow(instance, current_node, triggered_by)
            return

        # 2. Fall back to raw edges
        edges = current_node.outgoing_edges.select_related('target_node').all()
        for edge in edges:
            is_match, reason, cond_result = ConditionEvaluator.evaluate(
                edge.condition or {}, effective_context
            )
            if is_match:
                WorkflowStageEngine.execute_stage_transition(
                    instance, current_node, edge.target_node,
                    transition_type='auto',
                    triggered_by=triggered_by,
                    actor_id=actor_id,
                    reason=reason,
                    condition_result=cond_result,
                )
                return

        # 3. No path — complete
        WorkflowStageEngine._complete_workflow(instance, current_node, triggered_by)

    @staticmethod
    def execute_stage_transition(instance, from_node, to_node,
                                 transition_type='auto', label='',
                                 triggered_by='system', actor_id=None,
                                 reason='', condition_result=None):
        """
        Log the transition and dispatch based on to_node type.
        """
        _transition_log(
            instance, from_node, to_node,
            transition_type=transition_type, label=label,
            triggered_by=triggered_by, actor_id=actor_id,
            reason=reason, condition_result=condition_result,
        )

        if to_node.node_type == 'end':
            WorkflowStageEngine._complete_workflow(instance, to_node, triggered_by)
        elif to_node.node_type in WAIT_NODE_TYPES:
            WorkflowStageEngine.handle_wait_state(
                instance, to_node, triggered_by=triggered_by
            )
        else:
            WorkflowStageEngine.complete_stage(
                instance, to_node,
                triggered_by=triggered_by, actor_id=actor_id,
            )

    @staticmethod
    def evaluate_transition_conditions(condition_config, context):
        """
        Public wrapper around ConditionEvaluator.evaluate.
        Returns (is_match, reason, trace).
        """
        return ConditionEvaluator.evaluate(condition_config, context)

    # ------------------------------------------------------------------ #
    # Wait state management                                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def handle_wait_state(instance, node, triggered_by='system'):
        """
        Create a WorkflowWaitState, put stage execution in 'waiting',
        and pause the instance.
        """
        wait_type   = NODE_TYPE_TO_WAIT_TYPE.get(node.node_type, 'manual')
        wait_reason = WAIT_TYPE_TO_WAIT_REASON.get(wait_type, 'waiting_other')
        node_config = node.config or {}
        resume_event = node_config.get('resume_event', '')

        # Stage execution record
        stage_exec = WorkflowStageExecution.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_id=node.id,
            stage_name=node.node_type,
            status='waiting',
            wait_reason=wait_reason,
            actor_type=triggered_by,
        )
        from apps.workflow_execution.services.workflow_sla_engine import WorkflowSLAEngine
        WorkflowSLAEngine.initialize_sla(instance, stage_exec)

        # Explicit wait state record
        wait_state = WorkflowInstanceTracker.create_wait_state(
            instance=instance,
            stage_execution=stage_exec,
            wait_type=wait_type,
            wait_reason=node_config.get('wait_reason', wait_type.replace('_', ' ').title()),
            timeout_at=node_config.get('timeout_at'),
            metadata={'resume_event': resume_event},
        )
        wait_state.resume_event = resume_event
        wait_state.save(update_fields=['resume_event', 'updated_at'])

        # Pause instance
        instance.current_stage_id = node.id
        instance.status = 'waiting'
        instance.wait_reason = wait_reason
        instance.save(update_fields=['current_stage_id', 'status', 'wait_reason', 'updated_at'])

        _timeline(
            instance,
            f"Workflow paused at {node.node_type} stage",
            stage_id=node.id,
            actor=triggered_by,
            metadata={'wait_type': wait_type, 'wait_reason': wait_reason,
                      'wait_state_id': str(wait_state.id)},
        )
        return wait_state

    @staticmethod
    def resume_wait_state(wait_state_id, triggered_by='system', actor_id=None, context=None):
        """
        Resume a specific WorkflowWaitState and continue executing the workflow.
        """
        try:
            wait_state = WorkflowWaitState.objects.select_related(
                'workflow_instance', 'stage_execution'
            ).get(id=wait_state_id)
        except WorkflowWaitState.DoesNotExist:
            logger.error("resume_wait_state: wait state %s not found", wait_state_id)
            return None

        if wait_state.status != 'waiting':
            logger.warning(
                "resume_wait_state: state %s already %s", wait_state_id, wait_state.status
            )
            return wait_state

        # Mark wait state as resumed
        wait_state.do_resume(triggered_by=triggered_by, context=context)
        WorkflowInstanceTracker.resume_wait_state(
            wait_state,
            actor_type=triggered_by,
            actor_id=actor_id,
            metadata=context or {},
        )

        instance = wait_state.workflow_instance

        # Complete the stage execution
        if wait_state.stage_execution:
            se = wait_state.stage_execution
            se.status = 'completed'
            se.completed_at = timezone.now()
            se.save(update_fields=['status', 'completed_at', 'updated_at'])
            from apps.workflow_execution.services.workflow_sla_engine import WorkflowSLAEngine
            WorkflowSLAEngine.resolve_sla(instance, se)

        # Resume instance
        instance.status = 'running'
        instance.wait_reason = None
        instance.save(update_fields=['status', 'wait_reason', 'updated_at'])

        _timeline(
            instance, "Workflow resumed",
            stage_id=instance.current_stage_id,
            actor=triggered_by,
            metadata={'wait_state_id': str(wait_state.id), 'triggered_by': triggered_by},
        )

        # Move to next stage from the wait node
        try:
            node = WorkflowNode.objects.get(id=instance.current_stage_id)
            WorkflowStageEngine.move_to_next_stage(
                instance, node,
                context=context,
                triggered_by=triggered_by,
                actor_id=actor_id,
            )
        except WorkflowNode.DoesNotExist:
            WorkflowStageEngine.fail_stage(
                instance, reason="Resume node not found", triggered_by=triggered_by
            )

        return wait_state

    @staticmethod
    def resume_instance(instance_id, triggered_by='system', actor_id=None, context=None):
        """
        Resume the most recent waiting wait_state for an instance.
        Convenience wrapper used by the API and event listener.
        """
        try:
            instance = WorkflowInstance.objects.get(id=instance_id)
        except WorkflowInstance.DoesNotExist:
            return None

        if instance.status != 'waiting':
            return instance

        wait_state = instance.wait_states.filter(status='waiting').order_by('-created_at').first()
        if wait_state:
            WorkflowStageEngine.resume_wait_state(
                wait_state.id,
                triggered_by=triggered_by,
                actor_id=actor_id,
                context=context,
            )
        else:
            # No explicit wait_state — use simple node resume
            instance.status = 'running'
            instance.wait_reason = None
            instance.save(update_fields=['status', 'wait_reason', 'updated_at'])
            _timeline(instance, "Workflow resumed (no wait_state found)",
                      stage_id=instance.current_stage_id, actor=triggered_by)
            try:
                node = WorkflowNode.objects.get(id=instance.current_stage_id)
                WorkflowStageEngine.move_to_next_stage(
                    instance, node, context=context, triggered_by=triggered_by
                )
            except WorkflowNode.DoesNotExist:
                WorkflowStageEngine.fail_stage(instance, reason="Resume node not found")

        instance.refresh_from_db()
        return instance

    @staticmethod
    def resume_by_event(event_key, tenant_id, entity_type=None, entity_id=None, context=None):
        """
        Find all waiting instances whose active wait_state.resume_event matches event_key
        OR whose wait_reason maps to an event that matches event_key (via WAIT_REASON_RESUME_EVENTS).
        Resume them all.
        """
        # Build matching wait_reasons from constants
        matching_reasons = [
            reason for reason, events in WAIT_REASON_RESUME_EVENTS.items()
            if event_key in events
        ]

        # Find open wait states matching by resume_event field directly
        qs = WorkflowWaitState.objects.select_related('workflow_instance').filter(
            workflow_instance__tenant_id=tenant_id,
            status='waiting',
        )
        if entity_type:
            qs = qs.filter(workflow_instance__entity_type=entity_type)
        if entity_id:
            qs = qs.filter(workflow_instance__entity_id=entity_id)

        # Match either explicit resume_event or via wait_reason mapping
        from django.db.models import Q
        qs = qs.filter(
            Q(resume_event=event_key) |
            Q(workflow_instance__wait_reason__in=matching_reasons)
        )

        resumed = []
        for wait_state in qs.distinct():
            try:
                WorkflowStageEngine.resume_wait_state(
                    wait_state.id, triggered_by='event', context=context
                )
                resumed.append(wait_state.workflow_instance_id)
                logger.info(
                    "Resumed instance %s via event '%s'",
                    wait_state.workflow_instance_id, event_key,
                )
            except Exception:
                logger.exception(
                    "Failed to resume wait_state %s via event '%s'",
                    wait_state.id, event_key,
                )

        return resumed

    # ------------------------------------------------------------------ #
    # Internal helpers                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _complete_workflow(instance, node=None, triggered_by='system'):
        instance.status = 'completed'
        instance.completed_at = timezone.now()
        instance.failed_at = None
        instance.wait_reason = None
        instance.save(update_fields=['status', 'completed_at', 'failed_at', 'wait_reason', 'updated_at'])

        _timeline(instance, "Workflow completed successfully",
                  stage_id=node.id if node else None, actor=triggered_by)
        from apps.workflow_execution.services.workflow_notification_engine import WorkflowNotificationEngine
        stage_execution = None
        if node:
            stage_execution = instance.stage_executions.filter(stage_id=node.id).order_by('-created_at').first()
        WorkflowNotificationEngine.trigger_notifications(
            workflow_instance=instance,
            trigger_type='workflow_completed',
            stage_execution=stage_execution,
            payload={'triggered_by': triggered_by},
        )
