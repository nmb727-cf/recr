from django.dispatch import receiver
from apps.core import events
from apps.agencies.services import AgencyIntelligenceService
from apps.agencies.tasks import refresh_agency_performance_scores_task


@receiver(events.job.published)
def on_job_published_agency_distribution(sender, **kwargs):
    """
    Agency Distribution Engine:
    Handles both automated intelligent distribution and manual assignments
    from job metadata when a requisition is published.
    """
    requisition = kwargs.get('requisition')
    if not requisition:
        return

    # 1. Trigger intelligent distribution logic if enabled
    if requisition.auto_distribute_to_agencies:
        AgencyIntelligenceService.perform_intelligent_distribution(
            requisition_id=requisition.id
        )
    
    # 2. Backfill: Handle manual agency assignments from metadata
    # This ensures agencies selected during Job Setup Studio are assigned.
    manual_agency_ids = requisition.metadata.get('agency_tenant_ids', [])
    if manual_agency_ids and isinstance(manual_agency_ids, list):
        from apps.agencies.services import AgencyAssignmentService
        for agency_id in manual_agency_ids:
            try:
                AgencyAssignmentService.assign_job_to_agency(
                    tenant_id=requisition.tenant_id,
                    requisition_id=requisition.id,
                    agency_tenant_id=agency_id,
                    notes="Assigned during job setup studio."
                )
            except Exception:
                # Fallback safely; don't block publishing if one assignment fails
                pass


@receiver(events.agency.candidate_submitted)
def on_agency_candidate_submitted_refresh(sender, **kwargs):
    """
    Refresh performance scores when a new candidate is submitted by an agency.
    """
    application = kwargs.get('application')
    if application:
        refresh_agency_performance_scores_task.delay(str(application.tenant_id))


@receiver(events.application.stage_changed)
def on_application_stage_changed_refresh(sender, **kwargs):
    """
    Refresh performance scores when an agency-submitted application changes stage
    (e.g., shortlisted, interviewed, joined).
    """
    application = kwargs.get('application')
    if application and application.is_agency_submission:
        refresh_agency_performance_scores_task.delay(str(application.tenant_id))
