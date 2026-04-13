from datetime import datetime, time, timedelta

from django.utils import timezone

from apps.agencies.models import AgencyClientRelationship
from apps.core import events
from apps.jobs.models import JobRequisition
from apps.pipeline.models import PlacementGuarantee


def _to_date(dt):
    if not dt:
        return None
    if hasattr(dt, 'date'):
        return dt.date()
    return dt


def _resolve_guarantee_start_date(application, relationship):
    start_type = relationship.guarantee_start_type or 'joining_date'
    if start_type == 'offer_acceptance_date':
        return _to_date(application.offer_accepted_at) or timezone.now().date()
    if start_type == 'first_working_day':
        return application.joining_date or timezone.now().date()
    # joining_date default
    return _to_date(application.joined_at) or application.joining_date or timezone.now().date()


def _compute_guarantee_end_date(start_date, days):
    day_count = max(int(days or 0), 0)
    return start_date + timedelta(days=day_count)


def _active_guarantees_for_job(requisition_id):
    return PlacementGuarantee.objects.filter(
        requisition_id=requisition_id,
        status__in=['active', 'breached', 'replacement_requested', 'refund_requested'],
    )


def recalculate_job_hiring_state(requisition_id):
    try:
        job = JobRequisition.objects.get(id=requisition_id, is_deleted=False)
    except JobRequisition.DoesNotExist:
        return None

    has_active_guarantee = _active_guarantees_for_job(requisition_id).exists()

    update_fields = ['updated_at']
    if has_active_guarantee:
        latest = _active_guarantees_for_job(requisition_id).order_by('-guarantee_end_date').first()
        watch_until = None
        if latest:
            watch_until = timezone.make_aware(
                datetime.combine(latest.guarantee_end_date, time(23, 59, 59))
            )
        if job.headcount <= 0:
            job.status = 'in_guarantee_period'
            job.hiring_status = 'in_guarantee_period'
            job.guarantee_watch_until = watch_until
            update_fields.extend(['status', 'hiring_status', 'guarantee_watch_until'])
            events.job.guarantee_watch_started.send(sender=JobRequisition, requisition=job)
        else:
            job.status = 'active'
            job.hiring_status = 'active_hiring'
            job.guarantee_watch_until = watch_until
            update_fields.extend(['status', 'hiring_status', 'guarantee_watch_until'])
    else:
        if job.headcount <= 0:
            job.status = 'closed'
            job.hiring_status = 'fully_closed'
            if not job.closed_at:
                job.closed_at = timezone.now()
            update_fields.extend(['status', 'hiring_status', 'closed_at'])
            events.job.fully_closed.send(sender=JobRequisition, requisition=job)
        else:
            job.status = 'active'
            job.hiring_status = 'active_hiring'
            job.guarantee_watch_until = None
            update_fields.extend(['status', 'hiring_status', 'guarantee_watch_until'])
    job.save(update_fields=list(dict.fromkeys(update_fields)))
    return job


def start_guarantee_for_joined_placement(application):
    if not application.is_agency_submission or not application.agency_id:
        recalculate_job_hiring_state(application.requisition_id)
        return None

    relationship = AgencyClientRelationship.objects.filter(
        agency_tenant_id=application.agency_id,
        company_tenant_id=application.tenant_id,
        is_deleted=False,
    ).order_by('-updated_at').first()
    if not relationship:
        recalculate_job_hiring_state(application.requisition_id)
        return None

    if not relationship.replacement_guarantee_enabled:
        recalculate_job_hiring_state(application.requisition_id)
        return None
    if relationship.guarantee_resolution_type == 'no_guarantee':
        recalculate_job_hiring_state(application.requisition_id)
        return None

    start_date = _resolve_guarantee_start_date(application, relationship)
    end_date = _compute_guarantee_end_date(start_date, relationship.guarantee_period_days)

    guarantee, _ = PlacementGuarantee.objects.update_or_create(
        application_id=application.id,
        defaults={
            'candidate_id': application.candidate_id,
            'requisition_id': application.requisition_id,
            'agency_tenant_id': application.agency_id,
            'company_tenant_id': application.tenant_id,
            'agency_relationship_id': relationship.id,
            'guarantee_start_date': start_date,
            'guarantee_end_date': end_date,
            'guarantee_resolution_type': relationship.guarantee_resolution_type,
            'refund_mode': relationship.refund_mode or '',
            'refund_percentage': relationship.refund_percentage,
            'replacement_attempt_limit': relationship.replacement_attempt_limit or '1',
            'status': 'active',
            'metadata': {
                'guarantee_notes': relationship.guarantee_notes,
                'guarantee_start_type': relationship.guarantee_start_type,
            },
        },
    )

    events.placement.guarantee_started.send(
        sender=PlacementGuarantee,
        placement_guarantee=guarantee,
        application=application,
    )

    recalculate_job_hiring_state(application.requisition_id)
    return guarantee


def expire_due_placement_guarantees():
    today = timezone.now().date()
    expired_count = 0
    guarantees = PlacementGuarantee.objects.filter(
        status='active',
        guarantee_end_date__lte=today,
    )
    for guarantee in guarantees:
        guarantee.status = 'expired'
        guarantee.save(update_fields=['status', 'updated_at'])
        events.placement.guarantee_expired.send(
            sender=PlacementGuarantee,
            placement_guarantee=guarantee,
        )
        recalculate_job_hiring_state(guarantee.requisition_id)
        expired_count += 1
    return expired_count


def mark_guarantee_breached(*, placement_guarantee, reason='', requested_action='replacement'):
    placement_guarantee.status = 'breached'
    meta = dict(placement_guarantee.metadata or {})
    meta['breach_reason'] = reason
    meta['breach_requested_action'] = requested_action
    meta['breached_at'] = timezone.now().isoformat()
    placement_guarantee.metadata = meta
    placement_guarantee.save(update_fields=['status', 'metadata', 'updated_at'])

    if requested_action == 'refund':
        placement_guarantee.status = 'refund_requested'
        placement_guarantee.save(update_fields=['status', 'updated_at'])
    elif requested_action == 'replacement':
        placement_guarantee.status = 'replacement_requested'
        placement_guarantee.save(update_fields=['status', 'updated_at'])
        try:
            job = JobRequisition.objects.get(id=placement_guarantee.requisition_id, is_deleted=False)
            if job.status != 'active':
                job.status = 'active'
            job.hiring_status = 'replacement_required'
            job.save(update_fields=['status', 'hiring_status', 'updated_at'])
        except JobRequisition.DoesNotExist:
            pass

    events.placement.guarantee_breached.send(
        sender=PlacementGuarantee,
        placement_guarantee=placement_guarantee,
        reason=reason,
    )
    return placement_guarantee
