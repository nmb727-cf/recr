import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)

@shared_task
def check_sla_reminders():
    """
    Periodic task to send scheduled reminders.
    """
    from apps.automation_sla.models import WorkflowSLAReminder, SLAReminderStatus, SLAReminderType, SLAExecutionStatus
    
    now = timezone.now()
    due_ids = list(
        WorkflowSLAReminder.objects.filter(
            status=SLAReminderStatus.SCHEDULED,
            scheduled_at__lte=now,
        ).values_list('id', flat=True)
    )

    sent_count = 0
    skipped_count = 0
    for reminder_id in due_ids:
        try:
            with transaction.atomic():
                reminder = (
                    WorkflowSLAReminder.objects.select_for_update()
                    .select_related('sla_execution')
                    .filter(id=reminder_id)
                    .first()
                )
                if not reminder or reminder.status != SLAReminderStatus.SCHEDULED:
                    continue

                execution = reminder.sla_execution
                if execution.current_status in (SLAExecutionStatus.COMPLETED, SLAExecutionStatus.CANCELLED):
                    reminder.status = SLAReminderStatus.SKIPPED
                    reminder.save(update_fields=['status', 'updated_at'])
                    skipped_count += 1
                    continue

                # Mock sending for now
                reminder.status = SLAReminderStatus.SENT
                reminder.sent_at = now
                reminder.save(update_fields=['status', 'sent_at', 'updated_at'])

                # Update execution status if it was active
                if reminder.reminder_type == SLAReminderType.WARNING:
                    if execution.current_status == SLAExecutionStatus.ACTIVE:
                        execution.current_status = SLAExecutionStatus.WARNING_DUE
                        execution.save(update_fields=['current_status', 'updated_at'])

                sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send SLA reminder {reminder_id}: {str(e)}")
            WorkflowSLAReminder.objects.filter(id=reminder_id, status=SLAReminderStatus.SCHEDULED).update(
                status=SLAReminderStatus.FAILED,
                updated_at=timezone.now(),
            )

    return f"Sent {sent_count} reminders, skipped {skipped_count} stale reminders."

@shared_task
def check_sla_breaches():
    """
    Periodic task to detect and process breached SLAs.
    """
    from apps.automation_sla.services.workflow_sla_engine import WorkflowSLAEngine
    breached_ids = WorkflowSLAEngine.detect_breach()
    return f"Detected {len(breached_ids)} breaches."

@shared_task
def run_sla_daily_maintenance():
    """
    Aggregates analytics and generates insights.
    Runs once a day.
    """
    from apps.tenants.models import Client
    from apps.automation_sla.services.workflow_sla_engine import WorkflowSLAEngine
    
    total_insights = 0
    for tenant in Client.objects.all():
        count = WorkflowSLAEngine.generate_breach_insights(tenant.id)
        total_insights += count
        
    return f"Generated {total_insights} breach insights across all tenants."
