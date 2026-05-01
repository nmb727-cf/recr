import logging
from django.utils import timezone
from ..models import (
    AgencyWorkflowEventDefinition,
    AgencyWorkflowEventSubscription,
    AgencyWorkflowEventLog,
    AgencyWorkflowEventDebugTrace
)
from ..models import AgencyWorkflowDefinition
from .agency_visual_workflow_engine import AgencyVisualWorkflowEngine

logger = logging.getLogger(__name__)

class AgencyWorkflowEventEngine:
    @staticmethod
    def emit_agency_event(tenant_id, event_key, entity_type, entity_id, payload, source_module, 
                          candidate_id=None, client_id=None, job_id=None):
        """Emits an event and triggers matching agency workflows."""
        # 1. Log the event
        event_log = AgencyWorkflowEventEngine.log_event(
            tenant_id, event_key, entity_type, entity_id, payload, source_module,
            candidate_id, client_id, job_id
        )

        # 2. Validate payload (simplified for now)
        if not AgencyWorkflowEventEngine.validate_event_payload(event_key, payload):
            event_log.status = 'failed'
            event_log.save()
            return event_log

        # 3. Find matching workflows
        subscriptions = AgencyWorkflowEventEngine.find_matching_workflows(tenant_id, event_key, payload)
        
        if not subscriptions:
            event_log.status = 'ignored'
            event_log.save()
            return event_log

        # 4. Dispatch to workflows
        executed_count = 0
        for sub in subscriptions:
            AgencyWorkflowEventEngine.dispatch_event_to_agency_workflow(event_log, sub, payload)
            executed_count += 1

        event_log.status = 'consumed' if executed_count > 0 else 'ignored'
        event_log.save()
        
        return event_log

    @staticmethod
    def validate_event_payload(event_key, payload):
        """Validates payload against defined schema."""
        try:
            definition = AgencyWorkflowEventDefinition.objects.get(event_key=event_key)
            # Schema validation logic would go here
            return True
        except AgencyWorkflowEventDefinition.DoesNotExist:
            logger.warning(f"Event definition not found for key: {event_key}")
            return True # Allow if not explicitly defined yet? Or return False for strictness.

    @staticmethod
    def find_matching_workflows(tenant_id, event_key, payload):
        """Finds active subscriptions for this event type within the tenant."""
        active_subs = AgencyWorkflowEventSubscription.objects.filter(
            tenant_id=tenant_id,
            event_definition__event_key=event_key,
            is_active=True,
            workflow__status='active'
        )
        
        matching_subs = []
        for sub in active_subs:
            if AgencyWorkflowEventEngine.evaluate_trigger_filters(sub.trigger_filters, payload):
                matching_subs.append(sub)
            else:
                AgencyWorkflowEventEngine.generate_debug_trace(
                    tenant_id, None, sub.workflow, 'filtered_out', "Filters did not match payload"
                )
        
        return matching_subs

    @staticmethod
    def evaluate_trigger_filters(filters, payload):
        """Evaluates if the event payload matches the subscription filters."""
        if not filters:
            return True
        
        for key, expected_value in filters.items():
            actual_value = payload.get(key)
            if str(actual_value) != str(expected_value):
                return False
        return True

    @staticmethod
    def dispatch_event_to_agency_workflow(event_log, subscription, payload):
        """Starts the agency workflow for a matched event."""
        tenant_id = event_log.tenant_id
        workflow = subscription.workflow
        
        try:
            AgencyWorkflowEventEngine.generate_debug_trace(
                tenant_id, event_log, workflow, 'matched', "Event matched subscription filters"
            )
            
            # Start the execution engine
            AgencyVisualWorkflowEngine.start_workflow(workflow.id, payload)
            
            AgencyWorkflowEventEngine.generate_debug_trace(
                tenant_id, event_log, workflow, 'executed', "Workflow execution started"
            )
        except Exception as e:
            logger.error(f"Failed to dispatch event to workflow {workflow.id}: {str(e)}")
            AgencyWorkflowEventEngine.generate_debug_trace(
                tenant_id, event_log, workflow, 'failed', f"Error: {str(e)}"
            )

    @staticmethod
    def log_event(tenant_id, event_key, entity_type, entity_id, payload, source_module,
                  candidate_id, client_id, job_id):
        return AgencyWorkflowEventLog.objects.create(
            tenant_id=tenant_id,
            event_key=event_key,
            entity_type=entity_type,
            entity_id=entity_id,
            related_candidate_id=candidate_id,
            related_client_id=client_id,
            related_job_id=job_id,
            payload=payload,
            source_module=source_module,
            status='emitted'
        )

    @staticmethod
    def generate_debug_trace(tenant_id, event_log, workflow, decision, reason, trace_payload=None):
        return AgencyWorkflowEventDebugTrace.objects.create(
            tenant_id=tenant_id,
            event_log=event_log,
            workflow=workflow,
            decision=decision,
            reason=reason,
            trace_payload=trace_payload or {}
        )
