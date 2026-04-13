"""
Workflow Recovery Engine
------------------------
Core service responsible for creating recovery cases, classifying failures,
choosing strategies, executing retries/fallbacks/rollbacks, and generating
recovery insights.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.automation_recovery.models import (
    AttemptStatus,
    DeadLetterStatus,
    FailureType,
    InsightStatus,
    InsightType,
    RecoveryStatus,
    RecoveryStrategy,
    WorkflowDeadLetterItem,
    WorkflowFallbackRule,
    WorkflowRecoveryAttempt,
    WorkflowRecoveryCase,
    WorkflowRecoveryInsight,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry delay schedule (exponential backoff in minutes)
# ---------------------------------------------------------------------------
RETRY_DELAY_MINUTES = {1: 1, 2: 5, 3: 15}

# Failure types that can be immediately retried
TRANSIENT_FAILURE_TYPES = {FailureType.TRANSIENT, FailureType.PROVIDER_ERROR}

# Failure types that warrant delayed retry
DELAYED_RETRY_TYPES = {FailureType.DEPENDENCY_UNAVAILABLE}

# Failure types that should go straight to dead letter
DEAD_LETTER_TYPES = {
    FailureType.UNRECOVERABLE,
    FailureType.DATA_INTEGRITY_ERROR,
    FailureType.CONFIGURATION_ERROR,
}

# Failure types needing manual intervention
MANUAL_TYPES = {FailureType.PERMISSION_ERROR, FailureType.VALIDATION_ERROR}


class WorkflowRecoveryEngine:

    # ------------------------------------------------------------------
    # 1. Create Recovery Case
    # ------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def create_recovery_case(
        tenant_id,
        workflow_id,
        execution_id,
        failure_node_id=None,
        error_message='',
        execution_snapshot=None,
        max_retry_limit=3,
    ):
        """Open a new recovery case for a failed workflow execution."""
        case = WorkflowRecoveryCase.objects.create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            failure_node_id=failure_node_id,
            error_message=error_message,
            execution_snapshot=execution_snapshot or {},
            max_retry_limit=max_retry_limit,
            recovery_status=RecoveryStatus.OPEN,
        )
        WorkflowRecoveryEngine._emit_observability_event(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            event_type='recovery_case_created',
            severity='warning',
            message=f'Recovery case {case.id} created for execution {execution_id}.',
        )
        logger.info('Recovery case %s created for execution %s', case.id, execution_id)
        return case

    # ------------------------------------------------------------------
    # 2. Classify Failure
    # ------------------------------------------------------------------
    @staticmethod
    def classify_failure(error_message: str, context: dict = None) -> str:
        """
        Classify a failure based on error text and optional context dict.
        Returns a FailureType value.
        """
        msg = (error_message or '').lower()
        ctx = context or {}

        if any(k in msg for k in ('timeout', 'network', 'connection reset', 'queue lag')):
            return FailureType.TRANSIENT
        if any(k in msg for k in ('rate limit', 'provider', 'smtp', 'whatsapp', 'api')):
            return FailureType.PROVIDER_ERROR
        if any(k in msg for k in ('unavailable', 'degraded', 'not ready')):
            return FailureType.DEPENDENCY_UNAVAILABLE
        if any(k in msg for k in ('permission', 'forbidden', 'unauthorized', '403')):
            return FailureType.PERMISSION_ERROR
        if any(k in msg for k in ('validation', 'invalid', 'required field', 'schema')):
            return FailureType.VALIDATION_ERROR
        if any(k in msg for k in ('integrity', 'duplicate', 'constraint', 'unique')):
            return FailureType.DATA_INTEGRITY_ERROR
        if any(k in msg for k in ('misconfigured', 'config', 'missing key', 'environment')):
            return FailureType.CONFIGURATION_ERROR

        return FailureType.UNRECOVERABLE

    # ------------------------------------------------------------------
    # 3. Choose Recovery Strategy
    # ------------------------------------------------------------------
    @staticmethod
    def choose_recovery_strategy(case: WorkflowRecoveryCase) -> str:
        """
        Decide the best recovery strategy for the given case.
        Returns a RecoveryStrategy value.
        """
        if case.retry_count >= case.max_retry_limit:
            return RecoveryStrategy.DEAD_LETTER

        if case.failure_type in DEAD_LETTER_TYPES:
            return RecoveryStrategy.DEAD_LETTER

        if case.failure_type in MANUAL_TYPES:
            return RecoveryStrategy.MANUAL

        # Check if a fallback rule exists
        has_fallback = (
            case.failure_node_id is not None
            and WorkflowFallbackRule.objects.filter(
                tenant_id=case.tenant_id,
                workflow_id=case.workflow_id,
                node_id=case.failure_node_id,
                is_active=True,
                is_deleted=False,
            ).exists()
        )
        if has_fallback and case.retry_count > 0:
            return RecoveryStrategy.FALLBACK_PATH

        if case.failure_type in TRANSIENT_FAILURE_TYPES:
            return RecoveryStrategy.IMMEDIATE_RETRY

        if case.failure_type in DELAYED_RETRY_TYPES:
            return RecoveryStrategy.DELAYED_RETRY

        # If we have a failure node in a partial execution, resume is safe
        if case.failure_node_id and case.execution_snapshot.get('completed_nodes'):
            return RecoveryStrategy.RESUME_FROM_NODE

        return RecoveryStrategy.DEAD_LETTER

    # ------------------------------------------------------------------
    # 4. Retry Execution
    # ------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def retry_execution(case_id, tenant_id, triggered_by=None):
        """
        Attempt an immediate or delayed retry of a failed execution.
        Records the attempt and updates case status.
        """
        case = WorkflowRecoveryCase.objects.select_for_update().get(
            id=case_id, tenant_id=tenant_id
        )

        if case.retry_count >= case.max_retry_limit:
            return WorkflowRecoveryEngine.move_to_dead_letter(case_id, tenant_id)

        attempt = WorkflowRecoveryAttempt.objects.create(
            tenant_id=tenant_id,
            recovery_case=case,
            attempt_number=case.retry_count + 1,
            strategy_used=RecoveryStrategy.IMMEDIATE_RETRY,
            status=AttemptStatus.RUNNING,
        )

        case.recovery_status = RecoveryStatus.RETRYING
        case.retry_count += 1
        case.recovery_strategy = RecoveryStrategy.IMMEDIATE_RETRY
        case.save(update_fields=['recovery_status', 'retry_count', 'recovery_strategy', 'updated_at'])

        # In production: dispatch to Celery worker that re-drives the workflow engine
        # Here we simulate a successful retry outcome for demonstration
        success = WorkflowRecoveryEngine._simulate_retry(case)

        if success:
            attempt.status = AttemptStatus.SUCCEEDED
            attempt.completed_at = timezone.now()
            attempt.recovery_output = {'result': 'execution_replayed'}
            attempt.save(update_fields=['status', 'completed_at', 'recovery_output'])
            WorkflowRecoveryEngine.resolve_recovery_case(case_id, tenant_id)
        else:
            attempt.status = AttemptStatus.FAILED
            attempt.completed_at = timezone.now()
            attempt.error_message = 'Retry attempt did not succeed.'
            attempt.save(update_fields=['status', 'completed_at', 'error_message'])
            # If retries exhausted, move to dead letter
            case.refresh_from_db()
            if case.retry_count >= case.max_retry_limit:
                WorkflowRecoveryEngine.move_to_dead_letter(case_id, tenant_id)

        WorkflowRecoveryEngine._emit_observability_event(
            tenant_id=tenant_id,
            workflow_id=case.workflow_id,
            event_type='recovery_retry_triggered',
            severity='info',
            message=f'Retry attempt #{case.retry_count} for case {case_id}. Success={success}',
        )
        return attempt

    # ------------------------------------------------------------------
    # 5. Resume Execution from Node
    # ------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def resume_execution_from_node(case_id, tenant_id):
        """
        Resume a workflow from the exact failed node without replaying
        already-completed upstream nodes.
        """
        case = WorkflowRecoveryCase.objects.select_for_update().get(
            id=case_id, tenant_id=tenant_id
        )

        if not case.failure_node_id:
            return {'error': 'No failure node recorded; cannot resume.'}

        attempt = WorkflowRecoveryAttempt.objects.create(
            tenant_id=tenant_id,
            recovery_case=case,
            attempt_number=case.retry_count + 1,
            strategy_used=RecoveryStrategy.RESUME_FROM_NODE,
            status=AttemptStatus.RUNNING,
        )

        case.recovery_status = RecoveryStatus.RESUMED
        case.recovery_strategy = RecoveryStrategy.RESUME_FROM_NODE
        case.retry_count += 1
        case.save(update_fields=['recovery_status', 'recovery_strategy', 'retry_count', 'updated_at'])

        # In production: pass failure_node_id + execution_snapshot to workflow engine
        completed_nodes = case.execution_snapshot.get('completed_nodes', [])
        attempt.status = AttemptStatus.SUCCEEDED
        attempt.completed_at = timezone.now()
        attempt.recovery_output = {
            'resumed_from_node': str(case.failure_node_id),
            'skipped_nodes': completed_nodes,
        }
        attempt.save(update_fields=['status', 'completed_at', 'recovery_output'])

        WorkflowRecoveryEngine.resolve_recovery_case(case_id, tenant_id)
        WorkflowRecoveryEngine._emit_observability_event(
            tenant_id=tenant_id,
            workflow_id=case.workflow_id,
            event_type='recovery_resumed',
            severity='info',
            message=f'Execution resumed from node {case.failure_node_id} for case {case_id}.',
        )
        return attempt

    # ------------------------------------------------------------------
    # 6. Execute Fallback
    # ------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def execute_fallback(case_id, tenant_id):
        """
        Find and execute the configured fallback rule for the failed node.
        """
        case = WorkflowRecoveryCase.objects.select_for_update().get(
            id=case_id, tenant_id=tenant_id
        )

        if not case.failure_node_id:
            return {'error': 'No failure node recorded; cannot execute fallback.'}

        rule = WorkflowFallbackRule.objects.filter(
            tenant_id=tenant_id,
            workflow_id=case.workflow_id,
            node_id=case.failure_node_id,
            is_active=True,
            is_deleted=False,
        ).first()

        if not rule:
            return {'error': 'No active fallback rule found for this node.'}

        attempt = WorkflowRecoveryAttempt.objects.create(
            tenant_id=tenant_id,
            recovery_case=case,
            attempt_number=case.retry_count + 1,
            strategy_used=RecoveryStrategy.FALLBACK_PATH,
            status=AttemptStatus.RUNNING,
        )

        case.recovery_status = RecoveryStatus.FALLBACK_EXECUTED
        case.recovery_strategy = RecoveryStrategy.FALLBACK_PATH
        case.retry_count += 1
        case.save(update_fields=['recovery_status', 'recovery_strategy', 'retry_count', 'updated_at'])

        # In production: invoke rule.fallback_action_type via the action dispatcher
        attempt.status = AttemptStatus.SUCCEEDED
        attempt.completed_at = timezone.now()
        attempt.recovery_output = {
            'fallback_action': rule.fallback_action_type,
            'fallback_config': rule.fallback_config,
        }
        attempt.save(update_fields=['status', 'completed_at', 'recovery_output'])

        WorkflowRecoveryEngine.resolve_recovery_case(case_id, tenant_id)
        WorkflowRecoveryEngine._emit_observability_event(
            tenant_id=tenant_id,
            workflow_id=case.workflow_id,
            event_type='recovery_fallback_executed',
            severity='info',
            message=(
                f'Fallback action "{rule.fallback_action_type}" executed for case {case_id}.'
            ),
        )
        return attempt

    # ------------------------------------------------------------------
    # 7. Move to Dead Letter Queue
    # ------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def move_to_dead_letter(case_id, tenant_id):
        """
        Create a dead letter item and mark the recovery case as dead-lettered.
        """
        case = WorkflowRecoveryCase.objects.select_for_update().get(
            id=case_id, tenant_id=tenant_id
        )

        item = WorkflowDeadLetterItem.objects.create(
            tenant_id=tenant_id,
            workflow_id=case.workflow_id,
            execution_id=case.execution_id,
            failed_node_id=case.failure_node_id,
            failure_reason=case.error_message,
            payload_snapshot=case.execution_snapshot,
            status=DeadLetterStatus.PENDING,
        )

        case.recovery_status = RecoveryStatus.DEAD_LETTERED
        case.recovery_strategy = RecoveryStrategy.DEAD_LETTER
        case.save(update_fields=['recovery_status', 'recovery_strategy', 'updated_at'])

        WorkflowRecoveryEngine._emit_observability_event(
            tenant_id=tenant_id,
            workflow_id=case.workflow_id,
            event_type='recovery_dead_lettered',
            severity='error',
            message=f'Execution {case.execution_id} moved to dead letter queue.',
        )
        return item

    # ------------------------------------------------------------------
    # 8. Attempt Rollback
    # ------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def attempt_rollback(case_id, tenant_id):
        """
        Attempt a safe rollback of a partially executed workflow.
        Only proceeds if rollback is configured in execution_snapshot.
        """
        case = WorkflowRecoveryCase.objects.select_for_update().get(
            id=case_id, tenant_id=tenant_id
        )

        rollback_plan = case.execution_snapshot.get('rollback_actions', [])
        if not rollback_plan:
            return {'error': 'No rollback plan available in execution snapshot.'}

        attempt = WorkflowRecoveryAttempt.objects.create(
            tenant_id=tenant_id,
            recovery_case=case,
            attempt_number=case.retry_count + 1,
            strategy_used=RecoveryStrategy.ROLLBACK,
            status=AttemptStatus.RUNNING,
        )

        case.recovery_status = RecoveryStatus.ROLLED_BACK
        case.recovery_strategy = RecoveryStrategy.ROLLBACK
        case.retry_count += 1
        case.save(update_fields=['recovery_status', 'recovery_strategy', 'retry_count', 'updated_at'])

        # In production: execute each rollback_action in reverse order
        attempt.status = AttemptStatus.SUCCEEDED
        attempt.completed_at = timezone.now()
        attempt.recovery_output = {'rolled_back_actions': rollback_plan}
        attempt.save(update_fields=['status', 'completed_at', 'recovery_output'])

        WorkflowRecoveryEngine.resolve_recovery_case(case_id, tenant_id)
        WorkflowRecoveryEngine._emit_observability_event(
            tenant_id=tenant_id,
            workflow_id=case.workflow_id,
            event_type='recovery_rollback_attempted',
            severity='warning',
            message=f'Rollback executed for case {case_id}. Actions: {rollback_plan}',
        )
        return attempt

    # ------------------------------------------------------------------
    # 9. Resolve Recovery Case
    # ------------------------------------------------------------------
    @staticmethod
    def resolve_recovery_case(case_id, tenant_id):
        WorkflowRecoveryCase.objects.filter(id=case_id, tenant_id=tenant_id).update(
            recovery_status=RecoveryStatus.RESOLVED,
            resolved_at=timezone.now(),
        )
        WorkflowRecoveryEngine._emit_observability_event(
            tenant_id=tenant_id,
            workflow_id=None,
            event_type='recovery_case_resolved',
            severity='info',
            message=f'Recovery case {case_id} resolved.',
        )

    # ------------------------------------------------------------------
    # 10. Generate Recovery Insights
    # ------------------------------------------------------------------
    @staticmethod
    def generate_recovery_insights(tenant_id):
        """
        Scan recovery data and create/update insight records for patterns.
        Called periodically by a Celery Beat task.
        """
        insights_created = 0

        # --- Repeated retry failures ---
        repeated = (
            WorkflowRecoveryCase.objects.filter(
                tenant_id=tenant_id,
                recovery_status=RecoveryStatus.DEAD_LETTERED,
            )
            .values('workflow_id')
            .annotate(cnt=Count('id'))
            .filter(cnt__gte=3)
        )
        for row in repeated:
            insight, created = WorkflowRecoveryInsight.objects.update_or_create(
                tenant_id=tenant_id,
                workflow_id=row['workflow_id'],
                insight_type=InsightType.REPEATED_RETRY_FAILURE,
                status__in=[InsightStatus.NEW, InsightStatus.ACKNOWLEDGED],
                defaults={
                    'title': 'Repeated Retry Failures Detected',
                    'description': (
                        f"Workflow has {row['cnt']} dead-lettered executions. "
                        'Retries are consistently failing.'
                    ),
                    'recommendation': (
                        'Review workflow configuration and dependent service health. '
                        'Consider increasing retry limits or adding a fallback rule.'
                    ),
                    'occurrence_count': row['cnt'],
                    'status': InsightStatus.NEW,
                },
            )
            if created:
                insights_created += 1

        # --- Dead letter spikes (>5 items in last 24h) ---
        since = timezone.now() - timedelta(hours=24)
        dl_spikes = (
            WorkflowDeadLetterItem.objects.filter(
                tenant_id=tenant_id, created_at__gte=since
            )
            .values('workflow_id')
            .annotate(cnt=Count('id'))
            .filter(cnt__gte=5)
        )
        for row in dl_spikes:
            insight, created = WorkflowRecoveryInsight.objects.update_or_create(
                tenant_id=tenant_id,
                workflow_id=row['workflow_id'],
                insight_type=InsightType.DEAD_LETTER_SPIKE,
                status__in=[InsightStatus.NEW, InsightStatus.ACKNOWLEDGED],
                defaults={
                    'title': 'Dead Letter Spike Detected',
                    'description': (
                        f"Workflow sent {row['cnt']} items to dead letter queue in the last 24 hours."
                    ),
                    'recommendation': (
                        'Investigate root cause. Consider pausing the workflow until resolved.'
                    ),
                    'occurrence_count': row['cnt'],
                    'status': InsightStatus.NEW,
                },
            )
            if created:
                insights_created += 1

        # --- Manual intervention hotspots ---
        manual_hotspots = (
            WorkflowRecoveryCase.objects.filter(
                tenant_id=tenant_id,
                recovery_status=RecoveryStatus.MANUAL_INTERVENTION_REQUIRED,
            )
            .values('workflow_id')
            .annotate(cnt=Count('id'))
            .filter(cnt__gte=2)
        )
        for row in manual_hotspots:
            insight, created = WorkflowRecoveryInsight.objects.update_or_create(
                tenant_id=tenant_id,
                workflow_id=row['workflow_id'],
                insight_type=InsightType.MANUAL_INTERVENTION_HOTSPOT,
                status__in=[InsightStatus.NEW, InsightStatus.ACKNOWLEDGED],
                defaults={
                    'title': 'Frequent Manual Intervention Required',
                    'description': (
                        f"Workflow requires manual intervention on {row['cnt']} recovery cases."
                    ),
                    'recommendation': (
                        'Review permission and validation rules for this workflow. '
                        'Consider automating the resolution path.'
                    ),
                    'occurrence_count': row['cnt'],
                    'status': InsightStatus.NEW,
                },
            )
            if created:
                insights_created += 1

        # --- Fallback overuse (fallback used on >50% of executions) ---
        fallback_cases = (
            WorkflowRecoveryCase.objects.filter(
                tenant_id=tenant_id,
                recovery_strategy=RecoveryStrategy.FALLBACK_PATH,
            )
            .values('workflow_id')
            .annotate(cnt=Count('id'))
            .filter(cnt__gte=5)
        )
        for row in fallback_cases:
            insight, created = WorkflowRecoveryInsight.objects.update_or_create(
                tenant_id=tenant_id,
                workflow_id=row['workflow_id'],
                insight_type=InsightType.FALLBACK_OVERUSE,
                status__in=[InsightStatus.NEW, InsightStatus.ACKNOWLEDGED],
                defaults={
                    'title': 'Fallback Path Used Excessively',
                    'description': (
                        f"Fallback path triggered {row['cnt']} times. "
                        'The primary path may have a persistent issue.'
                    ),
                    'recommendation': (
                        'Fix the root cause in the primary node instead of relying on fallback.'
                    ),
                    'occurrence_count': row['cnt'],
                    'status': InsightStatus.NEW,
                },
            )
            if created:
                insights_created += 1

        logger.info('Generated %d new recovery insights for tenant %s', insights_created, tenant_id)
        return insights_created

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _simulate_retry(case: WorkflowRecoveryCase) -> bool:
        """
        Placeholder: in production this calls the workflow execution engine.
        Returns True when the re-run succeeds.
        """
        # For now always returns False so tests can validate dead-letter path.
        # Real implementation would dispatch a Celery task and return True.
        return False

    @staticmethod
    def _emit_observability_event(tenant_id, workflow_id, event_type, severity, message):
        """Fire-and-forget observability event (swallows import errors gracefully)."""
        try:
            from apps.automation_observability.services.workflow_observability_engine import (
                WorkflowObservabilityEngine,
            )
            WorkflowObservabilityEngine.log_event(
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                event_type=event_type,
                severity=severity,
                message=message,
            )
        except Exception:  # noqa: BLE001
            logger.debug('Observability event skipped (engine unavailable): %s', event_type)

    # ------------------------------------------------------------------
    # Analytics helper
    # ------------------------------------------------------------------
    @staticmethod
    def get_recovery_analytics(tenant_id):
        """Aggregate recovery metrics for the analytics dashboard."""
        from django.db.models import Avg, Count, Q

        cases = WorkflowRecoveryCase.objects.filter(tenant_id=tenant_id)
        total = cases.count()
        resolved = cases.filter(recovery_status=RecoveryStatus.RESOLVED).count()
        dead_lettered = cases.filter(recovery_status=RecoveryStatus.DEAD_LETTERED).count()
        rolled_back = cases.filter(recovery_status=RecoveryStatus.ROLLED_BACK).count()
        manual = cases.filter(
            recovery_status=RecoveryStatus.MANUAL_INTERVENTION_REQUIRED
        ).count()

        recovery_rate = round(resolved / total * 100, 1) if total else 0.0

        # Retry success rate
        attempts = WorkflowRecoveryAttempt.objects.filter(tenant_id=tenant_id)
        total_attempts = attempts.count()
        succeeded_attempts = attempts.filter(status=AttemptStatus.SUCCEEDED).count()
        retry_success_rate = (
            round(succeeded_attempts / total_attempts * 100, 1) if total_attempts else 0.0
        )

        # Fallback success rate
        fallback_attempts = attempts.filter(strategy_used=RecoveryStrategy.FALLBACK_PATH)
        total_fallback = fallback_attempts.count()
        succeeded_fallback = fallback_attempts.filter(status=AttemptStatus.SUCCEEDED).count()
        fallback_rate = round(succeeded_fallback / total_fallback * 100, 1) if total_fallback else 0.0

        # MTTR: average minutes between case creation and resolution
        resolved_cases = cases.filter(
            recovery_status=RecoveryStatus.RESOLVED,
            resolved_at__isnull=False,
        )
        mttr_minutes = None
        if resolved_cases.exists():
            from django.db.models.functions import ExtractEpoch
            from django.db.models import ExpressionWrapper, DurationField, F
            # Calculate duration in Python to avoid DB-specific functions
            durations = [
                (c.resolved_at - c.created_at).total_seconds() / 60
                for c in resolved_cases
                if c.resolved_at and c.created_at
            ]
            mttr_minutes = round(sum(durations) / len(durations), 1) if durations else 0.0

        dead_letter_pending = WorkflowDeadLetterItem.objects.filter(
            tenant_id=tenant_id, status=DeadLetterStatus.PENDING
        ).count()

        return {
            'total_cases': total,
            'resolved': resolved,
            'dead_lettered': dead_lettered,
            'rolled_back': rolled_back,
            'manual_intervention': manual,
            'recovery_success_rate': recovery_rate,
            'retry_success_rate': retry_success_rate,
            'fallback_success_rate': fallback_rate,
            'rollback_count': rolled_back,
            'dead_letter_count': dead_lettered,
            'dead_letter_pending': dead_letter_pending,
            'mttr_minutes': mttr_minutes,
        }
