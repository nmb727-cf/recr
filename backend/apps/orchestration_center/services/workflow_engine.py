import json
import logging
import uuid
from datetime import timedelta
from django.utils import timezone
from apps.orchestration_center.models.workflow import (
    Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowExecutionLog, WorkflowVersion
)
from apps.orchestration_center.services.automation_analytics_engine import AutomationAnalyticsEngine

logger = logging.getLogger(__name__)

class WorkflowEngine:
    @staticmethod
    def trigger_workflows(tenant_id, trigger_event, entity_type, entity_id, context_data=None):
        """Find matching workflows and start execution."""
        workflows = Workflow.objects.filter(
            tenant_id=tenant_id, 
            trigger_event=trigger_event, 
            status='active',
            is_deleted=False
        )
        
        executions = []
        for workflow in workflows:
            AutomationAnalyticsEngine.track_trigger_metrics(tenant_id, workflow.id, trigger_event)
            
            # Use current version snapshot if available
            version = workflow.versions.filter(is_active=True).first()
            
            execution = WorkflowExecution.objects.create(
                tenant_id=tenant_id,
                workflow=workflow,
                version=version,
                entity_type=entity_type,
                entity_id=str(entity_id),
                status='running',
                context_data=context_data or {}
            )
            
            # Find start node
            start_node = workflow.nodes.filter(node_type='start').first()
            if start_node:
                WorkflowEngine.execute_node(execution, start_node)
            else:
                execution.status = 'failed'
                execution.save()
                WorkflowExecutionLog.objects.create(
                    execution=execution,
                    status='error',
                    message='No start node found'
                )
            executions.append(execution)
            
        return executions

    @staticmethod
    def execute_node(execution, node):
        """Evaluate node and move to next node."""
        if execution.status in ['failed', 'completed', 'rolled_back']:
            return

        WorkflowExecutionLog.objects.create(
            execution=execution,
            node=node,
            status='started',
            message=f'Executing node type: {node.node_type}'
        )
        
        context = execution.context_data
        
        try:
            start_ts = timezone.now()
            
            # Dispatch to specific handler based on node type
            handler_map = {
                'action': WorkflowEngine._handle_action,
                'condition': WorkflowEngine._handle_condition,
                'delay': WorkflowEngine._handle_delay,
                'approval': WorkflowEngine._handle_approval,
                'human_task': WorkflowEngine._handle_human_task,
                'scheduling': WorkflowEngine._handle_scheduling,
                'document': WorkflowEngine._handle_document,
                'integration': WorkflowEngine._handle_integration,
                'start': WorkflowEngine._handle_generic_pass,
                'end': WorkflowEngine._handle_end,
            }
            
            handler = handler_map.get(node.node_type)
            if not handler:
                raise ValueError(f"Unknown node type: {node.node_type}")
                
            next_node = handler(execution, node, context)
            
            # If the handler returns a node, we continue execution.
            # If it returns None, it might be waiting for an external event (delay, approval, human_task).
            if next_node:
                WorkflowEngine.execute_node(execution, next_node)
            elif node.node_type == 'end':
                execution.status = 'completed'
                execution.completed_at = timezone.now()
                execution.save()
                
        except Exception as e:
            logger.exception(f"Error executing workflow node {node.id}")
            execution.status = 'failed'
            execution.save()
            WorkflowExecutionLog.objects.create(
                execution=execution,
                node=node,
                status='failed',
                message=str(e)
            )

    @staticmethod
    def _handle_generic_pass(execution, node, context):
        """Simply move to the next node."""
        return WorkflowEngine._get_next_node(node, context)

    @staticmethod
    def _handle_action(execution, node, context):
        """Execute a system action."""
        start_ts = timezone.now()
        action_config = node.config
        
        # Call proper service based on action type
        # In a real system, this would use a registry of action handlers.
        action_type = action_config.get('type')
        success = True
        try:
            # Simulation of action execution
            logger.info(f"Executing action {action_type} for execution {execution.id}")
            # WorkflowEngine.call_service(action_type, action_config, context)
        except Exception:
            success = False
            raise

        AutomationAnalyticsEngine.track_action_metrics(
            tenant_id=execution.tenant_id,
            workflow_id=execution.workflow_id,
            action_type=action_type,
            success=success,
            duration_ms=(timezone.now() - start_ts).total_seconds() * 1000
        )
        
        return WorkflowEngine._get_next_node(node, context)

    @staticmethod
    def _handle_condition(execution, node, context):
        """Evaluate conditions and branch."""
        edges = node.outgoing_edges.all()
        for edge in edges:
            if WorkflowEngine.evaluate_condition(edge.condition, context):
                return edge.target_node
        return None

    @staticmethod
    def _handle_delay(execution, node, context):
        """Pause execution for a specific duration."""
        duration = int(node.config.get('duration', 0))
        unit = node.config.get('unit', 'hours')
        
        # In a real implementation, we would schedule a Celery task to resume
        execution.status = 'paused'
        execution.save()
        
        WorkflowExecutionLog.objects.create(
            execution=execution,
            node=node,
            status='paused',
            message=f"Paused for delay: {duration} {unit}"
        )
        return None

    @staticmethod
    def _handle_approval(execution, node, context):
        """Wait for human approval."""
        execution.status = 'paused'
        execution.save()
        
        WorkflowExecutionLog.objects.create(
            execution=execution,
            node=node,
            status='waiting_for_approval',
            message=f"Waiting for approval from: {node.config.get('approver_role', 'Manager')}"
        )
        # Create approval record in apps.orchestration_center.models.WorkflowApproval
        return None

    @staticmethod
    def _handle_human_task(execution, node, context):
        """Wait for a human to complete a task."""
        execution.status = 'paused'
        execution.save()
        
        WorkflowExecutionLog.objects.create(
            execution=execution,
            node=node,
            status='waiting_for_task',
            message=f"Waiting for task completion: {node.config.get('task_name')}"
        )
        return None

    @staticmethod
    def _handle_scheduling(execution, node, context):
        """Check availability or book interview."""
        # Simulated scheduling logic
        return WorkflowEngine._get_next_node(node, context)

    @staticmethod
    def _handle_document(execution, node, context):
        """Generate or upload a document."""
        # Simulated document generation
        return WorkflowEngine._get_next_node(node, context)

    @staticmethod
    def _handle_integration(execution, node, context):
        """Send data to external system."""
        # Simulated integration call
        return WorkflowEngine._get_next_node(node, context)

    @staticmethod
    def _handle_end(execution, node, context):
        """Finalize workflow."""
        return None

    @staticmethod
    def _get_next_node(node, context):
        """Find the next node based on edges."""
        edges = node.outgoing_edges.all()
        if edges.exists():
            return edges.first().target_node
        return None

    @staticmethod
    def evaluate_condition(condition, context):
        """Evaluate condition against context data."""
        if not condition:
            return True
            
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        context_value = context.get(field)
        
        if operator == 'equals':
            return str(context_value) == str(value)
        elif operator == 'greater_than':
            try:
                return float(context_value) > float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'less_than':
            try:
                return float(context_value) < float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'contains':
            return str(value) in str(context_value)
            
        return False

    @staticmethod
    def resume_execution(execution_id, node_id, context_update=None):
        """Resume a paused workflow execution."""
        execution = WorkflowExecution.objects.get(id=execution_id)
        node = WorkflowNode.objects.get(id=node_id)
        
        if context_update:
            execution.context_data.update(context_update)
            execution.save()
            
        execution.status = 'running'
        execution.save()
        
        # Move to next node after the one we were waiting on
        next_node = WorkflowEngine._get_next_node(node, execution.context_data)
        if next_node:
            WorkflowEngine.execute_node(execution, next_node)
        else:
            execution.status = 'completed'
            execution.completed_at = timezone.now()
            execution.save()
