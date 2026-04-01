from celery import shared_task

from apps.orchestration_center.models import DeadLetterItem
from apps.orchestration_center.services.audit_service import AuditService
from apps.orchestration_center.services.failure_service import FailureService
from apps.orchestration_center.tasks.ai_tasks import execute_ai_request
from apps.orchestration_center.tasks.automation_tasks import execute_automation_rule


@shared_task(bind=True)
def process_dead_letter_requeue(self, dead_letter_item_id):
    item = DeadLetterItem.objects.get(pk=dead_letter_item_id)
    FailureService.requeue_dead_letter(item=item)
    if item.item_type == 'ai_execution':
        execute_ai_request.delay(str(item.related_object_id))
    elif item.item_type == 'automation_run':
        execute_automation_rule.delay(str(item.related_object_id))
    AuditService.log(
        tenant_id=item.tenant_id,
        actor_id=item.created_by,
        actor_type='system',
        action_type='dead_letter.requeued',
        target_type='dead_letter_item',
        target_id=item.id,
        metadata_json={'item_type': item.item_type, 'related_object_id': str(item.related_object_id)},
    )
    return {'dead_letter_item_id': str(dead_letter_item_id), 'status': item.status}
