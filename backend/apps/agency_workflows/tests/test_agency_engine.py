import uuid
import pytest
from apps.agency_workflows.models import (
    AgencyWorkflowDefinition,
    AgencyWorkflowNode,
    AgencyWorkflowEdge
)
from apps.agency_workflows.services.agency_visual_workflow_engine import AgencyVisualWorkflowEngine

@pytest.mark.django_db
class TestAgencyVisualWorkflowEngine:
    def setup_method(self):
        self.workflow = AgencyWorkflowDefinition.objects.create(
            name="Test Agency Workflow",
            scope="submission",
            status="active"
        )
        self.start_node = AgencyWorkflowNode.objects.create(
            workflow=self.workflow,
            node_type="start",
            position_x=0,
            position_y=0
        )
        self.action_node = AgencyWorkflowNode.objects.create(
            workflow=self.workflow,
            node_type="action",
            config={"type": "notify_recruiter"},
            position_x=100,
            position_y=100
        )
        self.edge = AgencyWorkflowEdge.objects.create(
            workflow=self.workflow,
            source_node=self.start_node,
            target_node=self.action_node
        )

    def test_workflow_start(self, caplog):
        caplog.set_level("INFO")
        AgencyVisualWorkflowEngine.start_workflow(self.workflow.id, {"candidate_id": str(uuid.uuid4())})
        
        assert "Starting agency workflow: Test Agency Workflow" in caplog.text
        assert f"Executing node: start (ID: {self.start_node.id})" in caplog.text
        assert f"Executing node: action (ID: {self.action_node.id})" in caplog.text
        assert "Performing action: notify_recruiter" in caplog.text

    def test_workflow_condition_branching(self, caplog):
        caplog.set_level("INFO")
        
        # Add a conditional node
        high_salary_node = AgencyWorkflowNode.objects.create(
            workflow=self.workflow,
            node_type="action",
            config={"type": "manager_approval"},
            position_x=200,
            position_y=200
        )
        
        # Edge with condition: salary > 100000
        AgencyWorkflowEdge.objects.create(
            workflow=self.workflow,
            source_node=self.action_node,
            target_node=high_salary_node,
            condition={"field": "salary", "operator": "greater_than", "value": 100000}
        )
        
        # Case 1: Salary 150000 (Triggered)
        AgencyVisualWorkflowEngine.start_workflow(self.workflow.id, {"salary": 150000})
        assert "Performing action: manager_approval" in caplog.text
        
        # Case 2: Salary 50000 (Not triggered - wait, our simple engine currently moves if condition is met or True if no condition)
        # In our engine, it iterates all edges. If condition fails, it doesn't execute target.
        # Let's verify it doesn't run manager_approval for low salary.
        caplog.clear()
        AgencyVisualWorkflowEngine.start_workflow(self.workflow.id, {"salary": 50000})
        assert "Performing action: manager_approval" not in caplog.text
