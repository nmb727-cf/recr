from apps.prequalification.models import (
    PrequalForm, PrequalSection, PrequalQuestion, PrequalRule, PrequalResponse,
)


class PrequalFormService:

    @staticmethod
    def list_for_tenant(tenant_id):
        return PrequalForm.objects.filter(
            tenant_id=tenant_id,
            is_deleted=False,
        )

    @staticmethod
    def get(pk, tenant_id):
        return PrequalForm.objects.filter(
            id=pk,
            tenant_id=tenant_id,
            is_deleted=False,
        ).first()

    @staticmethod
    def create(tenant_id, created_by, name, description='', metadata=None):
        return PrequalForm.objects.create(
            tenant_id=tenant_id,
            created_by=created_by,
            name=name,
            description=description,
            metadata=metadata or {},
        )


class PrequalSectionService:

    @staticmethod
    def list_for_form(form_id):
        return PrequalSection.objects.filter(form_id=form_id).order_by('order')

    @staticmethod
    def create(tenant_id, created_by, form_id, title, description='', order=0, metadata=None):
        return PrequalSection.objects.create(
            tenant_id=tenant_id,
            created_by=created_by,
            form_id=form_id,
            title=title,
            description=description,
            order=order,
            metadata=metadata or {},
        )


class PrequalQuestionService:

    @staticmethod
    def list_for_section(section_id):
        return PrequalQuestion.objects.filter(
            section_id=section_id,
        ).order_by('order')

    @staticmethod
    def create(tenant_id, created_by, section_id, question_text, question_type='yes_no',
               required=True, order=0, help_text='', options_json=None,
               score_weight=0, is_knockout=False, metadata=None):
        return PrequalQuestion.objects.create(
            tenant_id=tenant_id,
            created_by=created_by,
            section_id=section_id,
            question_text=question_text,
            question_type=question_type,
            required=required,
            order=order,
            help_text=help_text,
            options_json=options_json or [],
            score_weight=score_weight,
            is_knockout=is_knockout,
            metadata=metadata or {},
        )


class PrequalRuleService:

    @staticmethod
    def list_for_question(question_id):
        return PrequalRule.objects.filter(question_id=question_id)

    @staticmethod
    def create(tenant_id, created_by, question_id, condition_type, compare_value,
               action_type, outcome_code='', target_question_id=None,
               target_section_id=None, metadata=None):
        return PrequalRule.objects.create(
            tenant_id=tenant_id,
            created_by=created_by,
            question_id=question_id,
            condition_type=condition_type,
            compare_value=compare_value,
            action_type=action_type,
            outcome_code=outcome_code,
            target_question_id=target_question_id,
            target_section_id=target_section_id,
            metadata=metadata or {},
        )

    @staticmethod
    def evaluate(rule, answer_text):
        """
        Returns True if the candidate's answer triggers this rule's action.
        Used for knockout / routing evaluation.
        """
        val = str(answer_text).strip().lower()
        compare = str(rule.compare_value).strip().lower()

        if rule.condition_type == 'equals':
            return val == compare
        elif rule.condition_type == 'not_equals':
            return val != compare
        elif rule.condition_type == 'contains':
            return compare in val
        elif rule.condition_type == 'greater_than':
            try:
                return float(val) > float(compare)
            except ValueError:
                return False
        elif rule.condition_type == 'less_than':
            try:
                return float(val) < float(compare)
            except ValueError:
                return False
        elif rule.condition_type == 'in':
            allowed = [v.strip().lower() for v in compare.split(',')]
            return val in allowed
        elif rule.condition_type == 'not_in':
            excluded = [v.strip().lower() for v in compare.split(',')]
            return val not in excluded
        elif rule.condition_type == 'is_empty':
            return not val
        elif rule.condition_type == 'is_not_empty':
            return bool(val)
        return False
