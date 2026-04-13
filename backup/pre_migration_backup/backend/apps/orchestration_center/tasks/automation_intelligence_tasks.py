from celery import shared_task

from apps.orchestration_center.models import AISuggestion
from apps.orchestration_center.services.audit_service import AuditService
from apps.orchestration_center.services.automation_intelligence_service import AutomationIntelligenceService


@shared_task(bind=True, max_retries=1, default_retry_delay=30)
def evaluate_suggestion_policy_task(self, suggestion_id):
    try:
        return AutomationIntelligenceService.evaluate_suggestion_policy(suggestion_id=suggestion_id)
    except AISuggestion.DoesNotExist:
        return {'status': 'missing', 'suggestion_id': str(suggestion_id)}
    except Exception as exc:
        suggestion = AISuggestion.objects.filter(pk=suggestion_id).only('id', 'tenant_id', 'created_by').first()
        if suggestion:
            AuditService.log(
                tenant_id=suggestion.tenant_id,
                actor_id=suggestion.created_by,
                actor_type='system',
                action_type='ai_suggestion.automation_policy_error',
                target_type='ai_suggestion',
                target_id=suggestion.id,
                metadata_json={'error': str(exc)},
            )
        return {'status': 'failed', 'suggestion_id': str(suggestion_id), 'error': str(exc)}


# ---------------------------------------------------------------------------
# Automation Learning Engine tasks
#
# Register these in your CELERY_BEAT_SCHEDULE (settings) to run periodically:
#
#   'automation-learning-hourly': {
#       'task': 'apps.orchestration_center.tasks.automation_intelligence_tasks.run_automation_learning_hourly',
#       'schedule': crontab(minute=0),  # top of every hour
#   },
#   'automation-learning-daily': {
#       'task': 'apps.orchestration_center.tasks.automation_intelligence_tasks.run_automation_learning_daily',
#       'schedule': crontab(hour=2, minute=0),  # 02:00 UTC daily
#   },
# ---------------------------------------------------------------------------

@shared_task(bind=True, name='run_automation_learning_hourly')
def run_automation_learning_hourly(self):
    """
    Lightweight hourly pass — evaluates all tenants for learning signals.
    Idempotency keys prevent duplicate suggestions within the same ISO week.
    """
    from apps.orchestration_center.services.automation_learning_service import AutomationLearningService
    try:
        return AutomationLearningService.run_for_all_tenants()
    except Exception as exc:
        return {'status': 'failed', 'error': str(exc)}


@shared_task(bind=True, name='run_automation_learning_daily')
def run_automation_learning_daily(self):
    """
    Daily comprehensive pass — same logic as hourly but intended to run at a
    low-traffic time (e.g. 02:00 UTC) for cost-effective scheduling.
    Idempotency keys ensure no double-suggestions if both tasks overlap.
    """
    from apps.orchestration_center.services.automation_learning_service import AutomationLearningService
    try:
        return AutomationLearningService.run_for_all_tenants()
    except Exception as exc:
        return {'status': 'failed', 'error': str(exc)}
