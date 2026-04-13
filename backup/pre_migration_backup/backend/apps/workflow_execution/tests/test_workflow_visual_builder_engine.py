import uuid

from django.test import TestCase

from apps.orchestration_center.models.workflow import Workflow
from apps.workflow_execution.models import WorkflowBuilderConnection, WorkflowBuilderNode, WorkflowInstance
from apps.workflow_execution.services.workflow_execution_engine import WorkflowExecutionEngine
from apps.workflow_execution.services.workflow_visual_builder_engine import WorkflowVisualBuilderEngine


class TestWorkflowVisualBuilderEngine(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Visual Builder WF',
            description='Workflow for visual builder tests',
            trigger_event='job_created',
            status='active',
            is_active=True,
        )

    def test_1_create_simple_workflow_nodes_saved(self):
        start = WorkflowVisualBuilderEngine.create_node(
            workflow_id=self.workflow.id,
            node_type='start',
            node_name='Start Hiring',
            tenant_id=self.tenant_id,
        )
        stage = WorkflowVisualBuilderEngine.create_node(
            workflow_id=self.workflow.id,
            node_type='stage',
            node_name='Review Candidate',
            tenant_id=self.tenant_id,
        )

        assert start is not None
        assert stage is not None
        assert WorkflowBuilderNode.objects.filter(workflow_id=self.workflow.id).count() == 2

    def test_2_connect_nodes_connection_created(self):
        source = WorkflowVisualBuilderEngine.create_node(
            workflow_id=self.workflow.id,
            node_type='start',
            node_name='Start Hiring',
            tenant_id=self.tenant_id,
        )
        target = WorkflowVisualBuilderEngine.create_node(
            workflow_id=self.workflow.id,
            node_type='stage',
            node_name='Agency Submit',
            tenant_id=self.tenant_id,
        )

        connection = WorkflowVisualBuilderEngine.connect_nodes(
            workflow_id=self.workflow.id,
            source_node_id=source.id,
            target_node_id=target.id,
            connection_type='default',
        )
        assert connection is not None
        assert WorkflowBuilderConnection.objects.filter(workflow_id=self.workflow.id).count() == 1

    def test_3_decision_node_multiple_paths_valid(self):
        start = WorkflowVisualBuilderEngine.create_node(
            workflow_id=self.workflow.id,
            node_type='start',
            node_name='Start',
            tenant_id=self.tenant_id,
        )
        decision = WorkflowVisualBuilderEngine.create_node(
            workflow_id=self.workflow.id,
            node_type='decision',
            node_name='Pass or Fail',
            tenant_id=self.tenant_id,
        )
        passed = WorkflowVisualBuilderEngine.create_node(
            workflow_id=self.workflow.id,
            node_type='stage',
            node_name='Interview 1',
            tenant_id=self.tenant_id,
        )
        failed = WorkflowVisualBuilderEngine.create_node(
            workflow_id=self.workflow.id,
            node_type='end',
            node_name='End Hiring',
            tenant_id=self.tenant_id,
        )
        WorkflowVisualBuilderEngine.connect_nodes(workflow_id=self.workflow.id, source_node_id=start.id, target_node_id=decision.id)
        WorkflowVisualBuilderEngine.connect_nodes(workflow_id=self.workflow.id, source_node_id=decision.id, target_node_id=passed.id, connection_type='success')
        WorkflowVisualBuilderEngine.connect_nodes(workflow_id=self.workflow.id, source_node_id=decision.id, target_node_id=failed.id, connection_type='failure')
        WorkflowVisualBuilderEngine.connect_nodes(workflow_id=self.workflow.id, source_node_id=passed.id, target_node_id=failed.id)

        validation = WorkflowVisualBuilderEngine.validate_workflow_graph(workflow_id=self.workflow.id)
        assert validation['valid'] is True

    def test_4_invalid_workflow_returns_validation_error(self):
        stage = WorkflowVisualBuilderEngine.create_node(
            workflow_id=self.workflow.id,
            node_type='stage',
            node_name='Only Stage',
            tenant_id=self.tenant_id,
        )
        assert stage is not None

        validation = WorkflowVisualBuilderEngine.validate_workflow_graph(workflow_id=self.workflow.id)
        assert validation['valid'] is False
        assert any('start node' in err.lower() for err in validation['errors'])

    def test_5_end_to_end_workflow_execution_compatible(self):
        start = WorkflowVisualBuilderEngine.create_node(workflow_id=self.workflow.id, node_type='start', node_name='Start', tenant_id=self.tenant_id)
        agency_submit = WorkflowVisualBuilderEngine.create_node(workflow_id=self.workflow.id, node_type='stage', node_name='Agency Submit', tenant_id=self.tenant_id)
        prequal = WorkflowVisualBuilderEngine.create_node(workflow_id=self.workflow.id, node_type='stage', node_name='Pre Qualification', tenant_id=self.tenant_id)
        decision = WorkflowVisualBuilderEngine.create_node(workflow_id=self.workflow.id, node_type='decision', node_name='Decision', tenant_id=self.tenant_id)
        interview = WorkflowVisualBuilderEngine.create_node(workflow_id=self.workflow.id, node_type='stage', node_name='Interview 1', tenant_id=self.tenant_id)
        end = WorkflowVisualBuilderEngine.create_node(workflow_id=self.workflow.id, node_type='end', node_name='End', tenant_id=self.tenant_id)

        WorkflowVisualBuilderEngine.connect_nodes(workflow_id=self.workflow.id, source_node_id=start.id, target_node_id=agency_submit.id)
        WorkflowVisualBuilderEngine.connect_nodes(workflow_id=self.workflow.id, source_node_id=agency_submit.id, target_node_id=prequal.id)
        WorkflowVisualBuilderEngine.connect_nodes(workflow_id=self.workflow.id, source_node_id=prequal.id, target_node_id=decision.id)
        WorkflowVisualBuilderEngine.connect_nodes(workflow_id=self.workflow.id, source_node_id=decision.id, target_node_id=interview.id, connection_type='success')
        WorkflowVisualBuilderEngine.connect_nodes(workflow_id=self.workflow.id, source_node_id=decision.id, target_node_id=end.id, connection_type='failure')
        WorkflowVisualBuilderEngine.connect_nodes(workflow_id=self.workflow.id, source_node_id=interview.id, target_node_id=end.id)

        save_result = WorkflowVisualBuilderEngine.save_to_runtime(workflow_id=self.workflow.id)
        assert save_result['saved'] is True
        assert self.workflow.nodes.count() == 6
        assert self.workflow.edges.count() == 6

        instance = WorkflowExecutionEngine.start_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='job',
            entity_id=uuid.uuid4(),
            context={'job_title': 'Engineer'},
        )
        instance.refresh_from_db()
        assert WorkflowInstance.objects.filter(id=instance.id).exists()
        assert instance.status in {'running', 'waiting', 'completed'}
