from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from apps.automation.models import AutomationRule, AutomationLog
from apps.interviews.models import Interview, InterviewPanelist
from apps.pipeline.models import Application, ApplicationStageHistory, ActionDeadline


class AutomationEngine:
    ACTION_ALIASES = {
        'schedule_next_interview': 'schedule_next_interview',
        'schedule_interview': 'schedule_next_interview',
        'send_email': 'send_email',
        'send_notification': 'send_notification',
        'assign_interviewer': 'assign_interviewer',
        'create_task': 'create_task',
        'move_stage': 'move_stage',
        'reject_candidate': 'reject_candidate',
        'shortlist_candidate': 'shortlist_candidate',
    }

    @classmethod
    def execute_trigger(
        cls,
        *,
        trigger_event: str,
        tenant_id,
        context: dict | None = None,
        actor_user_id=None,
        entity_type: str = '',
        entity_id=None,
    ) -> dict:
        context = context or {}
        rules = AutomationRule.objects.filter(
            tenant_id=tenant_id,
            trigger_event=trigger_event,
            is_active=True,
            is_deleted=False,
        ).order_by('created_at')

        matched = 0
        executed = 0
        skipped = 0

        for rule in rules:
            if not cls._conditions_match(rule.conditions or {}, context):
                skipped += 1
                cls._log(rule=rule, trigger_event=trigger_event, entity_type=entity_type, entity_id=entity_id, status='skipped', actions_taken=[], error_message='Conditions did not match')
                continue

            matched += 1
            taken = []
            status = 'success'
            err = ''
            try:
                for action in rule.actions or []:
                    result = cls._execute_action(
                        action=action,
                        context=context,
                        tenant_id=tenant_id,
                        actor_user_id=actor_user_id,
                        rule_id=rule.id,
                    )
                    taken.append(result)
                executed += 1
                rule.execution_count = (rule.execution_count or 0) + 1
                rule.last_executed_at = timezone.now()
                rule.save(update_fields=['execution_count', 'last_executed_at', 'updated_at'])
            except Exception as exc:
                status = 'failed'
                err = str(exc)
            cls._log(
                rule=rule,
                trigger_event=trigger_event,
                entity_type=entity_type,
                entity_id=entity_id,
                status=status,
                actions_taken=taken,
                error_message=err,
            )

        return {
            'trigger_event': trigger_event,
            'total_rules': rules.count(),
            'matched_rules': matched,
            'executed_rules': executed,
            'skipped_rules': skipped,
        }

    @classmethod
    def _log(cls, *, rule, trigger_event, entity_type, entity_id, status, actions_taken, error_message):
        AutomationLog.objects.create(
            tenant_id=rule.tenant_id,
            created_by=rule.created_by,
            rule_id=rule.id,
            trigger_event=trigger_event,
            entity_type=entity_type or '',
            entity_id=entity_id,
            status=status,
            actions_taken=actions_taken or [],
            error_message=error_message or '',
        )

    @classmethod
    def _value(cls, data: dict, field: str, default=None):
        if field in data:
            return data[field]
        cur = data
        for part in field.split('.'):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    @classmethod
    def _to_decimal(cls, val):
        try:
            return Decimal(str(val))
        except (InvalidOperation, TypeError, ValueError):
            return None

    @classmethod
    def _evaluate_single(cls, condition: dict, context: dict) -> bool:
        field = str(condition.get('field', '')).strip()
        op = str(condition.get('operator', 'eq')).strip().lower()
        expected = condition.get('value')
        actual = cls._value(context, field)

        if op in {'eq', 'equals'}:
            return actual == expected
        if op in {'ne', 'neq', 'not_equals'}:
            return actual != expected
        if op in {'gt', 'greater_than'}:
            a, b = cls._to_decimal(actual), cls._to_decimal(expected)
            return a is not None and b is not None and a > b
        if op in {'gte', 'greater_than_or_equal'}:
            a, b = cls._to_decimal(actual), cls._to_decimal(expected)
            return a is not None and b is not None and a >= b
        if op in {'lt', 'less_than'}:
            a, b = cls._to_decimal(actual), cls._to_decimal(expected)
            return a is not None and b is not None and a < b
        if op in {'lte', 'less_than_or_equal'}:
            a, b = cls._to_decimal(actual), cls._to_decimal(expected)
            return a is not None and b is not None and a <= b
        if op == 'contains':
            if isinstance(actual, (list, tuple, set)):
                return expected in actual
            return str(expected) in str(actual or '')
        if op == 'in':
            if not isinstance(expected, (list, tuple, set)):
                return False
            return actual in expected
        if op == 'is_true':
            return bool(actual) is True
        if op == 'is_false':
            return bool(actual) is False
        return False

    @classmethod
    def _legacy_condition_match(cls, conditions: dict, context: dict) -> bool:
        if not conditions:
            return True
        for key, expected in conditions.items():
            if key.endswith('__gte'):
                if cls._to_decimal(cls._value(context, key[:-5])) is None:
                    return False
                if cls._to_decimal(cls._value(context, key[:-5])) < cls._to_decimal(expected):
                    return False
            elif key.endswith('__lte'):
                if cls._to_decimal(cls._value(context, key[:-5])) is None:
                    return False
                if cls._to_decimal(cls._value(context, key[:-5])) > cls._to_decimal(expected):
                    return False
            elif key.endswith('__gt'):
                if cls._to_decimal(cls._value(context, key[:-4])) is None:
                    return False
                if cls._to_decimal(cls._value(context, key[:-4])) <= cls._to_decimal(expected):
                    return False
            elif key.endswith('__lt'):
                if cls._to_decimal(cls._value(context, key[:-4])) is None:
                    return False
                if cls._to_decimal(cls._value(context, key[:-4])) >= cls._to_decimal(expected):
                    return False
            else:
                if cls._value(context, key) != expected:
                    return False
        return True

    @classmethod
    def _conditions_match(cls, conditions: dict, context: dict) -> bool:
        if not conditions:
            return True
        all_conditions = conditions.get('all')
        any_conditions = conditions.get('any')
        if isinstance(all_conditions, list):
            if not all(cls._evaluate_single(c, context) for c in all_conditions):
                return False
        if isinstance(any_conditions, list) and any_conditions:
            if not any(cls._evaluate_single(c, context) for c in any_conditions):
                return False
        if isinstance(all_conditions, list) or isinstance(any_conditions, list):
            return True
        return cls._legacy_condition_match(conditions, context)

    @classmethod
    def _application_from_context(cls, context: dict):
        app_id = context.get('application_id')
        if not app_id:
            return None
        return Application.objects.filter(id=app_id, is_deleted=False).first()

    @classmethod
    def _move_application_status(cls, *, application: Application, to_status: str, reason: str, actor_user_id, rule_id):
        from_status = application.status
        application.status = to_status
        application.save(update_fields=['status', 'updated_at'])
        ApplicationStageHistory.objects.create(
            tenant_id=application.tenant_id,
            application_id=application.id,
            from_status=from_status,
            to_status=to_status,
            moved_by=actor_user_id,
            reason=reason,
            notes='Automation rule execution',
            metadata={'automation_rule_id': str(rule_id), 'actor_mode': 'system_automation'},
        )

    @classmethod
    def _execute_action(cls, *, action: dict, context: dict, tenant_id, actor_user_id, rule_id):
        action_type = cls.ACTION_ALIASES.get(str(action.get('type', '')).strip(), str(action.get('type', '')).strip())
        if not action_type:
            raise ValueError("Action type is required.")

        if action_type == 'send_email':
            return {'type': action_type, 'status': 'queued', 'template': action.get('template', '')}

        if action_type == 'send_notification':
            return {'type': action_type, 'status': 'queued', 'channel': action.get('channel', 'in_app')}

        if action_type == 'assign_interviewer':
            interview_id = action.get('interview_id') or context.get('interview_id')
            interviewer_id = action.get('interviewer_id')
            if not interview_id or not interviewer_id:
                return {'type': action_type, 'status': 'skipped', 'reason': 'interview_id or interviewer_id missing'}
            panelist, _ = InterviewPanelist.objects.get_or_create(
                interview_id=interview_id,
                interviewer_id=interviewer_id,
                defaults={
                    'tenant_id': tenant_id,
                    'role': action.get('role', 'panelist'),
                },
            )
            return {'type': action_type, 'status': 'executed', 'panelist_id': str(panelist.id)}

        if action_type == 'create_task':
            entity_type = action.get('entity_type') or context.get('entity_type') or 'interview'
            entity_id = action.get('entity_id') or context.get('interview_id') or context.get('application_id')
            if not entity_id:
                return {'type': action_type, 'status': 'skipped', 'reason': 'entity_id missing'}
            deadline_hours = int(action.get('deadline_hours', 24))
            task = ActionDeadline.objects.create(
                tenant_id=tenant_id,
                entity_type='interview' if entity_type not in {'application', 'interview', 'offer', 'requisition'} else entity_type,
                entity_id=entity_id,
                action_required=action.get('title', 'Interview automation follow-up'),
                assigned_to=action.get('assigned_to') or actor_user_id,
                deadline_at=timezone.now() + timedelta(hours=deadline_hours),
                metadata={'automation_rule_id': str(rule_id), 'details': action.get('details', '')},
            )
            return {'type': action_type, 'status': 'executed', 'task_id': str(task.id)}

        if action_type == 'schedule_next_interview':
            candidate_id = action.get('candidate_id') or context.get('candidate_id')
            application_id = action.get('application_id') or context.get('application_id')
            requisition_id = action.get('requisition_id') or context.get('requisition_id')
            if not all([candidate_id, application_id, requisition_id]):
                return {'type': action_type, 'status': 'skipped', 'reason': 'candidate/application/requisition missing'}
            interview = Interview.objects.create(
                tenant_id=tenant_id,
                candidate_id=candidate_id,
                application_id=application_id,
                requisition_id=requisition_id,
                created_by=actor_user_id,
                interview_type=action.get('interview_type', 'recruiter_screening'),
                interview_round=int(context.get('interview_round', 1) or 1) + 1,
                title=action.get('title', 'Auto Scheduled Next Round'),
                scheduled_at=timezone.now() + timedelta(days=int(action.get('offset_days', 2))),
                status='scheduled',
                metadata={'scheduled_by': 'automation', 'automation_rule_id': str(rule_id)},
            )
            return {'type': action_type, 'status': 'executed', 'interview_id': str(interview.id)}

        if action_type in {'move_stage', 'reject_candidate', 'shortlist_candidate'}:
            application = cls._application_from_context(context)
            if not application:
                return {'type': action_type, 'status': 'skipped', 'reason': 'application not found'}
            target = action.get('stage') if action_type == 'move_stage' else ('rejected' if action_type == 'reject_candidate' else 'shortlisted')
            cls._move_application_status(
                application=application,
                to_status=target,
                reason='automation_rule',
                actor_user_id=actor_user_id,
                rule_id=rule_id,
            )
            return {'type': action_type, 'status': 'executed', 'application_id': str(application.id), 'to_status': target}

        raise ValueError(f"Unsupported action type: {action_type}")

