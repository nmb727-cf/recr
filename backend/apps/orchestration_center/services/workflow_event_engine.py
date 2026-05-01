import logging
from django.utils import timezone
from apps.orchestration_center.models.event_trigger import (
    WorkflowEventDefinition,
    WorkflowEventSubscription,
    WorkflowEventLog,
    WorkflowEventDebugTrace,
)
from apps.orchestration_center.models.workflow import Workflow
from apps.orchestration_center.services.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)

class WorkflowEventEngine:
    @staticmethod
    def emit_event(tenant_id, event_key, entity_type, entity_id, payload, source_module):
        """
        Main entry point for emitting system events.
        Logs the event and triggers matching workflows.
        """
        # 1. Log the event
        event_log = WorkflowEventLog.objects.create(
            tenant_id=tenant_id,
            event_key=event_key,
            entity_type=entity_type,
            entity_id=str(entity_id),
            payload=payload,
            source_module=source_module,
            status='emitted'
        )

        # 2. Validate against definition (optional registry check)
        event_def = WorkflowEventDefinition.objects.filter(event_key=event_key, is_active=True).first()
        if not event_def:
            event_log.status = 'ignored'
            event_log.save()
            return

        # 3. Find matching subscriptions
        subscriptions = WorkflowEventSubscription.objects.filter(
            event_definition=event_def,
            tenant_id=tenant_id,
            is_active=True,
            workflow__status='active'
        )

        matched_count = 0
        for sub in subscriptions:
            workflow = sub.workflow
            
            # 4. Evaluate trigger filters
            is_match, reason, trace_payload = WorkflowEventEngine.evaluate_trigger_filters(
                sub.trigger_filters, payload
            )

            decision = 'matched' if is_match else 'filtered_out'
            
            # 5. Create debug trace
            WorkflowEventDebugTrace.objects.create(
                tenant_id=tenant_id,
                event_log=event_log,
                workflow=workflow,
                decision=decision,
                reason=reason,
                trace_payload=trace_payload
            )

            if is_match:
                # 6. Dispatch to workflow engine
                try:
                    WorkflowEngine.trigger_workflows(
                        tenant_id=tenant_id,
                        trigger_event=event_key, # Or workflow.trigger_event
                        entity_type=entity_type,
                        entity_id=entity_id,
                        context_data=payload
                    )
                    matched_count += 1
                except Exception as e:
                    logger.exception(f"Failed to dispatch event {event_key} to workflow {workflow.id}")
                    WorkflowEventDebugTrace.objects.create(
                        tenant_id=tenant_id,
                        event_log=event_log,
                        workflow=workflow,
                        decision='failed',
                        reason=str(e)
                    )

        if matched_count > 0:
            event_log.status = 'consumed'
        elif subscriptions.exists():
            event_log.status = 'ignored' # Filtered out by all
        
        event_log.save()

    @staticmethod
    def evaluate_trigger_filters(filters, payload):
        """
        Evaluates if the event payload matches the subscription filters.
        Supports simple key-value matching for Phase 1.
        """
        if not filters:
            return True, "No filters defined", {}

        trace_payload = {}
        for key, expected_value in filters.items():
            actual_value = payload.get(key)
            trace_payload[key] = {"expected": expected_value, "actual": actual_value}
            
            # Basic comparison
            if str(actual_value) != str(expected_value):
                return False, f"Filter mismatch: {key}", trace_payload

        return True, "All filters matched", trace_payload

    @staticmethod
    def validate_event_payload(event_key, payload):
        """Validates payload against registered schema."""
        event_def = WorkflowEventDefinition.objects.filter(event_key=event_key).first()
        if not event_def or not event_def.payload_schema:
            return True, []
            
        errors = []
        schema = event_def.payload_schema
        for key, expected_type in schema.items():
            if key not in payload:
                errors.append(f"Missing required key: {key}")
            # Add more sophisticated type checking if needed
            
        return len(errors) == 0, errors
