from celery import shared_task

from apps.orchestration_center.constants.execution_statuses import FailureSeverity
from apps.orchestration_center.models import AIExecutionRequest, ExecutionFailure
from apps.orchestration_center.services.ai_execution_service import AIExecutionService
from apps.orchestration_center.services.audit_service import AuditService
from apps.orchestration_center.services.failure_service import FailureService
from apps.orchestration_center.services.provider_router import ProviderExecutionError


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def execute_ai_request(self, execution_request_id):
    try:
        request = AIExecutionService.execute_request_by_id(execution_request_id=execution_request_id)
        return {'execution_request_id': str(request.id), 'status': request.status}
    except AIExecutionRequest.DoesNotExist:
        return {'execution_request_id': str(execution_request_id), 'status': 'missing'}
    except ProviderExecutionError as exc:
        request = AIExecutionRequest.objects.filter(pk=execution_request_id).first()
        if not request:
            return {'execution_request_id': str(execution_request_id), 'status': 'missing'}
        if exc.retryable and request.retry_count < request.max_retries:
            AIExecutionService.queue_for_retry(request=request)
            try:
                raise self.retry(countdown=60 * max(1, request.retry_count))
            except self.MaxRetriesExceededError:
                pass
        dead_letter = FailureService.move_to_dead_letter(
            tenant_id=request.tenant_id,
            created_by=request.created_by,
            item_type='ai_execution',
            related_object_id=request.id,
            reason_code=exc.category,
            payload_snapshot_json=request.context_snapshot_json,
            notes=str(exc),
        )
        failure = ExecutionFailure.objects.filter(related_request_id=request.id).order_by('-created_at').first()
        if failure:
            failure.status = 'moved_to_dead_letter'
            failure.severity = FailureSeverity.HIGH
            failure.save(update_fields=['status', 'severity', 'updated_at'])
        AuditService.log(
            tenant_id=request.tenant_id,
            actor_id=request.created_by,
            actor_type='system',
            action_type='ai_execution.dead_lettered',
            target_type='dead_letter_item',
            target_id=dead_letter.id,
            metadata_json={'execution_request_id': str(request.id), 'reason': exc.category},
        )
        return {'execution_request_id': str(request.id), 'status': request.status, 'dead_letter_id': str(dead_letter.id)}
    except Exception as exc:
        request = AIExecutionRequest.objects.filter(pk=execution_request_id).first()
        if request:
            AIExecutionService.mark_failed(
                request=request,
                failure_category='worker_exception',
                failure_reason=str(exc),
                retryable=request.retry_count < request.max_retries,
            )
        return {'execution_request_id': str(execution_request_id), 'status': 'failed', 'error': str(exc)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def retry_ai_request(self, execution_request_id):
    request = AIExecutionRequest.objects.get(pk=execution_request_id)
    AIExecutionService.queue_for_retry(request=request)
    return execute_ai_request.delay(str(request.id)).id
