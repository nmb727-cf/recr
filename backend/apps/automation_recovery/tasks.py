"""
Celery background tasks for the Automation Recovery Engine.
"""
import logging

from celery import shared_task
from django.utils import timezone

from apps.automation_recovery.models import (
    DeadLetterStatus,
    RecoveryStatus,
    WorkflowDeadLetterItem,
    WorkflowRecoveryCase,
)
from apps.automation_recovery.services.workflow_recovery_engine import WorkflowRecoveryEngine

logger = logging.getLogger(__name__)


@shared_task(name='automation_recovery.process_delayed_retries')
def process_delayed_retries():
    """
    Pick up recovery cases whose next_retry_at has passed and trigger retry.
    Runs every 5 minutes via Celery Beat.
    """
    now = timezone.now()
    due_cases = WorkflowRecoveryCase.objects.filter(
        recovery_status=RecoveryStatus.OPEN,
        next_retry_at__lte=now,
        is_deleted=False,
    ).values('id', 'tenant_id')

    retried = 0
    for row in due_cases:
        try:
            WorkflowRecoveryEngine.retry_execution(
                case_id=row['id'], tenant_id=row['tenant_id']
            )
            retried += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception('Delayed retry failed for case %s: %s', row['id'], exc)

    logger.info('process_delayed_retries: %d case(s) processed.', retried)
    return retried


@shared_task(name='automation_recovery.generate_recovery_insights')
def generate_recovery_insights():
    """
    Generate recovery insights for all tenants.
    Runs every hour via Celery Beat.
    """
    from apps.tenants.models import Client

    total = 0
    for tenant in Client.objects.filter(is_active=True):
        try:
            created = WorkflowRecoveryEngine.generate_recovery_insights(tenant_id=tenant.id)
            total += created
        except Exception as exc:  # noqa: BLE001
            logger.exception('Insight generation failed for tenant %s: %s', tenant.id, exc)

    logger.info('generate_recovery_insights: %d new insight(s) created.', total)
    return total


@shared_task(name='automation_recovery.recheck_degraded_dependencies')
def recheck_degraded_dependencies():
    """
    For recovery cases stuck in OPEN with a dependency_unavailable failure type,
    re-evaluate whether the dependency has recovered and trigger retry if so.
    Runs every 10 minutes via Celery Beat.
    """
    from apps.automation_recovery.models import FailureType
    from apps.automation_observability.models import DependencyStatus, WorkflowDependencyHealth

    cases = WorkflowRecoveryCase.objects.filter(
        recovery_status=RecoveryStatus.OPEN,
        failure_type=FailureType.DEPENDENCY_UNAVAILABLE,
        is_deleted=False,
    ).values('id', 'tenant_id')

    recovered = 0
    for row in cases:
        # Check if at least one dependency is healthy for this tenant
        any_healthy = WorkflowDependencyHealth.objects.filter(
            tenant_id=row['tenant_id'],
            status=DependencyStatus.HEALTHY,
        ).exists()
        if any_healthy:
            try:
                WorkflowRecoveryEngine.retry_execution(
                    case_id=row['id'], tenant_id=row['tenant_id']
                )
                recovered += 1
            except Exception as exc:  # noqa: BLE001
                logger.exception('Dependency recovery retry failed for case %s: %s', row['id'], exc)

    logger.info('recheck_degraded_dependencies: %d case(s) retried.', recovered)
    return recovered


@shared_task(name='automation_recovery.retry_approved_dead_letter_items')
def retry_approved_dead_letter_items():
    """
    Retry dead letter items that have been marked for retry by an operator.
    Runs every 15 minutes via Celery Beat.
    """
    items = WorkflowDeadLetterItem.objects.filter(
        status=DeadLetterStatus.RETRIED,
        is_deleted=False,
    ).values('id', 'tenant_id', 'workflow_id', 'execution_id', 'failed_node_id', 'failure_reason', 'payload_snapshot')

    retried = 0
    for item in items:
        try:
            # Create a fresh recovery case for the dead letter item
            case = WorkflowRecoveryEngine.create_recovery_case(
                tenant_id=item['tenant_id'],
                workflow_id=item['workflow_id'],
                execution_id=item['execution_id'],
                failure_node_id=item['failed_node_id'],
                error_message=item['failure_reason'],
                execution_snapshot=item['payload_snapshot'],
            )
            WorkflowRecoveryEngine.retry_execution(
                case_id=case.id, tenant_id=item['tenant_id']
            )
            WorkflowDeadLetterItem.objects.filter(id=item['id']).update(
                status=DeadLetterStatus.RESOLVED,
                resolved_at=timezone.now(),
            )
            retried += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception('Dead letter retry failed for item %s: %s', item['id'], exc)

    logger.info('retry_approved_dead_letter_items: %d item(s) retried.', retried)
    return retried
