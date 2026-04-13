from django.utils import timezone

from apps.orchestration_center.constants.execution_statuses import ApprovalStatus
from apps.orchestration_center.models import ApprovalQueueItem


class ApprovalService:
    @staticmethod
    def approve(item, user_id, comment='', apply_now=True):
        if item.status != ApprovalStatus.PENDING:
            raise ValueError('Approval item is no longer pending.')
        item.status = ApprovalStatus.APPROVED
        item.decided_by_id = user_id
        item.decided_at = timezone.now()
        item.decision_comment = comment
        if apply_now:
            item.applied_by_id = user_id
            item.applied_at = timezone.now()
            update_fields = ['status', 'decided_by_id', 'decided_at', 'decision_comment', 'applied_by_id', 'applied_at', 'updated_at']
        else:
            update_fields = ['status', 'decided_by_id', 'decided_at', 'decision_comment', 'updated_at']
        item.save(update_fields=update_fields)
        return item

    @staticmethod
    def reject(item, user_id, comment=''):
        if item.status != ApprovalStatus.PENDING:
            raise ValueError('Approval item is no longer pending.')
        item.status = ApprovalStatus.REJECTED
        item.decided_by_id = user_id
        item.decided_at = timezone.now()
        item.decision_comment = comment
        item.save(update_fields=['status', 'decided_by_id', 'decided_at', 'decision_comment', 'updated_at'])
        return item
