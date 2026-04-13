from celery import shared_task
from apps.agencies.services import AgencyIntelligenceService


@shared_task(name='apps.agencies.refresh_agency_performance_scores_task')
def refresh_agency_performance_scores_task(tenant_id):
    """
    Background task to recalculate agency performance scores.
    Called when submissions occur or stage changes.
    """
    AgencyIntelligenceService.refresh_agency_performance_scores(tenant_id)
