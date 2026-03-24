"""
Candidate engagement signals.
These fire on pipeline events to keep engagement layer in sync.
All logic is additive — never blocks or modifies existing pipeline flow.
"""
from django.utils import timezone


def get_or_create_engagement(candidate_id, tenant_id, job_id, user):
    from apps.candidates.models import CandidateEngagement

    engagement = CandidateEngagement.objects.filter(
        candidate_id=candidate_id,
        tenant_id=tenant_id,
        job_id=job_id,
        is_active=True,
        is_deleted=False
    ).first()

    if not engagement:
        engagement = CandidateEngagement.objects.filter(
            candidate_id=candidate_id,
            tenant_id=tenant_id,
            job_id=job_id,
            is_deleted=False
        ).order_by('-started_at').first()

    if not engagement:
        engagement = CandidateEngagement.objects.create(
            tenant_id=tenant_id,
            candidate_id=candidate_id,
            job_id=job_id,
            engagement_type='job_sourced',
            stage='new',
            priority='warm',
            is_active=True,
            owner_user=user,
            created_by=user,
            last_activity_at=timezone.now()
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


def sync_engagement_stage(engagement, application_status, actor):
    STATUS_TO_STAGE = {
        'applied':      'new',
        'screening':    'contacted',
        'shortlisted':  'shortlisted',
        'interview':    'interviewing',
        'assessment':   'interviewing',
        'offer':        'offered',
        'joined':       'placed',
        'rejected':     'closed',
        'withdrawn':    'closed',
        'on_hold':      'follow_up',
    }
    new_stage = STATUS_TO_STAGE.get(application_status)
    if new_stage and engagement.stage != new_stage:
        old_stage = engagement.stage
        engagement.stage = new_stage
        engagement.last_activity_at = timezone.now()
        if new_stage in ('placed', 'closed'):
            engagement.is_active = False
            engagement.closed_at = timezone.now()
        engagement.save()
        return old_stage, new_stage
    return None, None
