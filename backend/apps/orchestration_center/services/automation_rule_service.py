from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.orchestration_center.constants.execution_statuses import (
    ApprovalMode,
    ApprovalStatus,
    AutomationExecutionStatus,
    AutomationRuleStatus,
    ScheduledActionStatus,
)
from apps.orchestration_center.models import (
    ApprovalQueueItem,
    AutomationExecutionRun,
    AutomationRule,
    AutomationRuleAction,
    AutomationRuleCondition,
    AutomationRuleScope,
    AutomationScheduledAction,
    ExecutionFailure,
)
from apps.orchestration_center.services.automation_action_executor import AutomationActionExecutor
from apps.orchestration_center.services.ai_execution_service import AIExecutionService
from apps.orchestration_center.services.audit_service import AuditService
from shared.owner_contracts import OwnerContractError


class AutomationRuleService:
    @staticmethod
    def matching_rules(tenant_id, event_name):
        return AutomationRule.objects.filter(
            tenant_id__in=[tenant_id, None],
            trigger_event=event_name,
            status=AutomationRuleStatus.ACTIVE,
            is_deleted=False,
        ).order_by('priority_order')

    @staticmethod
    @transaction.atomic
    def create_run(*, tenant_id, created_by, rule, source_event, source_module, source_entity_type, source_entity_id, payload=None, mode=None, dedupe_key=''):
        if dedupe_key:
            existing_run = AutomationExecutionRun.objects.filter(dedupe_key=dedupe_key).first()
            if existing_run:
                return existing_run, False
        try:
            with transaction.atomic():
                run = AutomationExecutionRun.objects.create(
                    tenant_id=tenant_id,
                    created_by=created_by,
                    rule=rule,
                    source_event=source_event,
                    source_module=source_module,
                    source_entity_type=source_entity_type,
                    source_entity_id=str(source_entity_id),
                    trigger_payload_json=AIExecutionService._sanitize_json(payload or {}),
                    mode=mode or rule.mode,
                    status=AutomationExecutionStatus.QUEUED,
                    dedupe_key=dedupe_key or '',
                )
                created = True
        except IntegrityError:
            if not dedupe_key:
                raise
            run = AutomationExecutionRun.objects.get(dedupe_key=dedupe_key)
            created = False

        if created:
            AuditService.log(
                tenant_id=tenant_id,
                actor_id=created_by,
                actor_type='system',
                action_type='automation_run.created',
                target_type='automation_execution_run',
                target_id=run.id,
                after_state_json={'status': run.status, 'rule_id': str(rule.id)},
            )
        return run, created

    @staticmethod
    @transaction.atomic
    def create_rule(*, tenant_id, created_by, rule_data):
        conditions = rule_data.pop('conditions', [])
        actions = rule_data.pop('actions', [])
        scopes = rule_data.pop('scopes', [])
        rule = AutomationRule.objects.create(tenant_id=tenant_id, created_by=created_by, **rule_data)
        AutomationRuleService._replace_children(rule, tenant_id, created_by, conditions, actions, scopes)
        return rule

    @staticmethod
    @transaction.atomic
    def update_rule(*, rule, rule_data):
        conditions = rule_data.pop('conditions', None)
        actions = rule_data.pop('actions', None)
        scopes = rule_data.pop('scopes', None)
        for field, value in rule_data.items():
            setattr(rule, field, value)
        rule.save()
        if conditions is not None or actions is not None or scopes is not None:
            AutomationRuleService._replace_children(
                rule,
                rule.tenant_id,
                rule.created_by,
                conditions if conditions is not None else [AutomationRuleService._condition_to_dict(item) for item in rule.conditions.all()],
                actions if actions is not None else [AutomationRuleService._action_to_dict(item) for item in rule.actions.all()],
                scopes if scopes is not None else [AutomationRuleService._scope_to_dict(item) for item in rule.scopes.all()],
            )
        return rule

    @staticmethod
    def toggle_rule(*, rule, new_status):
        if new_status in {AutomationRuleStatus.ACTIVE, AutomationRuleStatus.TESTING} and not rule.actions.exists():
            raise ValueError('Automation rule must have at least one action before activation.')
        if rule.status == AutomationRuleStatus.ARCHIVED:
            raise ValueError('Archived automation rules cannot be reactivated.')
        rule.status = new_status
        rule.save(update_fields=['status', 'updated_at'])
        return rule

    @staticmethod
    def simulate_rule(*, rule, event_payload_json=None):
        return {
            'rule_id': str(rule.id),
            'trigger_event': rule.trigger_event,
            'mode': rule.mode,
            'simulation': True,
            'event_payload_json': event_payload_json or {},
            'conditions_loaded': rule.conditions.count(),
            'actions_loaded': rule.actions.count(),
            'scope_count': rule.scopes.count(),
        }

    @staticmethod
    @transaction.atomic
    def execute_run_by_id(*, automation_run_id):
        run = AutomationExecutionRun.objects.select_related('rule').prefetch_related('rule__conditions', 'rule__actions').get(pk=automation_run_id)
        if run.status not in {AutomationExecutionStatus.QUEUED, AutomationExecutionStatus.SCHEDULED, AutomationExecutionStatus.FAILED, AutomationExecutionStatus.PARTIAL}:
            return run

        run.status = AutomationExecutionStatus.RUNNING
        run.started_at = timezone.now()
        run.save(update_fields=['status', 'started_at', 'updated_at'])
        AuditService.log(
            tenant_id=run.tenant_id,
            actor_id=run.created_by,
            actor_type='system',
            action_type='automation_run.running',
            target_type='automation_execution_run',
            target_id=run.id,
            after_state_json={'status': run.status},
        )

        conditions_result = AutomationRuleService.evaluate_conditions(
            rule=run.rule,
            payload=run.trigger_payload_json or {},
        )
        run.evaluated_conditions_json = conditions_result
        if not all(item['matched'] for item in conditions_result):
            run.status = AutomationExecutionStatus.COMPLETED
            run.completed_at = timezone.now()
            run.action_results_json = [{'status': 'skipped', 'reason': 'conditions_not_met'}]
            run.save(update_fields=['evaluated_conditions_json', 'action_results_json', 'status', 'completed_at', 'updated_at'])
            return run

        action_results = []
        requires_review = run.mode == ApprovalMode.APPROVAL_REQUIRED
        for action in run.rule.actions.all().order_by('sequence_order'):
            if action.requires_approval:
                requires_review = True
            if action.delay_seconds > 0:
                scheduled = AutomationScheduledAction.objects.create(
                    tenant_id=run.tenant_id,
                    created_by=run.created_by,
                    run=run,
                    action_type=action.action_type,
                    status=ScheduledActionStatus.PENDING,
                    execute_at=timezone.now() + timezone.timedelta(seconds=action.delay_seconds),
                    payload_json=action.action_config_json,
                )
                action_results.append(
                    {
                        'action_type': action.action_type,
                        'status': 'scheduled',
                        'scheduled_action_id': str(scheduled.id),
                    }
                )
                continue
            try:
                action_results.append(
                    AutomationRuleService._apply_action(
                        run=run,
                        action=action,
                    )
                )
            except OwnerContractError as exc:
                action_results.append(
                    {
                        'action_type': action.action_type,
                        'status': 'failed',
                        'error': str(exc),
                        'error_category': exc.error_category,
                        'retry_safe': exc.retry_safe,
                    }
                )
            except Exception as exc:
                action_results.append(
                    {
                        'action_type': action.action_type,
                        'status': 'failed',
                        'error': str(exc),
                        'error_category': 'unhandled_runtime_error',
                        'retry_safe': True,
                    }
                )

        if requires_review:
            ApprovalQueueItem.objects.get_or_create(
                tenant_id=run.tenant_id,
                origin_type='automation_run',
                origin_id=run.id,
                requested_action='apply_automation_actions',
                defaults={
                    'created_by': run.created_by,
                    'item_type': 'automation_action',
                    'summary_payload_json': {'actions': action_results},
                    'recommended_decision': 'approve',
                    'approver_role': 'tenant_admin',
                    'status': ApprovalStatus.PENDING,
                },
            )
            run.status = AutomationExecutionStatus.REQUIRES_REVIEW
        elif any(item.get('status') == 'scheduled' for item in action_results):
            run.status = AutomationExecutionStatus.SCHEDULED
            run.scheduled_for = min(item.execute_at for item in run.scheduled_actions.all()) if run.scheduled_actions.exists() else None
        elif any(item.get('status') == 'failed' for item in action_results):
            run.status = AutomationExecutionStatus.PARTIAL
        else:
            run.status = AutomationExecutionStatus.COMPLETED

        run.completed_at = timezone.now() if run.status in {AutomationExecutionStatus.COMPLETED, AutomationExecutionStatus.PARTIAL} else None
        run.action_results_json = action_results
        run.failure_category = ''
        run.failure_reason = ''
        run.save(
            update_fields=[
                'evaluated_conditions_json',
                'action_results_json',
                'status',
                'scheduled_for',
                'completed_at',
                'failure_category',
                'failure_reason',
                'updated_at',
            ]
        )
        AuditService.log(
            tenant_id=run.tenant_id,
            actor_id=run.created_by,
            actor_type='system',
            action_type='automation_run.completed',
            target_type='automation_execution_run',
            target_id=run.id,
            after_state_json={'status': run.status},
        )
        return run

    @staticmethod
    def queue_for_retry(*, run):
        if run.status == AutomationExecutionStatus.CANCELLED:
            raise ValueError('Cancelled automation runs cannot be retried.')
        run.retry_count += 1
        run.status = AutomationExecutionStatus.QUEUED
        run.completed_at = None
        run.failure_category = ''
        run.failure_reason = ''
        run.save(update_fields=['retry_count', 'status', 'completed_at', 'failure_category', 'failure_reason', 'updated_at'])
        AuditService.log(
            tenant_id=run.tenant_id,
            actor_id=run.created_by,
            actor_type='system',
            action_type='automation_run.retry_scheduled',
            target_type='automation_execution_run',
            target_id=run.id,
            after_state_json={'status': run.status, 'retry_count': run.retry_count},
        )
        return run

    @staticmethod
    def process_due_scheduled_actions():
        due_actions = AutomationScheduledAction.objects.filter(
            status=ScheduledActionStatus.PENDING,
            execute_at__lte=timezone.now(),
        ).select_related('run', 'run__rule')
        completed_ids = []
        for action in due_actions:
            try:
                result = AutomationRuleService._apply_scheduled_action(action=action)
                action.status = ScheduledActionStatus.COMPLETED
                action.last_error = ''
                action.attempt_count += 1
                action.save(update_fields=['status', 'last_error', 'attempt_count', 'updated_at'])
                run = action.run
                run.refresh_from_db(fields=['action_results_json', 'status', 'completed_at', 'updated_at'])
                run.action_results_json = [*(run.action_results_json or []), result]
                remaining_pending = run.scheduled_actions.filter(status=ScheduledActionStatus.PENDING).exists()
                any_failed = run.scheduled_actions.filter(status=ScheduledActionStatus.FAILED).exists()
                if remaining_pending:
                    run.status = AutomationExecutionStatus.SCHEDULED
                elif any_failed:
                    run.status = AutomationExecutionStatus.PARTIAL
                    run.completed_at = timezone.now()
                else:
                    run.status = AutomationExecutionStatus.COMPLETED
                    run.completed_at = timezone.now()
                run.save(update_fields=['action_results_json', 'status', 'completed_at', 'updated_at'])
                completed_ids.append(str(action.id))
            except OwnerContractError as exc:
                action.status = ScheduledActionStatus.FAILED
                action.last_error = str(exc)
                action.attempt_count += 1
                action.save(update_fields=['status', 'last_error', 'attempt_count', 'updated_at'])
                run = action.run
                run.refresh_from_db(fields=['action_results_json', 'status', 'completed_at', 'updated_at'])
                run.action_results_json = [
                    *(run.action_results_json or []),
                    {
                        'action_type': action.action_type,
                        'status': 'failed',
                        'error': str(exc),
                        'error_category': exc.error_category,
                        'retry_safe': exc.retry_safe,
                        'scheduled_action_id': str(action.id),
                    },
                ]
                if run.scheduled_actions.filter(status=ScheduledActionStatus.PENDING).exists():
                    run.status = AutomationExecutionStatus.SCHEDULED
                else:
                    run.status = AutomationExecutionStatus.PARTIAL
                    run.completed_at = timezone.now()
                run.save(update_fields=['action_results_json', 'status', 'completed_at', 'updated_at'])
            except Exception as exc:
                action.status = ScheduledActionStatus.FAILED
                action.last_error = str(exc)
                action.attempt_count += 1
                action.save(update_fields=['status', 'last_error', 'attempt_count', 'updated_at'])
                run = action.run
                run.refresh_from_db(fields=['action_results_json', 'status', 'completed_at', 'updated_at'])
                run.action_results_json = [
                    *(run.action_results_json or []),
                    {
                        'action_type': action.action_type,
                        'status': 'failed',
                        'error': str(exc),
                        'error_category': 'unhandled_runtime_error',
                        'retry_safe': True,
                        'scheduled_action_id': str(action.id),
                    },
                ]
                if run.scheduled_actions.filter(status=ScheduledActionStatus.PENDING).exists():
                    run.status = AutomationExecutionStatus.SCHEDULED
                else:
                    run.status = AutomationExecutionStatus.PARTIAL
                    run.completed_at = timezone.now()
                run.save(update_fields=['action_results_json', 'status', 'completed_at', 'updated_at'])
        return completed_ids

    @staticmethod
    def mark_failed(*, run, failure_category, failure_reason, retryable=True):
        run.status = AutomationExecutionStatus.FAILED
        run.completed_at = timezone.now()
        run.failure_category = failure_category
        run.failure_reason = failure_reason
        run.save(update_fields=['status', 'completed_at', 'failure_category', 'failure_reason', 'updated_at'])
        ExecutionFailure.objects.create(
            tenant_id=run.tenant_id,
            created_by=run.created_by,
            failure_type='automation_run',
            related_run_id=run.id,
            category=failure_category,
            retryable=retryable,
            max_retries=2,
            last_error_message=failure_reason,
        )
        AuditService.log(
            tenant_id=run.tenant_id,
            actor_id=run.created_by,
            actor_type='system',
            action_type='automation_run.failed',
            target_type='automation_execution_run',
            target_id=run.id,
            after_state_json={'status': run.status, 'failure_category': failure_category},
        )
        return run

    @staticmethod
    def evaluate_conditions(*, rule, payload):
        results = []
        for condition in rule.conditions.all().order_by('condition_group', 'sequence_order'):
            actual_value = AutomationRuleService._resolve_field(payload, condition.field_path)
            matched = AutomationRuleService._compare(actual_value, condition.operator, condition.expected_value_json)
            if condition.is_negated:
                matched = not matched
            results.append(
                {
                    'field_path': condition.field_path,
                    'operator': condition.operator,
                    'actual_value': actual_value,
                    'expected_value': condition.expected_value_json,
                    'matched': matched,
                }
            )
        return results

    @staticmethod
    def _replace_children(rule, tenant_id, created_by, conditions, actions, scopes):
        rule.conditions.all().delete()
        rule.actions.all().delete()
        rule.scopes.all().delete()
        requires_high_risk_approval = False
        for item in conditions:
            AutomationRuleCondition.objects.create(
                tenant_id=tenant_id,
                created_by=created_by,
                rule=rule,
                condition_group=item.get('condition_group', 'default'),
                field_path=item['field_path'],
                operator=item['operator'],
                expected_value_json=item.get('expected_value_json', {}),
                sequence_order=item.get('sequence_order', 1),
                is_negated=item.get('is_negated', False),
            )
        for item in actions:
            if item.get('action_type') in {'move_stage', 'reject_candidate', 'send_rejection_email'}:
                requires_high_risk_approval = True
            AutomationRuleAction.objects.create(
                tenant_id=tenant_id,
                created_by=created_by,
                rule=rule,
                action_type=item['action_type'],
                action_config_json=item.get('action_config_json', {}),
                delay_seconds=item.get('delay_seconds', 0),
                requires_approval=item.get('requires_approval', False),
                sequence_order=item.get('sequence_order', 1),
            )
        for item in scopes:
            AutomationRuleScope.objects.create(
                tenant_id=tenant_id,
                created_by=created_by,
                rule=rule,
                entity_type=item.get('entity_type', ''),
                stage_key=item.get('stage_key', ''),
                role_scope=item.get('role_scope', ''),
                source_scope=item.get('source_scope', ''),
                working_hours_only=item.get('working_hours_only', False),
                is_active=item.get('is_active', True),
            )
        if requires_high_risk_approval:
            rule.mode = ApprovalMode.APPROVAL_REQUIRED
        rule.requires_high_risk_approval = requires_high_risk_approval
        rule.save(update_fields=['mode', 'requires_high_risk_approval', 'updated_at'])

    @staticmethod
    def _apply_action(*, run, action):
        return AutomationActionExecutor.execute(run=run, action=action)

    @staticmethod
    def _apply_scheduled_action(*, action):
        pseudo_action = type(
            'ScheduledActionProxy',
            (),
            {
                'id': action.id,
                'action_type': action.action_type,
                'action_config_json': action.payload_json,
            },
        )
        result = AutomationRuleService._apply_action(run=action.run, action=pseudo_action)
        result.setdefault('scheduled_action_id', str(action.id))
        return result

    @staticmethod
    def _condition_to_dict(item):
        return {
            'condition_group': item.condition_group,
            'field_path': item.field_path,
            'operator': item.operator,
            'expected_value_json': item.expected_value_json,
            'sequence_order': item.sequence_order,
            'is_negated': item.is_negated,
        }

    @staticmethod
    def _action_to_dict(item):
        return {
            'action_type': item.action_type,
            'action_config_json': item.action_config_json,
            'delay_seconds': item.delay_seconds,
            'requires_approval': item.requires_approval,
            'sequence_order': item.sequence_order,
        }

    @staticmethod
    def _scope_to_dict(item):
        return {
            'entity_type': item.entity_type,
            'stage_key': item.stage_key,
            'role_scope': item.role_scope,
            'source_scope': item.source_scope,
            'working_hours_only': item.working_hours_only,
            'is_active': item.is_active,
        }

    @staticmethod
    def _resolve_field(payload, path):
        current = payload
        for part in path.split('.'):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def _compare(actual, operator, expected):
        if operator == 'eq':
            return actual == expected
        if operator == 'ne':
            return actual != expected
        if operator == 'gt':
            return actual is not None and actual > expected
        if operator == 'gte':
            return actual is not None and actual >= expected
        if operator == 'lt':
            return actual is not None and actual < expected
        if operator == 'lte':
            return actual is not None and actual <= expected
        if operator == 'contains':
            return actual is not None and expected in actual
        if operator == 'in':
            return actual in (expected or [])
        if operator == 'exists':
            return actual is not None
        return False
