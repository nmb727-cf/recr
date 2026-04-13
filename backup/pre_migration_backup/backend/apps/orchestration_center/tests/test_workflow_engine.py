from django.test import TestCase
from apps.orchestration_center.models.workflow import Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowTemplate
from apps.orchestration_center.services.workflow_engine import WorkflowEngine
from django.utils import timezone
import uuid

class WorkflowEngineTest(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()

    def test_workflow_engine_candidate_applied(self):
        workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name="Auto Assign Recruiter",
            trigger_event="candidate_applied",
            is_active=True
        )
        
        start_node = WorkflowNode.objects.create(
            workflow=workflow,
            node_type="start"
        )
        
        action_node = WorkflowNode.objects.create(
            workflow=workflow,
            node_type="action",
            config={"type": "assign_user"}
        )
        
        WorkflowEdge.objects.create(
            workflow=workflow,
            source_node=start_node,
            target_node=action_node
        )
        
        # Trigger event
        executions = WorkflowEngine.trigger_workflows(
            tenant_id=self.tenant_id,
            trigger_event="candidate_applied",
            entity_type="candidate",
            entity_id="123"
        )
        
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].status, 'completed')
        self.assertTrue(executions[0].logs.count() >= 2)
        self.assertTrue(executions[0].logs.filter(node=action_node).exists())

    def test_workflow_engine_interview_completed(self):
        workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name="Move stage if score > 80",
            trigger_event="interview_completed",
            is_active=True
        )
        
        start_node = WorkflowNode.objects.create(
            workflow=workflow,
            node_type="start"
        )
        
        condition_node = WorkflowNode.objects.create(
            workflow=workflow,
            node_type="condition"
        )
        
        action_node = WorkflowNode.objects.create(
            workflow=workflow,
            node_type="action",
            config={"type": "move_stage"}
        )
        
        WorkflowEdge.objects.create(
            workflow=workflow,
            source_node=start_node,
            target_node=condition_node
        )
        
        WorkflowEdge.objects.create(
            workflow=workflow,
            source_node=condition_node,
            target_node=action_node,
            condition={"field": "score", "operator": "greater_than", "value": 80}
        )
        
        # Trigger event with context scoring 85 (Should execute action)
        executions_pass = WorkflowEngine.trigger_workflows(
            tenant_id=self.tenant_id,
            trigger_event="interview_completed",
            entity_type="interview",
            entity_id="123",
            context_data={"score": 85}
        )
        
        self.assertEqual(len(executions_pass), 1)
        self.assertEqual(executions_pass[0].status, 'completed')
        self.assertTrue(executions_pass[0].logs.filter(node=action_node).exists())
        
        # Trigger event with context scoring 75 (Should NOT execute action)
        executions_fail = WorkflowEngine.trigger_workflows(
            tenant_id=self.tenant_id,
            trigger_event="interview_completed",
            entity_type="interview",
            entity_id="124",
            context_data={"score": 75}
        )
        
        self.assertEqual(len(executions_fail), 1)
        self.assertEqual(executions_fail[0].status, 'completed')
        self.assertFalse(executions_fail[0].logs.filter(node=action_node).exists())

    def test_enable_workflow_template(self):
        template = WorkflowTemplate.objects.create(
            name="Test Template",
            category="Test",
            trigger_event="candidate_applied",
            template_json={
                'nodes': [{'id': 'start', 'type': 'start'}, {'id': 'end', 'type': 'end'}],
                'edges': [{'source': 'start', 'target': 'end'}]
            }
        )
        
        from apps.orchestration_center.api.views import WorkflowTemplateEnableView
        from rest_framework.test import APIRequestFactory, force_authenticate
        
        factory = APIRequestFactory()
        view = WorkflowTemplateEnableView.as_view()
        
        # Mock user
        from apps.accounts.models import CustomUser
        user = CustomUser.objects.create(email="admin@test.com", tenant_id=self.tenant_id, role="super_admin")
        
        request = factory.post(f'/api/v1/intelligence/workflows/templates/{template.id}/enable/')
        force_authenticate(request, user=user)
        
        response = view(request, pk=template.id)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Workflow.objects.filter(tenant_id=self.tenant_id, name="Test Template").exists())
        
        workflow = Workflow.objects.get(tenant_id=self.tenant_id, name="Test Template")
        self.assertEqual(workflow.nodes.count(), 2)
        self.assertEqual(workflow.edges.count(), 1)
