from django.utils import timezone

from apps.orchestration_center.constants.execution_statuses import DeadLetterStatus, FailureStatus
from apps.orchestration_center.models import DeadLetterItem, ExecutionFailure


class FailureService:
    @staticmethod
    def create_failure(**kwargs):
        return ExecutionFailure.objects.create(**kwargs)

    @staticmethod
    def move_to_dead_letter(*, tenant_id, created_by, item_type, related_object_id, reason_code, payload_snapshot_json=None, notes=''):
        return DeadLetterItem.objects.create(
            tenant_id=tenant_id,
            created_by=created_by,
            item_type=item_type,
            related_object_id=related_object_id,
            reason_code=reason_code,
            payload_snapshot_json=payload_snapshot_json or {},
            notes=notes,
        )

    @staticmethod
    def retry_failure(*, failure):
        if not failure.retryable:
            raise ValueError('This failure is not retryable.')
        if failure.status in {FailureStatus.RESOLVED, FailureStatus.IGNORED, FailureStatus.MOVED_TO_DEAD_LETTER}:
            raise ValueError('This failure is already terminal.')
        failure.status = FailureStatus.RETRYING
        failure.next_retry_at = timezone.now()
        failure.save(update_fields=['status', 'next_retry_at', 'updated_at'])
        return failure

    @staticmethod
    def resolve_failure(*, failure, user_id, resolution_note=''):
        if failure.status in {FailureStatus.RESOLVED, FailureStatus.IGNORED}:
            raise ValueError('Failure is already resolved.')
        failure.status = FailureStatus.RESOLVED
        failure.operator_notes = resolution_note or failure.operator_notes
        failure.resolved_by_id = user_id
        failure.resolved_at = timezone.now()
        failure.save(update_fields=['status', 'operator_notes', 'resolved_by_id', 'resolved_at', 'updated_at'])
        return failure

    @staticmethod
    def requeue_dead_letter(*, item):
        if item.status in {DeadLetterStatus.RESOLVED, DeadLetterStatus.IGNORED}:
            raise ValueError('Terminal dead-letter items cannot be requeued.')
        item.status = DeadLetterStatus.REQUEUED
        item.requeue_count += 1
        item.save(update_fields=['status', 'requeue_count', 'updated_at'])
        return item
