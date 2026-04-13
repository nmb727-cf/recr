import uuid

import pytest

from apps.orchestration_center.models.workflow import Workflow, WorkflowEdge, WorkflowNode
from apps.workflow_execution.models import (
    WorkflowFailureLog,
    WorkflowTransitionLog,
    WorkflowWaitState,
)
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine


def make_workflow(tenant_id):
    workflow = Workflow.objects.create(
        tenant_id=tenant_id,
        name='Instance Tracker WF',
        trigger_event='job_created',
        status='active',
        is_active=True,
    )
    start = WorkflowNode.objects.create(workflow=workflow, node_type='start')
    approval = WorkflowNode.objects.create(workflow=workflow, node_type='approval', config={'wait_reason': 'Approval Needed'})
    end = WorkflowNode.objects.create(workflow=workflow, node_type='end')
    WorkflowEdge.objects.create(workflow=workflow, source_node=start, target_node=approval)
    WorkflowEdge.objects.create(workflow=workflow, source_node=approval, target_node=end)
    return workflow, start, approval, end


@pytest.mark.django_db
class TestWorkflowInstanceTracker:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow, self.start, self.approval, self.end = make_workflow(self.tenant_id)
        self.entity_id = uuid.uuid4()

    def test_1_workflow_created_instance_created(self):
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='job',
            entity_id=self.entity_id,
        )

        assert instance.id is not None
        assert instance.status == 'pending'

    def test_2_stage_moves_transition_logged(self):
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='job',
            entity_id=self.entity_id,
            status='running',
        )

        WorkflowStageEngine.complete_stage(instance, self.start)
        assert WorkflowTransitionLog.objects.filter(workflow_instance=instance).exists()

    def test_3_wait_state_created_waiting_recorded(self):
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='job',
            entity_id=self.entity_id,
            status='running',
        )

        WorkflowStageEngine.complete_stage(instance, self.start)
        instance.refresh_from_db()
        assert instance.status == 'waiting'
        assert WorkflowWaitState.objects.filter(workflow_instance=instance, status='waiting').exists()

    def test_4_wait_resumed_stage_resumed(self):
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='job',
            entity_id=self.entity_id,
            status='running',
        )

        WorkflowStageEngine.complete_stage(instance, self.start)
        wait_state = WorkflowWaitState.objects.filter(workflow_instance=instance, status='waiting').first()
        assert wait_state is not None

        WorkflowStageEngine.resume_wait_state(wait_state.id, triggered_by='user')

        wait_state.refresh_from_db()
        instance.refresh_from_db()
        assert wait_state.status == 'resumed'
        assert instance.status == 'completed'

    def test_5_failure_retry_possible(self):
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='job',
            entity_id=self.entity_id,
            status='running',
        )
        stage_execution = WorkflowInstanceTracker.start_stage_execution(
            instance,
            stage_id=self.start.id,
            stage_name='start',
        )
        WorkflowInstanceTracker.fail_stage_execution(
            stage_execution,
            error_message='Forced failure',
            error_type='test_failure',
        )

        assert WorkflowFailureLog.objects.filter(workflow_instance=instance).exists()

        retried = WorkflowInstanceTracker.retry_stage(instance, stage_execution=stage_execution)
        assert retried is not None
