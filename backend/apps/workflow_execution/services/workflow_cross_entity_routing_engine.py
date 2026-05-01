"""
WorkflowCrossEntityRoutingEngine
==================================
Orchestrates routing of workflow control across entities and actors:
  Company ↔ Agency ↔ Candidate ↔ Recruiter ↔ Hiring Manager ↔ HR ↔ HRMS

Architecture:
  1. determine_next_route()       — evaluate WorkflowRoutingRule against context
  2. create_entity_route()        — persist WorkflowEntityRoute hop
  3. assign_actor_for_stage()     — create WorkflowActorAssignment
  4. handoff_stage_control()      — create WorkflowHandoffCheckpoint + route
  5. validate_cross_entity_route() — tenant-safety check
  6. complete_handoff()           — mark checkpoint completed → continue workflow
  7. fail_handoff()               — mark checkpoint failed → fail or retry
  8. continue_after_handoff()     — advance instance post-handoff
  9. route_to_onboarding()        — shortcut: company → HR onboarding hop
  10. route_to_hrms()             — shortcut: onboarding → HRMS handoff

Integration with WorkflowStageEngine:
  The stage engine calls apply_routing_rules() after each stage completion.
  This method evaluates routing rules, creates actor assignments, and
  emits handoff checkpoints if needed — without blocking stage transitions.
"""
import logging
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowInstance,
    WorkflowStageExecution,
    WorkflowExecutionTimeline,
    WorkflowEntityRoute,
    WorkflowActorAssignment,
    WorkflowHandoffCheckpoint,
    WorkflowRoutingRule,
    WorkflowRouteTimelineLog,
)
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.workflow_execution.services.workflow_stage_engine import ConditionEvaluator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------#
# Allowed cross-entity routes per tenant safety rules                          #
# ---------------------------------------------------------------------------#
# Format: frozenset({from_entity_type, to_entity_type}) — both directions OK
ALLOWED_ROUTE_PAIRS = {
    frozenset({'company',        'agency'}),
    frozenset({'company',        'candidate'}),
    frozenset({'company',        'recruiter'}),
    frozenset({'company',        'hiring_manager'}),
    frozenset({'company',        'hr'}),
    frozenset({'company',        'onboarding'}),
    frozenset({'company',        'hrms'}),
    frozenset({'company',        'interviewer'}),
    frozenset({'company',        'panel'}),
    frozenset({'agency',         'candidate'}),
    frozenset({'agency',         'recruiter'}),
    frozenset({'recruiter',      'hiring_manager'}),
    frozenset({'hiring_manager', 'hr'}),
    frozenset({'hr',             'onboarding'}),
    frozenset({'onboarding',     'hrms'}),
}


def _route_log(instance, action, from_actor='', to_actor='', reason='', route=None, metadata=None):
    route_log = WorkflowRouteTimelineLog.objects.create(
        tenant_id=instance.tenant_id,
        workflow_instance=instance,
        route=route,
        action=action,
        from_actor=from_actor,
        to_actor=to_actor,
        reason=reason,
        metadata=metadata or {},
    )
    WorkflowInstanceTracker._timeline(
        instance=instance,
        event_type='routing',
        event_label=action,
        actor_type='system',
        payload={
            'from_actor': from_actor,
            'to_actor': to_actor,
            'reason': reason,
            'route_log_id': str(route_log.id),
            **(metadata or {}),
        },
    )
    from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine

    lower = action.lower()
    entry_type = 'routing_started'
    if 'completed' in lower or 'created' in lower:
        entry_type = 'routing_completed'
    WorkflowObservabilityEngine.create_timeline_entry(
        workflow_instance=instance,
        entry_type=entry_type,
        entry_label=action,
        entry_description=reason,
        actor_type='system',
        metadata={'from_actor': from_actor, 'to_actor': to_actor, **(metadata or {})},
    )
    WorkflowObservabilityEngine.create_trace(
        workflow_instance=instance,
        trace_key='routing',
        trace_type='routing',
        source_module='workflow_cross_entity_routing_engine',
        source_id=str(route.id) if route else '',
        trace_message=action,
        severity='info',
        metadata={'from_actor': from_actor, 'to_actor': to_actor, 'reason': reason, **(metadata or {})},
    )
    WorkflowObservabilityEngine.record_metric(
        workflow_instance=instance,
        metric_name='handoff_count',
        metric_value=1,
        metric_type='handoff_count',
        metadata={'from_actor': from_actor, 'to_actor': to_actor},
    )


def _timeline(instance, action, actor='system', metadata=None):
    WorkflowExecutionTimeline.objects.create(
        tenant_id=instance.tenant_id,
        workflow_instance=instance,
        action=action,
        actor=actor,
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------#
# WorkflowCrossEntityRoutingEngine                                             #
# ---------------------------------------------------------------------------#

class WorkflowCrossEntityRoutingEngine:

    # ------------------------------------------------------------------ #
    # 1. determine_next_route                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def determine_next_route(instance, stage_id=None, context=None):
        """
        Evaluate WorkflowRoutingRule rows for this workflow+stage against context.

        Returns the first matching rule (WorkflowRoutingRule) or None.
        Evaluates stage-specific rules first (stage_id match), then global rules.
        """
        effective_context = dict(instance.context_data)
        if context:
            effective_context.update(context)

        rules = WorkflowRoutingRule.objects.filter(
            workflow_id=instance.workflow_id,
            is_active=True,
        ).order_by('priority')

        if stage_id:
            # Stage-specific rules first
            for rule in rules.filter(stage_id=stage_id):
                is_match, _, _ = ConditionEvaluator.evaluate(rule.condition_config, effective_context)
                if is_match:
                    return rule

        # Global rules (no stage_id restriction)
        for rule in rules.filter(stage_id__isnull=True):
            is_match, _, _ = ConditionEvaluator.evaluate(rule.condition_config, effective_context)
            if is_match:
                return rule

        return None

    # ------------------------------------------------------------------ #
    # 2. create_entity_route                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_entity_route(instance, from_entity_type, to_entity_type,
                            route_type='workflow_continuation', route_reason='',
                            from_entity_id=None, to_entity_id=None, stage_id=None):
        """
        Create a WorkflowEntityRoute record.
        Validates tenant safety before creating.
        Returns (route, error_str) — error_str is None on success.
        """
        is_valid, error = WorkflowCrossEntityRoutingEngine.validate_cross_entity_route(
            instance, from_entity_type, to_entity_type
        )
        if not is_valid:
            logger.warning(
                "Blocked invalid route %s→%s for instance %s: %s",
                from_entity_type, to_entity_type, instance.id, error,
            )
            _route_log(
                instance,
                action=f"Route blocked: {from_entity_type} → {to_entity_type}",
                from_actor=from_entity_type,
                to_actor=to_entity_type,
                reason=error,
            )
            return None, error

        route = WorkflowEntityRoute.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            from_entity_type=from_entity_type,
            from_entity_id=from_entity_id,
            to_entity_type=to_entity_type,
            to_entity_id=to_entity_id,
            route_type=route_type,
            route_reason=route_reason,
            status='active',
            stage_id=stage_id,
        )

        _route_log(
            instance,
            action=f"Route created: {from_entity_type} → {to_entity_type}",
            from_actor=from_entity_type,
            to_actor=to_entity_type,
            reason=route_reason,
            route=route,
        )
        _timeline(
            instance,
            action=f"Cross-entity route: {from_entity_type} → {to_entity_type} ({route_type})",
            metadata={'route_id': str(route.id), 'route_type': route_type},
        )

        return route, None

    # ------------------------------------------------------------------ #
    # 3. assign_actor_for_stage                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def assign_actor_for_stage(instance, stage_id, actor_type, actor_id=None,
                               assignment_type='responsible', notes=''):
        """
        Create a WorkflowActorAssignment for a stage.
        Revokes any existing 'responsible' assignment for the same stage before creating.
        """
        if assignment_type == 'responsible':
            # Revoke previous responsible assignee for this stage
            WorkflowActorAssignment.objects.filter(
                workflow_instance=instance,
                stage_id=stage_id,
                assignment_type='responsible',
                status='active',
            ).update(status='revoked')

        assignment = WorkflowActorAssignment.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_id=stage_id,
            actor_type=actor_type,
            actor_id=actor_id,
            assignment_type=assignment_type,
            status='active',
            notes=notes,
        )

        _route_log(
            instance,
            action=f"Actor assigned: {actor_type} ({assignment_type}) for stage",
            to_actor=actor_type,
            reason=notes,
        )
        WorkflowInstanceTracker._timeline(
            instance=instance,
            event_type='actor_changed',
            event_label=f"Actor assigned: {actor_type} ({assignment_type})",
            actor_type=actor_type,
            actor_id=actor_id,
            payload={'stage_id': str(stage_id), 'assignment_id': str(assignment.id), 'notes': notes},
        )
        return assignment

    # ------------------------------------------------------------------ #
    # 4. handoff_stage_control                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def handoff_stage_control(instance, stage_execution, from_entity, to_entity,
                              handoff_type, payload=None, expected_response_event='',
                              route_type='action_handoff', reason=''):
        """
        Create a WorkflowHandoffCheckpoint and a companion WorkflowEntityRoute.
        Does NOT pause the instance — caller decides whether to wait.
        Returns (handoff_checkpoint, entity_route).
        """
        route, error = WorkflowCrossEntityRoutingEngine.create_entity_route(
            instance,
            from_entity_type=from_entity,
            to_entity_type=to_entity,
            route_type=route_type,
            route_reason=reason,
            stage_id=stage_execution.stage_id if stage_execution else None,
        )
        if error:
            return None, None

        checkpoint = WorkflowHandoffCheckpoint.objects.create(
            tenant_id=instance.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_execution,
            handoff_from=from_entity,
            handoff_to=to_entity,
            handoff_type=handoff_type,
            payload=payload or {},
            expected_response_event=expected_response_event,
            status='pending',
        )

        _route_log(
            instance,
            action=f"Handoff created: {from_entity} → {to_entity} ({handoff_type})",
            from_actor=from_entity,
            to_actor=to_entity,
            reason=reason,
            route=route,
            metadata={'checkpoint_id': str(checkpoint.id), 'expected_event': expected_response_event},
        )
        return checkpoint, route

    # ------------------------------------------------------------------ #
    # 5. validate_cross_entity_route                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def validate_cross_entity_route(instance, from_entity_type, to_entity_type):
        """
        Validate that the from→to entity route is allowed.

        Rules:
          1. Same entity type is always allowed (intra-entity)
          2. The pair must be in ALLOWED_ROUTE_PAIRS
          3. Cannot route across different tenants (entity_id check handled externally)
        Returns (is_valid: bool, error_str: str|None).
        """
        if from_entity_type == to_entity_type:
            return True, None

        pair = frozenset({from_entity_type, to_entity_type})
        if pair not in ALLOWED_ROUTE_PAIRS:
            return False, (
                f"Cross-entity route from '{from_entity_type}' to '{to_entity_type}' "
                "is not permitted by routing rules."
            )

        return True, None

    # ------------------------------------------------------------------ #
    # 6. complete_handoff                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def complete_handoff(handoff_id, response_payload=None, triggered_by='system', context=None):
        """
        Mark a handoff checkpoint as completed and continue the workflow.
        """
        try:
            checkpoint = WorkflowHandoffCheckpoint.objects.select_related(
                'workflow_instance', 'stage_execution'
            ).get(id=handoff_id)
        except WorkflowHandoffCheckpoint.DoesNotExist:
            logger.error("complete_handoff: checkpoint %s not found", handoff_id)
            return None

        if checkpoint.status in ('completed', 'failed', 'expired'):
            return checkpoint

        checkpoint.complete(response_payload=response_payload)

        # Complete associated route
        route = checkpoint.workflow_instance.entity_routes.filter(
            stage_id=checkpoint.stage_execution.stage_id if checkpoint.stage_execution else None,
            status='active',
        ).first()
        if route:
            route.complete()

        _route_log(
            checkpoint.workflow_instance,
            action=f"Handoff completed: {checkpoint.handoff_from} → {checkpoint.handoff_to}",
            from_actor=checkpoint.handoff_from,
            to_actor=checkpoint.handoff_to,
            reason='Handoff response received',
            route=route,
        )

        WorkflowCrossEntityRoutingEngine.continue_after_handoff(
            checkpoint.workflow_instance, checkpoint, context=context, triggered_by=triggered_by
        )
        return checkpoint

    # ------------------------------------------------------------------ #
    # 7. fail_handoff                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def fail_handoff(handoff_id, reason='Handoff failed', triggered_by='system'):
        """
        Mark a handoff checkpoint as failed. Fails the associated route.
        Does NOT automatically fail the workflow — caller decides escalation.
        """
        try:
            checkpoint = WorkflowHandoffCheckpoint.objects.select_related(
                'workflow_instance'
            ).get(id=handoff_id)
        except WorkflowHandoffCheckpoint.DoesNotExist:
            return None

        checkpoint.fail(reason=reason)

        route = checkpoint.workflow_instance.entity_routes.filter(
            stage_id=checkpoint.stage_execution.stage_id if checkpoint.stage_execution else None,
            status='active',
        ).first()
        if route:
            route.fail(reason=reason)

        _route_log(
            checkpoint.workflow_instance,
            action=f"Handoff failed: {checkpoint.handoff_from} → {checkpoint.handoff_to}",
            from_actor=checkpoint.handoff_from,
            to_actor=checkpoint.handoff_to,
            reason=reason,
            route=route,
        )
        _timeline(
            checkpoint.workflow_instance,
            action=f"Handoff failed: {reason}",
            actor=triggered_by,
        )
        return checkpoint

    # ------------------------------------------------------------------ #
    # 8. continue_after_handoff                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def continue_after_handoff(instance, handoff_checkpoint, context=None, triggered_by='system'):
        """
        Resume the workflow instance after a handoff is completed.
        Merges response_payload into instance context, then resumes the stage engine.
        """
        if context or handoff_checkpoint.response_payload:
            merged = dict(instance.context_data)
            merged.update(handoff_checkpoint.response_payload or {})
            if context:
                merged.update(context)
            instance.context_data = merged
            instance.save(update_fields=['context_data', 'updated_at'])

        if instance.status == 'waiting':
            from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine
            WorkflowStageEngine.resume_instance(
                instance.id,
                triggered_by=triggered_by,
                context=context,
            )

    # ------------------------------------------------------------------ #
    # 9. route_to_onboarding                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def route_to_onboarding(instance, stage_id=None, hr_actor_id=None,
                            payload=None, triggered_by='system'):
        """
        Shortcut: create company → HR → onboarding route chain.
        Assigns HR actor to the stage and creates the handoff checkpoint.
        """
        # Company → HR route
        route, error = WorkflowCrossEntityRoutingEngine.create_entity_route(
            instance,
            from_entity_type='company',
            to_entity_type='hr',
            route_type='onboarding_handoff',
            route_reason='Offer accepted — routing to HR onboarding',
            stage_id=stage_id,
        )
        if error:
            return None

        # Assign HR actor
        if stage_id:
            WorkflowCrossEntityRoutingEngine.assign_actor_for_stage(
                instance,
                stage_id=stage_id,
                actor_type='hr',
                actor_id=hr_actor_id,
                assignment_type='responsible',
                notes='HR assigned for onboarding stage',
            )

        stage_exec = (
            instance.stage_executions.filter(stage_id=stage_id).last()
            if stage_id else None
        )

        checkpoint, _ = WorkflowCrossEntityRoutingEngine.handoff_stage_control(
            instance,
            stage_execution=stage_exec,
            from_entity='company',
            to_entity='onboarding',
            handoff_type='company_to_hr',
            payload=payload or instance.context_data,
            expected_response_event='onboarding_started',
            route_type='onboarding_handoff',
            reason='Onboarding handoff initiated',
        )

        _timeline(
            instance,
            action='Routed to HR Onboarding',
            actor=triggered_by,
            metadata={'route_id': str(route.id) if route else None,
                      'checkpoint_id': str(checkpoint.id) if checkpoint else None},
        )
        return checkpoint

    # ------------------------------------------------------------------ #
    # 10. route_to_hrms                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def route_to_hrms(instance, stage_id=None, hrms_payload=None, triggered_by='system'):
        """
        Shortcut: create onboarding → HRMS handoff.
        Represents the final system-to-system hop before workflow closes.
        """
        route, error = WorkflowCrossEntityRoutingEngine.create_entity_route(
            instance,
            from_entity_type='onboarding',
            to_entity_type='hrms',
            route_type='onboarding_handoff',
            route_reason='Onboarding complete — dispatching HRMS payload',
            stage_id=stage_id,
        )
        if error:
            return None

        stage_exec = (
            instance.stage_executions.filter(stage_id=stage_id).last()
            if stage_id else None
        )

        checkpoint, _ = WorkflowCrossEntityRoutingEngine.handoff_stage_control(
            instance,
            stage_execution=stage_exec,
            from_entity='onboarding',
            to_entity='hrms',
            handoff_type='workflow_to_hrms',
            payload=hrms_payload or instance.context_data,
            expected_response_event='hrms_handoff_ready',
            route_type='onboarding_handoff',
            reason='HRMS handoff dispatch',
        )

        _timeline(
            instance,
            action='HRMS handoff dispatched',
            actor=triggered_by,
            metadata={'checkpoint_id': str(checkpoint.id) if checkpoint else None},
        )
        return checkpoint

    # ------------------------------------------------------------------ #
    # apply_routing_rules — called by WorkflowStageEngine post-completion  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def apply_routing_rules(instance, stage_id, context=None):
        """
        Evaluate routing rules after a stage completes.
        Creates actor assignments and handoff checkpoints as needed.
        This is a non-blocking side-effect — it does not pause the workflow.
        """
        rule = WorkflowCrossEntityRoutingEngine.determine_next_route(
            instance, stage_id=stage_id, context=context
        )
        if not rule:
            return

        route_config = rule.route_config or {}
        assignment_type = route_config.get('assignment_type', 'responsible')
        handoff_type    = route_config.get('handoff_type', '')
        expected_event  = route_config.get('expected_response_event', '')

        # Create actor assignment
        WorkflowCrossEntityRoutingEngine.assign_actor_for_stage(
            instance,
            stage_id=stage_id,
            actor_type=rule.route_to_actor_type or rule.route_to_entity_type,
            assignment_type=assignment_type,
            notes=f"Assigned by routing rule: {rule.label or rule.id}",
        )

        # Create entity route
        route, _ = WorkflowCrossEntityRoutingEngine.create_entity_route(
            instance,
            from_entity_type=instance.entity_type if instance.entity_type in dict(
                __import__('apps.workflow_execution.models.routing', fromlist=['ENTITY_TYPE_CHOICES']).ENTITY_TYPE_CHOICES
            ) else 'company',
            to_entity_type=rule.route_to_entity_type,
            route_type='workflow_continuation',
            route_reason=f"Routing rule: {rule.label or str(rule.id)}",
            stage_id=stage_id,
        )

        # Create handoff checkpoint if needed
        if handoff_type and expected_event:
            stage_exec = instance.stage_executions.filter(stage_id=stage_id).last()
            WorkflowCrossEntityRoutingEngine.handoff_stage_control(
                instance,
                stage_execution=stage_exec,
                from_entity=instance.entity_type,
                to_entity=rule.route_to_entity_type,
                handoff_type=handoff_type,
                payload=context or {},
                expected_response_event=expected_event,
                reason=f"Auto-handoff via routing rule {rule.id}",
            )

    # ------------------------------------------------------------------ #
    # complete_handoff_by_event — called by event listener                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def complete_handoff_by_event(event_key, tenant_id, entity_id=None, payload=None):
        """
        Find all pending handoffs whose expected_response_event matches event_key
        and complete them.
        """
        qs = WorkflowHandoffCheckpoint.objects.filter(
            tenant_id=tenant_id,
            expected_response_event=event_key,
            status__in=['pending', 'delivered', 'acknowledged'],
        )
        if entity_id:
            qs = qs.filter(workflow_instance__entity_id=entity_id)

        completed = []
        for checkpoint in qs:
            try:
                WorkflowCrossEntityRoutingEngine.complete_handoff(
                    checkpoint.id, response_payload=payload or {}, triggered_by='event'
                )
                completed.append(checkpoint.id)
            except Exception:
                logger.exception("Failed to complete handoff %s via event %s", checkpoint.id, event_key)

        return completed
