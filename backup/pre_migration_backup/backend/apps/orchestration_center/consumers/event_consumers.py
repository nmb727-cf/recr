from django.dispatch import receiver

from apps.core import events
from apps.orchestration_center.services.audit_service import AuditService
from apps.orchestration_center.services.runtime_event_service import IntelligenceRuntimeEventService


def _dispatch_safely(event_name: str, **kwargs):
    payload = {}
    try:
        payload = IntelligenceRuntimeEventService.build_payload(event_name=event_name, **kwargs)
        actor_id = payload.get('actor_user_id')
        IntelligenceRuntimeEventService.dispatch(
            event_name=event_name,
            actor_id=actor_id,
            payload=payload,
        )
    except Exception as exc:
        AuditService.log(
            tenant_id=payload.get('tenant_id'),
            actor_id=payload.get('actor_user_id'),
            actor_type='system',
            action_type='runtime_event.consumer_failed',
            target_type='platform_event',
            target_id=None,
            metadata_json={'event_name': event_name, 'error': str(exc)},
        )
        # Business flows must remain primary; orchestration failures stay non-blocking.
        return None


@receiver(events.job.created)
def on_job_created(sender, **kwargs):
    _dispatch_safely('job.created', **kwargs)


@receiver(events.job.published)
def on_job_published(sender, **kwargs):
    _dispatch_safely('job.published', **kwargs)


@receiver(events.application.created)
def on_application_created(sender, **kwargs):
    _dispatch_safely('application.created', **kwargs)


@receiver(events.application.stage_changed)
def on_application_stage_changed(sender, **kwargs):
    _dispatch_safely('application.stage_changed', **kwargs)


@receiver(events.application.shortlisted)
def on_application_shortlisted(sender, **kwargs):
    _dispatch_safely('application.shortlisted', **kwargs)


@receiver(events.interview.scheduled)
def on_interview_scheduled(sender, **kwargs):
    _dispatch_safely('interview.scheduled', **kwargs)


@receiver(events.interview.completed)
def on_interview_completed(sender, **kwargs):
    _dispatch_safely('interview.completed', **kwargs)


@receiver(events.interview.feedback_submitted)
def on_interview_feedback_submitted(sender, **kwargs):
    _dispatch_safely('interview.feedback_submitted', **kwargs)


@receiver(events.interview.decision_recorded)
def on_interview_decision_recorded(sender, **kwargs):
    _dispatch_safely('interview.decision_recorded', **kwargs)


@receiver(events.agency.candidate_submitted)
def on_agency_candidate_submitted(sender, **kwargs):
    _dispatch_safely('agency.candidate_submitted', **kwargs)
