from apps.automation.services import AutomationEngine
from apps.core import events


def _application_context(application):
    return {
        'application_id': str(application.id),
        'candidate_id': str(application.candidate_id),
        'requisition_id': str(application.requisition_id),
        'status': application.status,
        'match_score': float(application.match_score) if application.match_score is not None else None,
        'source': application.source,
    }


def _interview_context(interview):
    return {
        'interview_id': str(interview.id),
        'candidate_id': str(interview.candidate_id),
        'application_id': str(interview.application_id),
        'requisition_id': str(interview.requisition_id),
        'interview_type': interview.interview_type,
        'interview_round': interview.interview_round,
        'status': interview.status,
        'overall_score': float(interview.overall_score) if interview.overall_score is not None else None,
        'human_score': float(interview.human_score) if interview.human_score is not None else None,
    }


def on_application_created(sender, application, **kwargs):
    AutomationEngine.execute_trigger(
        trigger_event='candidate.applied',
        tenant_id=application.tenant_id,
        context=_application_context(application),
        entity_type='application',
        entity_id=application.id,
    )


def on_interview_scheduled(sender, interview, **kwargs):
    AutomationEngine.execute_trigger(
        trigger_event='interview.scheduled',
        tenant_id=interview.tenant_id,
        context=_interview_context(interview),
        entity_type='interview',
        entity_id=interview.id,
    )


def on_interview_completed(sender, interview, **kwargs):
    AutomationEngine.execute_trigger(
        trigger_event='interview.completed',
        tenant_id=interview.tenant_id,
        context=_interview_context(interview),
        entity_type='interview',
        entity_id=interview.id,
    )


def on_interview_cancelled(sender, interview, **kwargs):
    trigger = 'candidate.no_show' if interview.status == 'no_show' else 'interview.cancelled'
    AutomationEngine.execute_trigger(
        trigger_event=trigger,
        tenant_id=interview.tenant_id,
        context=_interview_context(interview),
        entity_type='interview',
        entity_id=interview.id,
    )


def on_feedback_submitted(sender, interview, feedback, **kwargs):
    panelist_id = getattr(feedback, 'panelist_id', None) or getattr(feedback, 'interviewer_id', None)
    context = _interview_context(interview)
    context.update({
        'feedback_id': str(feedback.id),
        'score': float(feedback.score) if feedback.score is not None else None,
        'recommendation': getattr(feedback, 'recommendation', ''),
        'panelist_id': str(panelist_id) if panelist_id else '',
    })
    AutomationEngine.execute_trigger(
        trigger_event='feedback.submitted',
        tenant_id=interview.tenant_id,
        context=context,
        entity_type='interview',
        entity_id=interview.id,
    )


def on_decision_made(sender, interview, decision, **kwargs):
    context = _interview_context(interview)
    context.update({
        'decision': decision.decision,
        'decision_source': decision.decision_source,
        'decision_mode': decision.decision_mode,
        'is_override': decision.is_override,
    })
    
    # ─── Built-in Job Binding Automation ───
    bind_interview_to_job_pipeline(interview, decision)
    
    AutomationEngine.execute_trigger(
        trigger_event='decision.made',
        tenant_id=interview.tenant_id,
        context=context,
        entity_type='interview',
        entity_id=interview.id,
    )


def bind_interview_to_job_pipeline(interview, decision):
    """
    Core binding logic: Phase 2 Job-Interview Completion.
    If binding is active and automation flags allow, move application status.
    """
    from apps.interviews.models import InterviewPackageBinding
    from apps.interviews.services import InterviewService
    from apps.pipeline.models import Application

    binding = InterviewPackageBinding.objects.filter(
        job_id=interview.requisition_id,
        is_deleted=False
    ).first()
    
    if not binding or not binding.automation_enabled:
        return

    # Check round-specific overrides
    round_config = binding.get_round_config(interview.interview_round)
    auto_pass = round_config.get('auto_pass_enabled', binding.auto_pass_enabled)
    auto_reject = round_config.get('auto_reject_enabled', binding.auto_reject_enabled)
    
    if decision.decision == 'next_round' and auto_pass:
        # Trigger next round
        InterviewService.trigger_next_round(
            tenant_id=interview.tenant_id,
            application_id=interview.application_id,
            job_id=interview.requisition_id,
            candidate_id=interview.candidate_id,
            current_round=interview.interview_round
        )
    elif decision.decision == 'reject' and auto_reject:
        # Reject application
        Application.objects.filter(id=interview.application_id).update(
            status='rejected',
            updated_at=timezone.now()
        )
    elif decision.decision == 'hold':
        # Move to hold
        Application.objects.filter(id=interview.application_id).update(
            status='on_hold',
            updated_at=timezone.now()
        )


events.application.created.connect(on_application_created, dispatch_uid='automation_application_created')
events.interview.scheduled.connect(on_interview_scheduled, dispatch_uid='automation_interview_scheduled')
events.interview.completed.connect(on_interview_completed, dispatch_uid='automation_interview_completed')
events.interview.cancelled.connect(on_interview_cancelled, dispatch_uid='automation_interview_cancelled')
events.interview.feedback_submitted.connect(on_feedback_submitted, dispatch_uid='automation_feedback_submitted')
events.interview.decision_recorded.connect(on_decision_made, dispatch_uid='automation_decision_made')
