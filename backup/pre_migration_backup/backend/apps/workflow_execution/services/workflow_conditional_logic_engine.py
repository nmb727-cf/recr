from __future__ import annotations

from typing import Any

from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowActorAssignment,
    WorkflowConditionEvaluationLog,
    WorkflowConditionGroup,
    WorkflowConditionRule,
    WorkflowInstance,
    WorkflowSLATracker,
    WorkflowStageTransition,
    WorkflowWaitState,
)


def _dig(data: dict[str, Any] | None, path: str):
    if not isinstance(data, dict):
        return None
    current: Any = data
    for part in path.split('.'):
        if not isinstance(current, dict):
            return None
        if part not in current:
            return None
        current = current.get(part)
    return current


class WorkflowConditionalLogicEngine:
    @staticmethod
    def resolve_context_value(
        *,
        workflow_instance: WorkflowInstance,
        stage_execution=None,
        condition_type: str,
        field_name: str,
        context: dict[str, Any] | None = None,
    ):
        merged_context = dict(workflow_instance.context_data or {})
        merged_context.update(context or {})

        if condition_type in {'workflow_context', 'custom'}:
            return _dig(merged_context, field_name) if '.' in field_name else merged_context.get(field_name)

        if condition_type == 'entity_field':
            value = _dig(merged_context, field_name)
            if value is not None:
                return value
            entity_obj = merged_context.get(workflow_instance.entity_type, {})
            if isinstance(entity_obj, dict):
                return _dig(entity_obj, field_name) if '.' in field_name else entity_obj.get(field_name)
            return None

        if condition_type == 'actor_field':
            stage_id = stage_execution.stage_id if stage_execution else workflow_instance.current_stage_id
            assignment = WorkflowActorAssignment.objects.filter(
                workflow_instance=workflow_instance,
                stage_id=stage_id,
                status='active',
            ).order_by('-assigned_at').first()
            if not assignment:
                return None
            actor_map = {
                'actor_id': assignment.actor_id,
                'actor_type': assignment.actor_type,
                'assignment_type': assignment.assignment_type,
                'status': assignment.status,
            }
            return _dig(actor_map, field_name) if '.' in field_name else actor_map.get(field_name)

        if condition_type == 'score_field':
            return _dig(merged_context, field_name) if '.' in field_name else merged_context.get(field_name)

        if condition_type == 'status_field':
            if field_name == 'workflow.status':
                return workflow_instance.status
            if field_name == 'stage.status' and stage_execution is not None:
                return stage_execution.status
            if field_name.startswith('sla.'):
                tracker = WorkflowSLATracker.objects.filter(
                    workflow_instance=workflow_instance,
                    stage_execution=stage_execution,
                ).order_by('-created_at').first()
                if tracker:
                    sla_map = {
                        'status': tracker.status,
                        'breached': tracker.status in {'breached', 'escalated'},
                        'warning': tracker.status == 'warning',
                    }
                    key = field_name.split('.', 1)[1]
                    return sla_map.get(key)
            return _dig(merged_context, field_name) if '.' in field_name else merged_context.get(field_name)

        if condition_type == 'time_field':
            now = timezone.now()
            if field_name == 'wait_state.duration':
                wait_state = WorkflowWaitState.objects.filter(
                    workflow_instance=workflow_instance,
                    stage_execution=stage_execution,
                    status='waiting',
                ).order_by('-created_at').first()
                if not wait_state:
                    return None
                return int((now - wait_state.created_at).total_seconds())
            if field_name == 'sla.seconds_to_breach':
                tracker = WorkflowSLATracker.objects.filter(
                    workflow_instance=workflow_instance,
                    stage_execution=stage_execution,
                ).order_by('-created_at').first()
                if not tracker:
                    return None
                return int((tracker.breach_at - now).total_seconds())
            return _dig(merged_context, field_name) if '.' in field_name else merged_context.get(field_name)

        return _dig(merged_context, field_name) if '.' in field_name else merged_context.get(field_name)

    @staticmethod
    def compare_values(*, actual, operator: str, expected):
        if operator == 'equals':
            return actual == expected
        if operator == 'not_equals':
            return actual != expected
        if operator == 'greater_than':
            return (actual is not None and expected is not None) and actual > expected
        if operator == 'less_than':
            return (actual is not None and expected is not None) and actual < expected
        if operator == 'greater_or_equal':
            return (actual is not None and expected is not None) and actual >= expected
        if operator == 'less_or_equal':
            return (actual is not None and expected is not None) and actual <= expected
        if operator == 'contains':
            return str(expected) in str(actual or '')
        if operator == 'not_contains':
            return str(expected) not in str(actual or '')
        if operator == 'in_list':
            hay = expected if isinstance(expected, list) else [expected]
            return actual in hay
        if operator == 'not_in_list':
            hay = expected if isinstance(expected, list) else [expected]
            return actual not in hay
        if operator == 'is_true':
            return bool(actual) is True
        if operator == 'is_false':
            return bool(actual) is False
        if operator == 'exists':
            return actual is not None
        if operator == 'not_exists':
            return actual is None
        return False

    @staticmethod
    def log_condition_result(
        *,
        workflow_instance: WorkflowInstance,
        stage_execution,
        condition_group: WorkflowConditionGroup | None,
        rule: WorkflowConditionRule | None,
        evaluated_value,
        expected_value,
        result: str,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowConditionEvaluationLog:
        return WorkflowConditionEvaluationLog.objects.create(
            tenant_id=workflow_instance.tenant_id,
            workflow_instance=workflow_instance,
            stage_execution=stage_execution,
            condition_group=condition_group,
            rule=rule,
            evaluated_value=evaluated_value,
            expected_value=expected_value,
            result=result,
            reason=reason,
            metadata=metadata or {},
        )

    @staticmethod
    def evaluate_condition_rule(
        *,
        workflow_instance: WorkflowInstance,
        stage_execution,
        rule: WorkflowConditionRule,
        condition_group: WorkflowConditionGroup | None = None,
        context: dict[str, Any] | None = None,
        write_log: bool = True,
    ) -> dict[str, Any]:
        actual = WorkflowConditionalLogicEngine.resolve_context_value(
            workflow_instance=workflow_instance,
            stage_execution=stage_execution,
            condition_type=rule.condition_type,
            field_name=rule.field_name,
            context=context,
        )
        passed = WorkflowConditionalLogicEngine.compare_values(
            actual=actual,
            operator=rule.operator,
            expected=rule.expected_value,
        )
        result = 'passed' if passed else 'failed'
        reason = f"{rule.field_name} {rule.operator} {rule.expected_value!r} -> {actual!r}"
        if write_log:
            WorkflowConditionalLogicEngine.log_condition_result(
                workflow_instance=workflow_instance,
                stage_execution=stage_execution,
                condition_group=condition_group,
                rule=rule,
                evaluated_value=actual,
                expected_value=rule.expected_value,
                result=result,
                reason=reason,
                metadata={'logical_join': rule.logical_join},
            )
        return {
            'rule_id': str(rule.id),
            'result': result,
            'passed': passed,
            'reason': reason,
            'evaluated_value': actual,
            'expected_value': rule.expected_value,
        }

    @staticmethod
    def get_default_transition(
        *,
        workflow_id,
        stage_id,
        group: WorkflowConditionGroup | None = None,
    ):
        if group and group.default_transition_id:
            return WorkflowStageTransition.objects.filter(id=group.default_transition_id).first()
        return WorkflowStageTransition.objects.filter(
            workflow_id=workflow_id,
            from_stage_id=stage_id,
            is_active=True,
        ).order_by('priority').first()

    @staticmethod
    def evaluate_condition_group(
        *,
        workflow_instance: WorkflowInstance,
        stage_execution,
        group: WorkflowConditionGroup,
        context: dict[str, Any] | None = None,
        write_log: bool = True,
    ) -> dict[str, Any]:
        rules = list(
            WorkflowConditionRule.objects.filter(
                workflow_id=group.workflow_id,
                stage_id=group.stage_id,
                rule_group=group.group_name,
                is_active=True,
            ).order_by('priority', 'created_at')
        )
        if not rules:
            if write_log:
                WorkflowConditionalLogicEngine.log_condition_result(
                    workflow_instance=workflow_instance,
                    stage_execution=stage_execution,
                    condition_group=group,
                    rule=None,
                    evaluated_value={},
                    expected_value={},
                    result='skipped',
                    reason='No active rules in condition group.',
                )
            return {
                'group_id': str(group.id),
                'group_result': 'skipped',
                'passed': False,
                'rule_results': [],
                'reason': 'No active rules in group.',
            }

        aggregate = None
        rule_results = []
        for index, rule in enumerate(rules):
            evaluated = WorkflowConditionalLogicEngine.evaluate_condition_rule(
                workflow_instance=workflow_instance,
                stage_execution=stage_execution,
                rule=rule,
                condition_group=group,
                context=context,
                write_log=write_log,
            )
            rule_results.append(evaluated)
            passed = bool(evaluated['passed'])
            if index == 0:
                aggregate = passed
            else:
                if rule.logical_join == 'OR':
                    aggregate = bool(aggregate) or passed
                else:
                    aggregate = bool(aggregate) and passed

        final_passed = bool(aggregate)
        return {
            'group_id': str(group.id),
            'group_result': 'passed' if final_passed else 'failed',
            'passed': final_passed,
            'rule_results': rule_results,
            'reason': f"Condition group {group.group_name} evaluated to {final_passed}",
        }

    @staticmethod
    def determine_transition_from_conditions(
        *,
        workflow_instance: WorkflowInstance,
        stage_execution=None,
        stage_id=None,
        context: dict[str, Any] | None = None,
        write_log: bool = True,
    ) -> dict[str, Any] | None:
        sid = stage_id or (stage_execution.stage_id if stage_execution else workflow_instance.current_stage_id)
        if not sid:
            return None

        group = WorkflowConditionGroup.objects.filter(
            workflow_id=workflow_instance.workflow_id,
            stage_id=sid,
            is_active=True,
        ).order_by('-created_at').first()
        if not group:
            return None

        evaluation = WorkflowConditionalLogicEngine.evaluate_condition_group(
            workflow_instance=workflow_instance,
            stage_execution=stage_execution,
            group=group,
            context=context,
            write_log=write_log,
        )
        transition = None
        if evaluation['passed'] and group.success_transition_id:
            transition = WorkflowStageTransition.objects.filter(id=group.success_transition_id).first()
        elif (not evaluation['passed']) and group.failure_transition_id:
            transition = WorkflowStageTransition.objects.filter(id=group.failure_transition_id).first()
        if transition is None:
            transition = WorkflowConditionalLogicEngine.get_default_transition(
                workflow_id=workflow_instance.workflow_id,
                stage_id=sid,
                group=group,
            )
        if transition is None:
            return None
        return {
            'group': group,
            'evaluation': evaluation,
            'transition': transition,
            'reason': evaluation['reason'],
        }


# Function-style exports required by prompt contract.
evaluate_condition_rule = WorkflowConditionalLogicEngine.evaluate_condition_rule
evaluate_condition_group = WorkflowConditionalLogicEngine.evaluate_condition_group
resolve_context_value = WorkflowConditionalLogicEngine.resolve_context_value
compare_values = WorkflowConditionalLogicEngine.compare_values
determine_transition_from_conditions = WorkflowConditionalLogicEngine.determine_transition_from_conditions
log_condition_result = WorkflowConditionalLogicEngine.log_condition_result
get_default_transition = WorkflowConditionalLogicEngine.get_default_transition
