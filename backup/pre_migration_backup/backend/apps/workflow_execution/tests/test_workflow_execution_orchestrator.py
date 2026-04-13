import uuid

import pytest

from apps.orchestration_center.models.workflow import Workflow, WorkflowEdge, WorkflowNode
from apps.workflow_execution.models import (
    WorkflowExecutionContext,
    WorkflowExecutionDecision,
    WorkflowInstance,
    WorkflowOrchestratorLog,
    WorkflowRoutingRule,
    WorkflowStageExecution,
)
from apps.workflow_execution.services.workflow_execution_orchestrator import WorkflowExecutionOrchestrator
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker


def make_workflow(tenant_id, *, with_wait=False):
    workflow = Workflow.objects.create(
        tenant_id=tenant_id,
        name='Orchestrator Test WF',
        trigger_event='job_created',
        status='active',
        is_active=True,
    )
    start = WorkflowNode.objects.create(workflow=workflow, node_type='start')
    action = WorkflowNode.objects.create(workflow=workflow, node_type='action')
    approval = WorkflowNode.objects.create(workflow=workflow, node_type='approval', config={'wait_reason': 'Approval Required'})
    end = WorkflowNode.objects.create(workflow=workflow, node_type='end')

    if with_wait:
        WorkflowEdge.objects.create(workflow=workflow, source_node=start, target_node=approval)
        WorkflowEdge.objects.create(workflow=workflow, source_node=approval, target_node=end)
    else:
        WorkflowEdge.objects.create(workflow=workflow, source_node=start, target_node=action)
        WorkflowEdge.objects.create(workflow=workflow, source_node=action, target_node=end)

    return workflow, start, action, approval, end


@pytest.mark.django_db
class TestWorkflowExecutionOrchestrator:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()

    def test_1_start_initializes_context_and_enters_first_stage(self):
        workflow, start, *_ = make_workflow(self.tenant_id, with_wait=False)
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=workflow.id,
            entity_type='job',
            entity_id=uuid.uuid4(),
            status='pending',
        )

        result = WorkflowExecutionOrchestrator.orchestrate_workflow_instance(
            instance.id,
            context={'current_job': 'J-1001'},
            source_type='workflow',
        )

        instance.refresh_from_db()
        assert result['decision_type'] == 'transition_select'
        assert WorkflowExecutionContext.objects.filter(workflow_instance=instance, context_key='current_job').exists()
        assert WorkflowOrchestratorLog.objects.filter(workflow_instance=instance, log_type='start').exists()

    def test_2_stage_completes_and_next_transition_selected(self):
        workflow, *_ = make_workflow(self.tenant_id, with_wait=False)
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=workflow.id,
            entity_type='job',
            entity_id=uuid.uuid4(),
            status='pending',
        )

        result = WorkflowExecutionOrchestrator.orchestrate_workflow_instance(instance.id)
        instance.refresh_from_db()

        assert result['decision_type'] == 'transition_select'
        assert instance.status in {'running', 'completed'}

    def test_3_stage_requires_approval_wait_decision_logged(self):
        workflow, *_ = make_workflow(self.tenant_id, with_wait=True)
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=workflow.id,
            entity_type='job',
            entity_id=uuid.uuid4(),
            status='pending',
        )
        WorkflowExecutionOrchestrator.orchestrate_workflow_instance(instance.id)
        instance.refresh_from_db()
        assert instance.status == 'waiting'

        result = WorkflowExecutionOrchestrator.orchestrate_workflow_instance(instance.id)
        assert result['decision_type'] == 'wait_required'
        assert WorkflowExecutionDecision.objects.filter(workflow_instance=instance, decision_type='wait_required').exists()

    def test_4_resume_event_resumes_correct_stage_path(self):
        workflow, *_ = make_workflow(self.tenant_id, with_wait=True)
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=workflow.id,
            entity_type='job',
            entity_id=uuid.uuid4(),
            status='pending',
        )
        WorkflowExecutionOrchestrator.orchestrate_workflow_instance(instance.id)
        instance.refresh_from_db()
        assert instance.status == 'waiting'

        result = WorkflowExecutionOrchestrator.orchestrate_workflow_instance(
            instance.id,
            resume_event='approval_received',
            context={'approval_result': 'approved'},
            source_type='event',
        )
        instance.refresh_from_db()

        assert result['decision_type'] == 'resume_allowed'
        assert instance.status in {'running', 'completed'}

    def test_5_cross_entity_routing_preserves_continuity(self):
        workflow, start, *_ = make_workflow(self.tenant_id, with_wait=False)
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=workflow.id,
            entity_type='company',
            entity_id=uuid.uuid4(),
            status='running',
        )
        instance.current_stage_id = start.id
        instance.save(update_fields=['current_stage_id', 'updated_at'])
        stage_exec = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_id=start.id,
            stage_name='start',
            status='running',
        )

        WorkflowRoutingRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=workflow.id,
            stage_id=start.id,
            route_to_entity_type='agency',
            route_to_actor_type='agency_manager',
            is_active=True,
            label='Company to agency review',
        )

        result = WorkflowExecutionOrchestrator.orchestrate_workflow_instance(instance.id)
        instance.refresh_from_db()

        assert result['decision_type'] == 'routing_required'
        assert instance.current_stage_id == start.id
        assert stage_exec.workflow_instance_id == instance.id

    def test_6_final_handoff_or_end_state_marks_complete(self):
        workflow, _, _, _, end = make_workflow(self.tenant_id, with_wait=False)
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=workflow.id,
            entity_type='job',
            entity_id=uuid.uuid4(),
            status='running',
        )
        instance.current_stage_id = end.id
        instance.save(update_fields=['current_stage_id', 'updated_at'])

        result = WorkflowExecutionOrchestrator.orchestrate_workflow_instance(instance.id)
        instance.refresh_from_db()

        assert result['decision_result'] in {'complete', 'already_complete'}
        assert instance.status == 'completed'

    def test_7_stage_failure_retry_allowed_retries(self):
        workflow, start, *_ = make_workflow(self.tenant_id, with_wait=False)
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=workflow.id,
            entity_type='job',
            entity_id=uuid.uuid4(),
            status='running',
        )
        instance.current_stage_id = start.id
        instance.save(update_fields=['current_stage_id', 'updated_at'])

        stage_exec = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_id=start.id,
            stage_name='start',
            status='failed',
            metadata={'max_retries': 2, 'retry_count': 0},
        )

        result = WorkflowExecutionOrchestrator.orchestrate_workflow_instance(instance.id)
        instance.refresh_from_db()

        assert result['decision_type'] == 'retry_required'
        assert WorkflowExecutionDecision.objects.filter(workflow_instance=instance, decision_type='retry_required').exists()
