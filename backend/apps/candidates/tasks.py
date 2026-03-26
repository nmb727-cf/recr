from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.candidates.protection import expire_protection_rights


@shared_task
def close_not_interested_engagements():
    """
    Finds all active engagements with stage=not_interested
    that were last updated more than 24 hours ago.
    Closes them by setting is_active=False and stage=closed.
    Emits a timeline event for each.
    """
    from apps.candidates.models import CandidateEngagement, CandidateTimelineEvent

    now = timezone.now()
    cutoff = now - timedelta(hours=24)

    engagements = CandidateEngagement.objects.filter(
        stage='not_interested',
        is_active=True,
        is_deleted=False,
        updated_at__lt=cutoff,
    )

    count = 0
    for engagement in engagements:
        engagement.stage = 'closed'
        engagement.is_active = False
        engagement.closed_at = now
        engagement.closure_reason = 'auto_closed_not_interested_24h'
        engagement.save(
            update_fields=[
                'stage',
                'is_active',
                'closed_at',
                'closure_reason',
                'updated_at',
            ]
        )

        CandidateTimelineEvent.objects.create(
            tenant_id=engagement.tenant_id,
            candidate_id=engagement.candidate_id,
            engagement=engagement,
            event_type='engagement.auto_closed',
            actor=None,
            payload={
                'reason': 'Not interested - auto closed after 24 hours',
                'previous_stage': 'not_interested',
                'new_stage': 'closed',
                'note': 'System automation moved stage due to stale not_interested timeout (24h).',
                'changed_by': 'system',
                'changed_at': now.isoformat(),
            },
            source='system',
        )
        count += 1

    return f"Auto-closed {count} not_interested engagements"


@shared_task
def expire_candidate_protection_rights():
    updated = expire_protection_rights(now_dt=timezone.now())
    return f"Expired/transitioned {updated} candidate protection rights"
