"""
Workflow Event Listener
=======================
Central entry point for all system events that can start or advance workflows.

Architecture:
  receive_event()
    → validate_registered_event()     (check against WorkflowEventDefinition registry)
    → find_matching_workflows()        (WorkflowEventSubscription + filters)
    → evaluate_trigger_filters()       (simple key/op/value matching)
    → start_workflow_instances()       (create WorkflowInstance via execution engine)
    → resume_from_event()              (advance waiting instances)
    → log_event_match_result()         (update WorkflowEventLog + WorkflowEventDebugTrace)
"""
import logging

from apps.orchestration_center.models.event_trigger import (
    WorkflowEventDefinition,
    WorkflowEventSubscription,
    WorkflowEventLog,
    WorkflowEventDebugTrace,
)
from apps.workflow_execution.services.workflow_execution_engine import WorkflowExecutionEngine

logger = logging.getLogger(__name__)


class WorkflowEventListener:

    # ------------------------------------------------------------------ #
    # Public entry point                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def receive_event(tenant_id, event_key, entity_type, entity_id, payload, source_module=''):
        """
        Receive a system event, validate it, match workflows, and start/advance them.

        Returns the WorkflowEventLog record created for this event.
        """
        # 1. Log raw event immediately
        event_log = WorkflowEventLog.objects.create(
            tenant_id=tenant_id,
            event_key=event_key,
            entity_type=entity_type,
            entity_id=str(entity_id),
            payload=payload,
            source_module=source_module or event_key.split('_')[0],
            status='emitted',
        )

        # 2. Validate against registry
        event_def, error = WorkflowEventListener.validate_registered_event(event_key)
        if error:
            event_log.status = 'ignored'
            event_log.save(update_fields=['status'])
            WorkflowEventListener.log_event_match_result(
                event_log, None, 'invalid', error
            )
            return event_log

        # 3. Find matching subscriptions (workflows that have subscribed to this event)
        subscriptions = WorkflowEventListener.find_matching_workflows(
            tenant_id, event_def, payload
        )

        matched_count = 0
        for sub, decision, reason in subscriptions:
            WorkflowEventListener.log_event_match_result(event_log, sub.workflow, decision, reason)

            if decision != 'matched':
                continue

            # 4. Start new workflow instance
            try:
                WorkflowEventListener.start_workflow_instances(
                    tenant_id, sub.workflow, entity_type, entity_id, payload
                )
                matched_count += 1
                WorkflowEventListener.log_event_match_result(
                    event_log, sub.workflow, 'started', 'Workflow instance created'
                )
            except Exception as exc:
                logger.exception(
                    "Failed to start workflow %s for event %s", sub.workflow_id, event_key
                )
                WorkflowEventListener.log_event_match_result(
                    event_log, sub.workflow, 'failed', str(exc)
                )

        # 5. Resume/advance waiting workflow instances via stage engine
        try:
            from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine
            resumed = WorkflowStageEngine.resume_by_event(
                event_key=event_key,
                tenant_id=tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                context=payload,
            )
            if resumed:
                matched_count += len(resumed)
        except Exception:
            logger.exception("Error resuming waiting instances for event %s", event_key)

        # 6. Finalise event log status
        if matched_count > 0:
            event_log.status = 'consumed'
        else:
            # Either no subscriptions at all, or all were filtered_out/inactive
            event_log.status = 'ignored'

        event_log.save(update_fields=['status'])
        return event_log

    # ------------------------------------------------------------------ #
    # Registry validation                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def validate_registered_event(event_key):
        """
        Check whether event_key exists in the registry and is active.

        Returns (event_def, None) on success, (None, error_string) on failure.
        """
        event_def = WorkflowEventDefinition.objects.filter(
            event_key=event_key, is_active=True
        ).first()
        if not event_def:
            logger.warning("Unregistered or inactive event key received: %s", event_key)
            return None, f"Event '{event_key}' is not registered or is inactive"
        return event_def, None

    # ------------------------------------------------------------------ #
    # Subscription / mapping lookup                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def find_matching_workflows(tenant_id, event_def, payload):
        """
        Return list of (subscription, decision, reason) tuples.

        decision is one of: matched | filtered_out | inactive
        """
        subscriptions = WorkflowEventSubscription.objects.select_related('workflow').filter(
            event_definition=event_def,
            tenant_id=tenant_id,
        )

        results = []
        for sub in subscriptions:
            if not sub.is_active or not sub.workflow.is_active or sub.workflow.status != 'active':
                results.append((sub, 'inactive', 'Subscription or workflow is inactive'))
                continue

            is_match, reason, _ = WorkflowEventListener.evaluate_trigger_filters(
                sub.trigger_filters, payload
            )
            decision = 'matched' if is_match else 'filtered_out'
            results.append((sub, decision, reason))

        return results

    # ------------------------------------------------------------------ #
    # Filter evaluation                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def evaluate_trigger_filters(filters, payload):
        """
        Evaluate trigger_filters dict against the event payload.

        Supported operators (via filter key suffixes):
          key           → exact string equality
          key__gt       → numeric greater-than
          key__lt       → numeric less-than
          key__contains → substring

        Returns (is_match, reason, trace_dict).
        """
        if not filters:
            return True, "No filters defined", {}

        trace = {}
        for raw_key, expected in filters.items():
            parts = raw_key.rsplit('__', 1)
            field = parts[0]
            op = parts[1] if len(parts) == 2 else 'eq'

            actual = payload.get(field)
            trace[raw_key] = {'expected': expected, 'actual': actual, 'op': op}

            if op == 'eq' or op == '':
                if str(actual) != str(expected):
                    return False, f"Filter mismatch: {field} (expected={expected}, got={actual})", trace
            elif op == 'gt':
                try:
                    if not (float(actual) > float(expected)):
                        return False, f"Filter mismatch: {field} > {expected} (got={actual})", trace
                except (TypeError, ValueError):
                    return False, f"Filter type error on {field}", trace
            elif op == 'lt':
                try:
                    if not (float(actual) < float(expected)):
                        return False, f"Filter mismatch: {field} < {expected} (got={actual})", trace
                except (TypeError, ValueError):
                    return False, f"Filter type error on {field}", trace
            elif op == 'contains':
                if str(expected) not in str(actual or ''):
                    return False, f"Filter mismatch: {field} contains {expected}", trace

        return True, "All filters matched", trace

    # ------------------------------------------------------------------ #
    # Workflow instance creation                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def start_workflow_instances(tenant_id, workflow, entity_type, entity_id, payload):
        """Start a new WorkflowInstance for the given workflow."""
        instance = WorkflowExecutionEngine.start_workflow_instance(
            tenant_id=tenant_id,
            workflow_id=workflow.id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        logger.info(
            "Started workflow instance %s for workflow %s (entity=%s/%s)",
            instance.id,
            workflow.id,
            entity_type,
            entity_id,
        )
        return instance

    # ------------------------------------------------------------------ #
    # Audit / trace logging                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def log_event_match_result(event_log, workflow, decision, reason):
        """Record a WorkflowEventDebugTrace entry for one match decision."""
        if workflow is None and decision == 'invalid':
            # Log at event level only, no specific workflow to attach
            return
        if workflow is None:
            return
        WorkflowEventDebugTrace.objects.create(
            tenant_id=event_log.tenant_id,
            event_log=event_log,
            workflow=workflow,
            decision=decision,
            reason=reason,
        )

    # ------------------------------------------------------------------ #
    # Convenience alias (backwards compat with old listener interface)    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def listen_event(tenant_id, event_type, entity_type, entity_id, payload):
        """Alias for receive_event kept for backwards compatibility."""
        return WorkflowEventListener.receive_event(
            tenant_id=tenant_id,
            event_key=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
