"""
WorkflowExecutionEngine
========================
High-level entry points: start, resume, fail.
Delegates all stage-transition / wait-state logic to WorkflowStageEngine.
Kept thin so callers don't need to know about the stage engine directly.
"""
import logging
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowInstance,
    WorkflowStageExecution,
    WorkflowExecutionTimeline,
    WAIT_REASON_RESUME_EVENTS,
    NODE_TYPE_WAIT_REASONS,
)
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.orchestration_center.models.workflow import Workflow, WorkflowNode

logger = logging.getLogger(__name__)


class WorkflowExecutionEngine:

    # ------------------------------------------------------------------ #
    # Start                                                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def start_workflow_instance(tenant_id, workflow_id, entity_type, entity_id, context=None):
        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine

        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status='running',
            metadata={'context_data': context or {}},
        )

        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            WorkflowStageEngine.fail_stage(instance, reason=f"Workflow {workflow_id} not found")
            return instance

        start_node = workflow.nodes.filter(node_type='start').first()
        if start_node:
            WorkflowStageEngine.complete_stage(instance, start_node)
        else:
            WorkflowStageEngine.fail_stage(instance, reason="No start node found")

        return instance

    # ------------------------------------------------------------------ #
    # Resume                                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def resume_workflow(instance_id, triggered_by='system', actor_id=None, context=None):
        """
        Resume a waiting workflow instance.
        Delegates to WorkflowStageEngine.resume_instance which uses WorkflowWaitState.
        """
        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine
        return WorkflowStageEngine.resume_instance(
            instance_id,
            triggered_by=triggered_by,
            actor_id=actor_id,
            context=context,
        )

    # ------------------------------------------------------------------ #
    # Fail / complete (convenience)                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def fail_workflow(instance, reason='Failed'):
        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine
        WorkflowStageEngine.fail_stage(instance, reason=reason)

    @staticmethod
    def complete_workflow(instance):
        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine
        WorkflowStageEngine._complete_workflow(instance)

    # ------------------------------------------------------------------ #
    # Resume from event (called by WorkflowEventListener)                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def resume_from_event(event_key, tenant_id, entity_type=None, entity_id=None):
        """
        Delegates to WorkflowStageEngine.resume_by_event which uses the
        full WorkflowWaitState + WAIT_REASON_RESUME_EVENTS mapping.
        """
        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine
        return WorkflowStageEngine.resume_by_event(
            event_key=event_key,
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )

    # ------------------------------------------------------------------ #
    # Legacy compat shims (used by existing tests)                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def execute_stage(instance, node):
        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine
        WorkflowStageEngine.complete_stage(instance, node)

    @staticmethod
    def move_to_next_stage(instance, current_node):
        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine
        WorkflowStageEngine.move_to_next_stage(instance, current_node)

    @staticmethod
    def handle_wait_state(instance, node):
        from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine
        WorkflowStageEngine.handle_wait_state(instance, node)

    @staticmethod
    def evaluate_decision(edge, instance):
        from apps.workflow_execution.services.workflow_stage_engine import ConditionEvaluator
        is_match, _, _ = ConditionEvaluator.evaluate(edge.condition or {}, instance.context_data)
        return is_match
