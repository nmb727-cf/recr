"""
Pipeline hooks — called from pipeline views to sync engagement layer.
All functions catch exceptions internally — they never break the main flow.
"""
from django.utils import timezone


def on_application_created(application, user):
    try:
        from apps.candidates.signals import get_or_create_engagement, emit_timeline_event
        engagement = get_or_create_engagement(
            candidate_id=application.candidate_id,
            tenant_id=application.tenant_id,
            job_id=application.requisition_id,
            user=user
        )
        # If engagement was a lead, promote stage to submitted
        lead_stages = ['new', 'contacted', 'interested', 'follow_up', 'shortlisted']
        if engagement.stage in lead_stages:
            engagement.stage = 'submitted'
        engagement.last_activity_at = timezone.now()
        engagement.save()
        emit_timeline_event(
            tenant_id=application.tenant_id,
            candidate_id=application.candidate_id,
            engagement=engagement,
            event_type='application.created',
            actor=user,
            payload={
                'application_id': str(application.id),
                'requisition_id': str(application.requisition_id),
                'source': application.source or 'direct',
                'is_agency_submission': application.is_agency_submission,
            }
        )
    except Exception:
        pass


def on_application_stage_changed(application, from_status, to_status, user):
    try:
        from apps.candidates.models import CandidateEngagement
        from apps.candidates.signals import sync_engagement_stage, emit_timeline_event
        engagement = CandidateEngagement.objects.filter(
            candidate_id=application.candidate_id,
            tenant_id=application.tenant_id,
            job_id=application.requisition_id,
            is_deleted=False
        ).order_by('-started_at').first()
        if not engagement:
            return
        old_stage, new_stage = sync_engagement_stage(engagement, to_status, user)
        if old_stage and new_stage:
            emit_timeline_event(
                tenant_id=application.tenant_id,
                candidate_id=application.candidate_id,
                engagement=engagement,
                event_type='application.stage_changed',
                actor=user,
                payload={
                    'application_id': str(application.id),
                    'from_status': from_status,
                    'to_status': to_status,
                    'engagement_from_stage': old_stage,
                    'engagement_to_stage': new_stage,
                }
            )
    except Exception:
        pass


def on_application_rejected(application, reason, user):
    try:
        from apps.candidates.models import CandidateEngagement
        from apps.candidates.signals import emit_timeline_event
        engagement = CandidateEngagement.objects.filter(
            candidate_id=application.candidate_id,
            tenant_id=application.tenant_id,
            job_id=application.requisition_id,
            is_deleted=False,
            is_active=True
        ).first()
        if engagement:
            engagement.stage = 'lost'
            engagement.is_active = False
            engagement.closed_at = timezone.now()
            engagement.closure_reason = reason
            engagement.last_activity_at = timezone.now()
            engagement.save()
            emit_timeline_event(
                tenant_id=application.tenant_id,
                candidate_id=application.candidate_id,
                engagement=engagement,
                event_type='application.rejected',
                actor=user,
                payload={
                    'application_id': str(application.id),
                    'rejection_reason': reason,
                }
            )
    except Exception:
        pass


def on_offer_made(application, offer_data, user):
    try:
        from apps.candidates.models import CandidateEngagement
        from apps.candidates.signals import emit_timeline_event
        engagement = CandidateEngagement.objects.filter(
            candidate_id=application.candidate_id,
            tenant_id=application.tenant_id,
            job_id=application.requisition_id,
            is_deleted=False
        ).order_by('-started_at').first()
        if engagement:
            engagement.stage = 'offered'
            engagement.priority = 'hot'
            engagement.last_activity_at = timezone.now()
            engagement.save()
            emit_timeline_event(
                tenant_id=application.tenant_id,
                candidate_id=application.candidate_id,
                engagement=engagement,
                event_type='application.offer_made',
                actor=user,
                payload={
                    'application_id': str(application.id),
                    'offer_amount': str(offer_data.get('offer_amount', '')),
                    'currency': offer_data.get('currency', 'INR'),
                }
            )
    except Exception:
        pass


def on_candidate_hired(application, user):
    try:
        from apps.candidates.models import CandidateEngagement
        from apps.candidates.signals import emit_timeline_event
        engagement = CandidateEngagement.objects.filter(
            candidate_id=application.candidate_id,
            tenant_id=application.tenant_id,
            job_id=application.requisition_id,
            is_deleted=False
        ).order_by('-started_at').first()
        if engagement:
            engagement.stage = 'placed'
            engagement.is_active = False
            engagement.closed_at = timezone.now()
            engagement.closure_reason = 'hired'
            engagement.last_activity_at = timezone.now()
            engagement.save()
            emit_timeline_event(
                tenant_id=application.tenant_id,
                candidate_id=application.candidate_id,
                engagement=engagement,
                event_type='application.hired',
                actor=user,
                payload={'application_id': str(application.id)}
            )
    except Exception:
        pass
