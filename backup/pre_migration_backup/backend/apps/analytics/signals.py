from __future__ import annotations

from django.dispatch import receiver

from apps.analytics.intelligence_substrate import IntelligenceEventTriggers
from apps.core import events


def _from_application(application):
    if not application:
        return None, None, None
    return application.tenant_id, application.requisition_id, application.candidate_id


def _from_requisition(requisition):
    if not requisition:
        return None, None
    return requisition.tenant_id, requisition.id


@receiver(events.candidate.created)
def on_candidate_created(sender, **kwargs):
    tenant_id = kwargs.get('tenant_id')
    candidate_id = kwargs.get('candidate_id')
    IntelligenceEventTriggers.handle_domain_event(
        event_name='candidate.created',
        tenant_id=tenant_id,
        candidate_id=candidate_id,
    )


@receiver(events.application.created)
def on_application_created(sender, **kwargs):
    app = kwargs.get('application')
    tenant_id, requisition_id, candidate_id = _from_application(app)
    IntelligenceEventTriggers.handle_domain_event(
        event_name='application.created',
        tenant_id=tenant_id,
        requisition_id=requisition_id,
        candidate_id=candidate_id,
    )


@receiver(events.application.stage_changed)
def on_application_stage_changed(sender, **kwargs):
    app = kwargs.get('application')
    tenant_id, requisition_id, candidate_id = _from_application(app)
    IntelligenceEventTriggers.handle_domain_event(
        event_name='application.stage_changed',
        tenant_id=tenant_id,
        requisition_id=requisition_id,
        candidate_id=candidate_id,
    )


@receiver(events.application.interviewed)
def on_application_interviewed(sender, **kwargs):
    app = kwargs.get('application')
    tenant_id, requisition_id, candidate_id = _from_application(app)
    IntelligenceEventTriggers.handle_domain_event(
        event_name='application.interviewed',
        tenant_id=tenant_id,
        requisition_id=requisition_id,
        candidate_id=candidate_id,
    )


@receiver(events.interview.completed)
def on_interview_completed(sender, **kwargs):
    interview = kwargs.get('interview')
    if not interview:
        return
    IntelligenceEventTriggers.handle_domain_event(
        event_name='interview.completed',
        tenant_id=interview.tenant_id,
        requisition_id=interview.requisition_id,
        candidate_id=interview.candidate_id,
    )


@receiver(events.job.created)
def on_job_created(sender, **kwargs):
    requisition = kwargs.get('requisition')
    tenant_id, requisition_id = _from_requisition(requisition)
    IntelligenceEventTriggers.handle_domain_event(
        event_name='job.created',
        tenant_id=tenant_id,
        requisition_id=requisition_id,
    )


@receiver(events.job.approved)
def on_job_approved(sender, **kwargs):
    requisition = kwargs.get('requisition')
    tenant_id, requisition_id = _from_requisition(requisition)
    IntelligenceEventTriggers.handle_domain_event(
        event_name='job.approved',
        tenant_id=tenant_id,
        requisition_id=requisition_id,
    )


@receiver(events.job.published)
def on_job_published(sender, **kwargs):
    requisition = kwargs.get('requisition')
    tenant_id, requisition_id = _from_requisition(requisition)
    IntelligenceEventTriggers.handle_domain_event(
        event_name='job.published',
        tenant_id=tenant_id,
        requisition_id=requisition_id,
    )


@receiver(events.agency.recruiter_assigned)
def on_agency_recruiter_assigned(sender, **kwargs):
    assignment = kwargs.get('assignment')
    if not assignment:
        return
    IntelligenceEventTriggers.handle_domain_event(
        event_name='agency.recruiter_assigned',
        tenant_id=assignment.tenant_id,
        requisition_id=getattr(assignment, 'requisition_id', None),
        recruiter_id=getattr(assignment, 'assigned_recruiter_id', None),
    )


@receiver(events.approval.requested)
def on_approval_requested(sender, **kwargs):
    IntelligenceEventTriggers.handle_domain_event(
        event_name='approval.requested',
        tenant_id=kwargs.get('tenant_id'),
    )
