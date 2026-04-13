import logging
from ..models import (
    AgencyWorkflowDefinition,
    AgencyWorkflowNode,
    AgencyWorkflowEdge
)

logger = logging.getLogger(__name__)

class AgencyVisualWorkflowEngine:
    @staticmethod
    def start_workflow(workflow_id, context_data):
        """Initializes and runs a custom agency workflow."""
        try:
            workflow = AgencyWorkflowDefinition.objects.get(id=workflow_id, status='active')
            start_node = workflow.nodes.filter(node_type='start').first()
            if not start_node:
                logger.error(f"No start node found for workflow {workflow_id}")
                return
            
            logger.info(f"Starting agency workflow: {workflow.name}")
            AgencyVisualWorkflowEngine.execute_node(start_node, context_data)
        except AgencyWorkflowDefinition.DoesNotExist:
            logger.error(f"Workflow {workflow_id} not found or not active")

    @staticmethod
    def execute_node(node, context_data):
        """Executes logic for a specific node and moves to next."""
        node_type = node.node_type
        config = node.config
        
        logger.info(f"Executing node: {node_type} (ID: {node.id})")
        
        # Dispatch logic based on node_type
        if node_type == 'action':
            AgencyVisualWorkflowEngine._handle_action(node, context_data)
        elif node_type == 'submission':
            AgencyVisualWorkflowEngine.create_submission(node, context_data)
        elif node_type == 'followup':
            AgencyVisualWorkflowEngine.create_followup(node, context_data)
        elif node_type == 'wait_state':
            AgencyVisualWorkflowEngine.handle_wait_state(node, context_data)
            return # Wait nodes pause execution
            
        # Move to next node
        AgencyVisualWorkflowEngine.move_next_node(node, context_data)

    @staticmethod
    def _handle_action(node, context_data):
        action_type = node.config.get('type')
        logger.info(f"Performing action: {action_type}")
        # Logic to move stage, assign recruiter, etc.

    @staticmethod
    def evaluate_condition(edge, context_data):
        """Checks if the edge transition condition is met."""
        condition = edge.condition
        if not condition:
            return True
        
        # Simple evaluation logic for conditions
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        actual_value = context_data.get(field)
        
        if operator == 'equals':
            return str(actual_value) == str(value)
        elif operator == 'greater_than':
            return float(actual_value) > float(value)
        # etc...
        return True

    @staticmethod
    def move_next_node(node, context_data):
        """Finds next node(s) based on outgoing edges and conditions."""
        edges = node.outgoing_edges.all()
        for edge in edges:
            if AgencyVisualWorkflowEngine.evaluate_condition(edge, context_data):
                AgencyVisualWorkflowEngine.execute_node(edge.target_node, context_data)

    @staticmethod
    def handle_wait_state(node, context_data):
        """Handles human/external wait states."""
        logger.info(f"Workflow waiting at node: {node.id}")
        # Persist wait state logic

    @staticmethod
    def create_followup(node, context_data):
        logger.info("Creating followup task")

    @staticmethod
    def create_submission(node, context_data):
        logger.info("Creating candidate submission to client")

    @staticmethod
    def close_workflow(workflow_id):
        logger.info(f"Workflow {workflow_id} closed")
