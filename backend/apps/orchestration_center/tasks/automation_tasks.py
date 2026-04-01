from celery import shared_task

from apps.orchestration_center.constants.execution_statuses import FailureSeverity
from apps.orchestration_center.models import AutomationExecutionRun, ExecutionFailure
from apps.orchestration_center.services.audit_service import AuditService
from apps.orchestration_center.services.automation_rule_service import AutomationRuleService
from apps.orchestration_center.services.failure_service import FailureService


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def execute_automation_rule(self, automation_run_id):
    try:
        run = AutomationRuleService.execute_run_by_id(automation_run_id=automation_run_id)
        return {'automation_run_id': str(run.id), 'status': run.status}
    except AutomationExecutionRun.DoesNotExist:
        return {'automation_run_id': str(automation_run_id), 'status': 'missing'}
    except Exception as exc:
        run = AutomationExecutionRun.objects.filter(pk=automation_run_id).first()
        if not run:
            return {'automation_run_id': str(automation_run_id), 'status': 'missing', 'error': str(exc)}
        retryable = run.retry_count < 2
        AutomationRuleService.mark_failed(
            run=run,
            failure_category='worker_exception',
            failure_reason=str(exc),
            retryable=retryable,
        )
        if retryable:
            AutomationRuleService.queue_for_retry(run=run)
            try:
                raise self.retry(countdown=60 * max(1, run.retry_count))
            except self.MaxRetriesExceededError:
                pass
        dead_letter = FailureService.move_to_dead_letter(
            tenant_id=run.tenant_id,
            created_by=run.created_by,
            item_type='automation_run',
            related_object_id=run.id,
            reason_code='worker_exception',
            payload_snapshot_json=run.trigger_payload_json,
            notes=str(exc),
        )
        failure = ExecutionFailure.objects.filter(related_run_id=run.id).order_by('-created_at').first()
        if failure:
            failure.status = 'moved_to_dead_letter'
            failure.severity = FailureSeverity.HIGH
            failure.save(update_fields=['status', 'severity', 'updated_at'])
        AuditService.log(
            tenant_id=run.tenant_id,
            actor_id=run.created_by,
            actor_type='system',
            action_type='automation_run.dead_lettered',
            target_type='dead_letter_item',
            target_id=dead_letter.id,
            metadata_json={'automation_run_id': str(run.id)},
        )
        return {'automation_run_id': str(run.id), 'status': run.status, 'dead_letter_id': str(dead_letter.id)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def retry_automation_run(self, automation_run_id):
    run = AutomationExecutionRun.objects.get(pk=automation_run_id)
    AutomationRuleService.queue_for_retry(run=run)
    return execute_automation_rule.delay(str(run.id)).id


@shared_task(bind=True)
def scheduled_automation_dispatch(self):
    completed_ids = AutomationRuleService.process_due_scheduled_actions()
    return {'status': 'dispatch_checked', 'completed_ids': completed_ids}
