"""
Workflow Execution Signal Connectors
=====================================
Connects Django signals from apps.core.events to WorkflowEventListener.receive_event().

Each handler translates the signal's kwargs into a standardised event payload and
calls receive_event(), which handles registry validation, subscription matching,
instance creation, and wait/resume logic.
"""
import logging
from datetime import timedelta

from django.utils import timezone

from apps.core import events
from apps.workflow_execution.models import WorkflowHumanTask, WorkflowInstance
from apps.workflow_execution.services.workflow_human_task_engine import WorkflowHumanTaskEngine
from apps.workflow_execution.services.workflow_event_listener import WorkflowEventListener

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Helper: safe event emission                                                  #
# --------------------------------------------------------------------------- #

def _emit(tenant_id, event_key, entity_type, entity_id, payload, source_module):
    try:
        WorkflowEventListener.receive_event(
            tenant_id=tenant_id,
            event_key=event_key,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            source_module=source_module,
        )
    except Exception:
        logger.exception("Workflow signal handler failed for event %s (entity=%s/%s)", event_key, entity_type, entity_id)


def _latest_instance_for_entity(*, tenant_id, entity_type, entity_id):
    return WorkflowInstance.objects.filter(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        status__in=['running', 'waiting', 'paused'],
        is_deleted=False,
    ).order_by('-created_at').first()


def _ensure_task(
    *,
    tenant_id,
    entity_type,
    entity_id,
    title,
    task_type,
    assigned_to_type='recruiter',
    priority='medium',
    due_hours=24,
    metadata=None,
):
    instance = _latest_instance_for_entity(tenant_id=tenant_id, entity_type=entity_type, entity_id=entity_id)
    if not instance:
        return None

    already_open = WorkflowHumanTask.objects.filter(
        tenant_id=tenant_id,
        workflow_instance=instance,
        title=title,
        status__in=['pending', 'in_progress'],
        is_deleted=False,
    ).exists()
    if already_open:
        return None

    due_at = timezone.now() + timedelta(hours=due_hours)
    task = WorkflowHumanTaskEngine.create_human_task(
        workflow_instance=instance,
        stage_execution=instance.stage_executions.order_by('-created_at').first(),
        task_type=task_type,
        title=title,
        assigned_to_type=assigned_to_type,
        priority=priority,
        due_at=due_at,
        wait_for_completion=False,
        metadata=metadata or {},
    )
    _emit(
        tenant_id=tenant_id,
        event_key='task_created',
        entity_type='task',
        entity_id=task.id,
        payload={'task_id': str(task.id), 'title': title, 'priority': priority, 'status': task.status},
        source_module='workflow_tasks',
    )
    return task


# --------------------------------------------------------------------------- #
# Job signals                                                                  #
# --------------------------------------------------------------------------- #

def on_job_created(sender, job, **kwargs):
    _emit(
        tenant_id=job.tenant_id,
        event_key='job_created',
        entity_type='job',
        entity_id=job.id,
        payload={
            'job_id': str(job.id),
            'title': getattr(job, 'title', ''),
            'department': getattr(job, 'department', ''),
            'status': getattr(job, 'status', ''),
        },
        source_module='jobs',
    )


def on_job_approved(sender, job, **kwargs):
    _emit(
        tenant_id=job.tenant_id,
        event_key='job_approved',
        entity_type='job',
        entity_id=job.id,
        payload={'job_id': str(job.id), 'status': getattr(job, 'status', '')},
        source_module='jobs',
    )


def on_job_published(sender, job, **kwargs):
    _emit(
        tenant_id=job.tenant_id,
        event_key='job_published',
        entity_type='job',
        entity_id=job.id,
        payload={'job_id': str(job.id), 'status': 'published'},
        source_module='jobs',
    )


# --------------------------------------------------------------------------- #
# Application / Candidate-applied signals                                      #
# --------------------------------------------------------------------------- #

def on_candidate_applied(sender, application, **kwargs):
    _emit(
        tenant_id=application.tenant_id,
        event_key='candidate_applied',
        entity_type='application',
        entity_id=application.id,
        payload={
            'application_id': str(application.id),
            'candidate_id': str(application.candidate_id),
            'job_id': str(application.requisition_id),
            'source': getattr(application, 'source', ''),
            'status': getattr(application, 'status', ''),
            'match_score': float(application.match_score) if getattr(application, 'match_score', None) is not None else None,
        },
        source_module='pipeline',
    )
    _emit(
        tenant_id=application.tenant_id,
        event_key='candidate_added',
        entity_type='application',
        entity_id=application.id,
        payload={
            'application_id': str(application.id),
            'candidate_id': str(application.candidate_id),
            'job_id': str(application.requisition_id),
            'source': getattr(application, 'source', ''),
            'status': getattr(application, 'status', ''),
        },
        source_module='pipeline',
    )
    _ensure_task(
        tenant_id=application.tenant_id,
        entity_type='application',
        entity_id=application.id,
        title='Recruiter review pending',
        task_type='review',
        assigned_to_type='recruiter',
        priority='medium',
        due_hours=24,
        metadata={'task_category': 'candidate_review'},
    )


def on_stage_changed(sender, application, **kwargs):
    _emit(
        tenant_id=application.tenant_id,
        event_key='stage_changed',
        entity_type='application',
        entity_id=application.id,
        payload={
            'application_id': str(application.id),
            'candidate_id': str(application.candidate_id),
            'stage': getattr(application, 'stage', ''),
            'status': getattr(application, 'status', ''),
        },
        source_module='pipeline',
    )


def on_candidate_shortlisted(sender, application, **kwargs):
    _emit(
        tenant_id=application.tenant_id,
        event_key='candidate_shortlisted',
        entity_type='application',
        entity_id=application.id,
        payload={
            'application_id': str(application.id),
            'candidate_id': str(application.candidate_id),
        },
        source_module='pipeline',
    )


def on_candidate_rejected(sender, application, **kwargs):
    _emit(
        tenant_id=application.tenant_id,
        event_key='candidate_rejected',
        entity_type='application',
        entity_id=application.id,
        payload={
            'application_id': str(application.id),
            'candidate_id': str(application.candidate_id),
        },
        source_module='pipeline',
    )


# --------------------------------------------------------------------------- #
# Agency signals                                                               #
# --------------------------------------------------------------------------- #

def on_agency_submission_created(sender, submission, **kwargs):
    _emit(
        tenant_id=getattr(submission, 'tenant_id', None),
        event_key='agency_submission_created',
        entity_type='agency_submission',
        entity_id=submission.id,
        payload={
            'submission_id': str(submission.id),
            'agency_id': str(getattr(submission, 'agency_id', '')),
            'candidate_id': str(getattr(submission, 'candidate_id', '')),
            'job_id': str(getattr(submission, 'job_id', '')),
            'source': 'agency',
        },
        source_module='agencies',
    )


# --------------------------------------------------------------------------- #
# Interview signals                                                            #
# --------------------------------------------------------------------------- #

def on_interview_completed(sender, interview, **kwargs):
    _emit(
        tenant_id=interview.tenant_id,
        event_key='interview_completed',
        entity_type='interview',
        entity_id=interview.id,
        payload={
            'interview_id': str(interview.id),
            'candidate_id': str(interview.candidate_id),
            'application_id': str(interview.application_id),
            'status': interview.status,
            'overall_score': float(interview.overall_score) if getattr(interview, 'overall_score', None) is not None else None,
        },
        source_module='interviews',
    )
    _ensure_task(
        tenant_id=interview.tenant_id,
        entity_type='application',
        entity_id=interview.application_id,
        title='Manual decision required after interview',
        task_type='decision',
        assigned_to_type='hiring_manager',
        priority='high',
        due_hours=24,
        metadata={'task_category': 'manual_decision', 'interview_id': str(interview.id)},
    )


def on_interview_feedback_submitted(sender, interview, feedback, **kwargs):
    _emit(
        tenant_id=interview.tenant_id,
        event_key='interview_feedback_submitted',
        entity_type='interview',
        entity_id=interview.id,
        payload={
            'interview_id': str(interview.id),
            'feedback_id': str(feedback.id),
            'candidate_id': str(interview.candidate_id),
            'recommendation': getattr(feedback, 'recommendation', ''),
            'score': float(feedback.score) if getattr(feedback, 'score', None) is not None else None,
        },
        source_module='interviews',
    )


def on_interview_scheduled(sender, interview, **kwargs):
    _emit(
        tenant_id=interview.tenant_id,
        event_key='interview_created',
        entity_type='interview',
        entity_id=interview.id,
        payload={
            'interview_id': str(interview.id),
            'candidate_id': str(interview.candidate_id),
            'application_id': str(interview.application_id),
            'status': interview.status,
        },
        source_module='interviews',
    )
    _emit(
        tenant_id=interview.tenant_id,
        event_key='interview_scheduled',
        entity_type='interview',
        entity_id=interview.id,
        payload={
            'interview_id': str(interview.id),
            'candidate_id': str(interview.candidate_id),
            'status': interview.status,
        },
        source_module='interviews',
    )


# --------------------------------------------------------------------------- #
# Offer signals                                                                #
# --------------------------------------------------------------------------- #

def on_offer_accepted(sender, application, **kwargs):
    _emit(
        tenant_id=application.tenant_id,
        event_key='offer_accepted',
        entity_type='application',
        entity_id=application.id,
        payload={
            'application_id': str(application.id),
            'candidate_id': str(application.candidate_id),
            'status': 'offer_accepted',
        },
        source_module='offers',
    )


def on_offer_rejected(sender, application, **kwargs):
    _emit(
        tenant_id=application.tenant_id,
        event_key='offer_rejected',
        entity_type='application',
        entity_id=application.id,
        payload={
            'application_id': str(application.id),
            'candidate_id': str(application.candidate_id),
            'status': 'offer_rejected',
        },
        source_module='offers',
    )


def on_offer_created(sender, offer=None, **kwargs):
    if offer is None:
        return
    _emit(
        tenant_id=offer.tenant_id,
        event_key='offer_created',
        entity_type='application',
        entity_id=offer.application_id,
        payload={
            'offer_id': str(offer.id),
            'application_id': str(offer.application_id),
            'candidate_id': str(offer.candidate_id),
            'status': offer.status,
        },
        source_module='offers',
    )


def on_offer_approved(sender, offer=None, **kwargs):
    if offer is None:
        return
    _emit(
        tenant_id=offer.tenant_id,
        event_key='offer_approved',
        entity_type='application',
        entity_id=offer.application_id,
        payload={
            'offer_id': str(offer.id),
            'application_id': str(offer.application_id),
            'candidate_id': str(offer.candidate_id),
            'status': offer.status,
        },
        source_module='offers',
    )


# --------------------------------------------------------------------------- #
# Onboarding signals                                                           #
# --------------------------------------------------------------------------- #

def on_onboarding_completed(sender, **kwargs):
    application = kwargs.get('application')
    if application is None:
        return
    _emit(
        tenant_id=application.tenant_id,
        event_key='onboarding_completed',
        entity_type='application',
        entity_id=application.id,
        payload={'application_id': str(application.id)},
        source_module='onboarding',
    )


def on_onboarding_started(sender, **kwargs):
    application = kwargs.get('application')
    if application is None:
        return
    _emit(
        tenant_id=application.tenant_id,
        event_key='onboarding_started',
        entity_type='application',
        entity_id=application.id,
        payload={'application_id': str(application.id)},
        source_module='onboarding',
    )
    _ensure_task(
        tenant_id=application.tenant_id,
        entity_type='application',
        entity_id=application.id,
        title='Onboarding checklist execution',
        task_type='confirmation',
        assigned_to_type='hr',
        priority='high',
        due_hours=72,
        metadata={'task_category': 'onboarding_checklist'},
    )


# --------------------------------------------------------------------------- #
# Signal wiring                                                                #
# --------------------------------------------------------------------------- #

def connect_signals():
    # Jobs
    events.job.created.connect(on_job_created, dispatch_uid='wf_exec_job_created')
    events.job.approved.connect(on_job_approved, dispatch_uid='wf_exec_job_approved')
    events.job.published.connect(on_job_published, dispatch_uid='wf_exec_job_published')

    # Applications / Candidate applied
    events.application.created.connect(on_candidate_applied, dispatch_uid='wf_exec_candidate_applied')
    events.application.stage_changed.connect(on_stage_changed, dispatch_uid='wf_exec_stage_changed')
    events.application.shortlisted.connect(on_candidate_shortlisted, dispatch_uid='wf_exec_candidate_shortlisted')
    events.application.rejected.connect(on_candidate_rejected, dispatch_uid='wf_exec_candidate_rejected')

    # Agency
    events.agency.candidate_submitted.connect(
        on_agency_submission_created, dispatch_uid='wf_exec_agency_submission_created'
    )

    # Interviews
    events.interview.completed.connect(on_interview_completed, dispatch_uid='wf_exec_interview_completed')
    events.interview.feedback_submitted.connect(
        on_interview_feedback_submitted, dispatch_uid='wf_exec_interview_feedback_submitted'
    )
    events.interview.scheduled.connect(on_interview_scheduled, dispatch_uid='wf_exec_interview_scheduled')

    # Offers
    events.offer.accepted.connect(on_offer_accepted, dispatch_uid='wf_exec_offer_accepted')
    events.offer.rejected.connect(on_offer_rejected, dispatch_uid='wf_exec_offer_rejected')
    events.offer.created.connect(on_offer_created, dispatch_uid='wf_exec_offer_created')
    events.offer.approved.connect(on_offer_approved, dispatch_uid='wf_exec_offer_approved')

    # Onboarding
    events.onboarding.started.connect(on_onboarding_started, dispatch_uid='wf_exec_onboarding_started')
    events.onboarding.completed.connect(on_onboarding_completed, dispatch_uid='wf_exec_onboarding_completed')
