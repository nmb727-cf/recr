"""
Candidate engagement signals.
These fire on pipeline events to keep engagement layer in sync.
All logic is additive — never blocks or modifies existing pipeline flow.
"""
from django.utils import timezone


def transition_candidate_to_job_track(candidate_id, tenant_id, job_id=None):
    """
    Move candidate out of general Active Work when they enter a job-specific track.
    This is intentional and explicit: general and job tracks must not run in parallel.
    """
    from apps.candidates.models import Candidate, CandidateEngagement

    now = timezone.now()
    CandidateEngagement.objects.filter(
        candidate_id=candidate_id,
        tenant_id=tenant_id,
        job__isnull=True,
        is_active=True,
        is_deleted=False,
    ).update(
        is_active=False,
        stage='nurture',
        closed_at=now,
        closure_reason='moved_to_job_workflow',
        last_activity_at=now,
    )

    candidate_updates = {
        'is_in_active_work': False,
        'last_activity_at': now,
        'candidate_pool': 'NONE',
        'candidate_state': 'JOB_ASSOCIATED',
        'is_general_pool_used': True,
    }
    if job_id:
        candidate_updates['active_job_id'] = job_id

    Candidate.objects.filter(
        id=candidate_id,
        tenant_id=tenant_id,
        is_deleted=False,
    ).update(**candidate_updates)


def get_or_create_engagement(candidate_id, tenant_id, job_id, user):
    from apps.candidates.models import CandidateEngagement

    # Priority 1 — find active engagement for this exact job
    engagement = CandidateEngagement.objects.filter(
        candidate_id=candidate_id,
        tenant_id=tenant_id,
        job_id=job_id,
        is_active=True,
        is_deleted=False,
    ).first()

    if engagement:
        transition_candidate_to_job_track(
            candidate_id=candidate_id,
            tenant_id=tenant_id,
            job_id=job_id,
        )
        return engagement

    # Priority 2 — no active job engagement, create a dedicated job-specific track
    engagement = CandidateEngagement.objects.create(
        tenant_id=tenant_id,
        candidate_id=candidate_id,
        job_id=job_id,
        engagement_type='job_sourced',
        stage='submitted',
        priority='warm',
        is_active=True,
        owner_user=user,
        created_by=user,
        last_activity_at=timezone.now(),
    )
    transition_candidate_to_job_track(
        candidate_id=candidate_id,
        tenant_id=tenant_id,
        job_id=job_id,
    )

    return engagement


def emit_timeline_event(tenant_id, candidate_id, engagement, event_type, actor, payload, source='system'):
    try:
        from apps.candidates.models import CandidateTimelineEvent
        CandidateTimelineEvent.objects.create(
            tenant_id=tenant_id,
            candidate_id=candidate_id,
            engagement=engagement,
            event_type=event_type,
            actor=actor,
            payload=payload,
            source=source
        )
    except Exception:
        pass


def sync_engagement_stage(engagement, application_status, actor, note=None):
    STATUS_TO_STAGE = {
        'applied':      'submitted',
        'screening':    'review',
        'shortlisted':  'review',
        'interview':    'interviewing',
        'assessment':   'interviewing',
        'offer':        'offered',
        'joined':       'joined',
        'rejected':     'rejected',
        'withdrawn':    'rejected',
        'on_hold':      'review',
    }
    new_stage = STATUS_TO_STAGE.get(application_status)
    if new_stage and engagement.stage != new_stage:
        old_stage = engagement.stage
        stage_note = note or f"System automation moved stage due to pipeline status '{application_status}'."
        engagement.stage = new_stage
        engagement.last_activity_at = timezone.now()
        if new_stage in ('joined', 'rejected'):
            engagement.is_active = False
            engagement.closed_at = timezone.now()
        engagement.save()
        emit_timeline_event(
            tenant_id=engagement.tenant_id,
            candidate_id=engagement.candidate_id,
            engagement=engagement,
            event_type='engagement.stage_changed',
            actor=actor,
            payload={
                'from_stage': old_stage,
                'to_stage': new_stage,
                'note': stage_note,
                'changed_by': str(actor.id) if actor else None,
                'changed_at': timezone.now().isoformat(),
            },
            source='system' if actor is None else 'user',
        )
        return old_stage, new_stage
    return None, None
