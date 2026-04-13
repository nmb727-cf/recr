from celery import shared_task
from django.utils import timezone
from apps.orchestration_center.models.workflow import Workflow
from apps.orchestration_center.services.automation_analytics_engine import AutomationAnalyticsEngine

@shared_task
def aggregate_workflow_snapshots_daily():
    # To be run by Celery Beat daily at 00:01
    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    workflows = Workflow.objects.filter(is_deleted=False)
    
    for wf in workflows:
        AutomationAnalyticsEngine.generate_workflow_snapshot(wf.tenant_id, wf.id, date=yesterday)
        AutomationAnalyticsEngine.calculate_impact_metrics(wf.tenant_id, wf.id)
        AutomationAnalyticsEngine.detect_failure_patterns(wf.tenant_id, wf.id)

@shared_task
def refresh_workflow_insights():
    # Periodic insight refresh
    pass
