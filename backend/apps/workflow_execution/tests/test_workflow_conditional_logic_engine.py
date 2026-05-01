import uuid

import pytest

from apps.orchestration_center.models.workflow import Workflow, WorkflowNode
from apps.workflow_execution.models import (
    WorkflowConditionGroup,
    WorkflowConditionRule,
    WorkflowInstance,
    WorkflowStageExecution,
    WorkflowStageTransition,
)
from apps.workflow_execution.services.workflow_conditional_logic_engine import WorkflowConditionalLogicEngine


def make_workflow(tenant_id):
    workflow = Workflow.objects.create(
        tenant_id=tenant_id,
        name='Conditional Logic WF',
        trigger_event='job_created',
        status='active',
        is_active=True,
    )
    stage = WorkflowNode.objects.create(workflow=workflow, node_type='decision')
    next_stage = WorkflowNode.objects.create(workflow=workflow, node_type='action')
    alt_stage = WorkflowNode.objects.create(workflow=workflow, node_type='end')
    default_stage = WorkflowNode.objects.create(workflow=workflow, node_type='hold')
    return workflow, stage, next_stage, alt_stage, default_stage


@pytest.mark.django_db
class TestWorkflowConditionalLogicEngine:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow, self.stage, self.next_stage, self.alt_stage, self.default_stage = make_workflow(self.tenant_id)
        self.instance = WorkflowInstance.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='candidate',
            entity_id=uuid.uuid4(),
            current_stage_id=self.stage.id,
            status='running',
            context_data={},
        )
        self.stage_execution = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_id=self.stage.id,
            stage_name='decision',
            status='running',
        )

    def test_1_candidate_score_ge_80_routes_to_next_interview(self):
        success_transition = WorkflowStageTransition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            from_stage_id=self.stage.id,
            to_stage_id=self.next_stage.id,
            transition_type='decision',
            label='score-pass',
            is_active=True,
        )
        group = WorkflowConditionGroup.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            group_name='score-check',
            success_transition_id=success_transition.id,
            is_active=True,
        )
        WorkflowConditionRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            rule_name='score-threshold',
            rule_group=group.group_name,
            condition_type='workflow_context',
            field_name='candidate.score',
            operator='greater_or_equal',
            expected_value=80,
            logical_join='AND',
            priority=1,
            is_active=True,
        )

        result = WorkflowConditionalLogicEngine.determine_transition_from_conditions(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            context={'candidate': {'score': 82}},
        )

        assert result is not None
        assert result['transition'].id == success_transition.id
        assert result['evaluation']['passed'] is True

    def test_2_offer_amount_above_threshold_selects_approval_path(self):
        approval_transition = WorkflowStageTransition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            from_stage_id=self.stage.id,
            to_stage_id=self.alt_stage.id,
            transition_type='approval',
            label='approval-required',
            is_active=True,
        )
        group = WorkflowConditionGroup.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            group_name='offer-approval',
            success_transition_id=approval_transition.id,
            is_active=True,
        )
        WorkflowConditionRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            rule_name='approval-limit-check',
            rule_group=group.group_name,
            condition_type='workflow_context',
            field_name='offer.amount',
            operator='greater_than',
            expected_value=100000,
            logical_join='AND',
            priority=1,
            is_active=True,
        )

        result = WorkflowConditionalLogicEngine.determine_transition_from_conditions(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            context={'offer': {'amount': 150000}},
        )

        assert result is not None
        assert result['transition'].id == approval_transition.id

    def test_3_source_agency_routes_to_company_review(self):
        company_review_transition = WorkflowStageTransition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            from_stage_id=self.stage.id,
            to_stage_id=self.alt_stage.id,
            transition_type='decision',
            label='agency-route',
            is_active=True,
        )
        group = WorkflowConditionGroup.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            group_name='source-routing',
            success_transition_id=company_review_transition.id,
            is_active=True,
        )
        WorkflowConditionRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            rule_name='source-is-agency',
            rule_group=group.group_name,
            condition_type='workflow_context',
            field_name='candidate.source',
            operator='equals',
            expected_value='agency',
            logical_join='AND',
            priority=1,
            is_active=True,
        )

        result = WorkflowConditionalLogicEngine.determine_transition_from_conditions(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            context={'candidate': {'source': 'agency'}},
        )

        assert result is not None
        assert result['transition'].id == company_review_transition.id

    def test_4_multiple_and_rules_only_pass_when_all_true(self):
        group = WorkflowConditionGroup.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            group_name='and-group',
            is_active=True,
        )
        WorkflowConditionRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            rule_name='score-threshold',
            rule_group=group.group_name,
            condition_type='workflow_context',
            field_name='candidate.score',
            operator='greater_or_equal',
            expected_value=80,
            logical_join='AND',
            priority=1,
            is_active=True,
        )
        WorkflowConditionRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            rule_name='status-screened',
            rule_group=group.group_name,
            condition_type='workflow_context',
            field_name='candidate.status',
            operator='equals',
            expected_value='screened',
            logical_join='AND',
            priority=2,
            is_active=True,
        )

        failed = WorkflowConditionalLogicEngine.evaluate_condition_group(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            group=group,
            context={'candidate': {'score': 85, 'status': 'new'}},
            write_log=False,
        )
        passed = WorkflowConditionalLogicEngine.evaluate_condition_group(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            group=group,
            context={'candidate': {'score': 85, 'status': 'screened'}},
            write_log=False,
        )

        assert failed['passed'] is False
        assert passed['passed'] is True

    def test_5_multiple_or_rules_pass_if_any_true(self):
        group = WorkflowConditionGroup.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            group_name='or-group',
            is_active=True,
        )
        WorkflowConditionRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            rule_name='source-direct',
            rule_group=group.group_name,
            condition_type='workflow_context',
            field_name='candidate.source',
            operator='equals',
            expected_value='direct',
            logical_join='AND',
            priority=1,
            is_active=True,
        )
        WorkflowConditionRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            rule_name='source-agency',
            rule_group=group.group_name,
            condition_type='workflow_context',
            field_name='candidate.source',
            operator='equals',
            expected_value='agency',
            logical_join='OR',
            priority=2,
            is_active=True,
        )

        result = WorkflowConditionalLogicEngine.evaluate_condition_group(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            group=group,
            context={'candidate': {'source': 'agency'}},
            write_log=False,
        )

        assert result['passed'] is True

    def test_6_no_rules_matched_default_transition_used(self):
        success_transition = WorkflowStageTransition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            from_stage_id=self.stage.id,
            to_stage_id=self.next_stage.id,
            transition_type='decision',
            label='success',
            is_active=True,
        )
        default_transition = WorkflowStageTransition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            from_stage_id=self.stage.id,
            to_stage_id=self.default_stage.id,
            transition_type='decision',
            label='default',
            priority=0,
            is_active=True,
        )
        group = WorkflowConditionGroup.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            group_name='default-fallback',
            success_transition_id=success_transition.id,
            default_transition_id=default_transition.id,
            is_active=True,
        )
        WorkflowConditionRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            rule_name='candidate-accepted',
            rule_group=group.group_name,
            condition_type='workflow_context',
            field_name='candidate.response',
            operator='equals',
            expected_value='accepted',
            logical_join='AND',
            priority=1,
            is_active=True,
        )

        result = WorkflowConditionalLogicEngine.determine_transition_from_conditions(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            context={'candidate': {'response': 'rejected'}},
        )

        assert result is not None
        assert result['evaluation']['passed'] is False
        assert result['transition'].id == default_transition.id
