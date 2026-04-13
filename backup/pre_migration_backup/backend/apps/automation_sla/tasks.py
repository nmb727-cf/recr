import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task
def check_sla_reminders():
    """
    Periodic task to send scheduled reminders.
    """
    from apps.automation_sla.models import WorkflowSLAReminder, SLAReminderStatus, SLAReminderType, SLAExecutionStatus
    
    now = timezone.now()
    pending_reminders = WorkflowSLAReminder.objects.filter(
        status=SLAReminderStatus.SCHEDULED,
        scheduled_at__lte=now
    ).select_related('sla_execution')

    sent_count = 0
    for reminder in pending_reminders:
        try:
            # Mock sending for now
            reminder.status = SLAReminderStatus.SENT
            reminder.sent_at = now
            reminder.save(update_fields=['status', 'sent_at'])
            
            # Update execution status if it was active
            if reminder.reminder_type == SLAReminderType.WARNING:
                exec = reminder.sla_execution
                if exec.current_status == SLAExecutionStatus.ACTIVE:
                    exec.current_status = SLAExecutionStatus.WARNING_DUE
                    exec.save(update_fields=['current_status', 'updated_at'])
            
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send SLA reminder {reminder.id}: {str(e)}")
            reminder.status = SLAReminderStatus.FAILED
            reminder.save(update_fields=['status'])

    return f"Sent {sent_count} reminders."

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
