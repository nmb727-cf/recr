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
        # Promote only pre-job stages to first job-specific stage.
        lead_stages = ['new_lead', 'contacted', 'follow_up', 'qualified', 'nurture', 'dormant']
        old_stage = engagement.stage
        if engagement.stage in lead_stages:
            engagement.stage = 'submitted'
        engagement.last_activity_at = timezone.now()
        engagement.save()
        if old_stage != engagement.stage:
            emit_timeline_event(
                tenant_id=application.tenant_id,
                candidate_id=application.candidate_id,
                engagement=engagement,
                event_type='engagement.stage_changed',
                actor=user,
                payload={
                    'from_stage': old_stage,
                    'to_stage': engagement.stage,
                    'note': 'System automation moved stage due to application creation.',
                    'changed_by': str(user.id) if user else None,
                    'changed_at': timezone.now().isoformat(),
                },
                source='system'
            )
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


def on_application_stage_changed(application, from_status, to_status, user, note=None):
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
        auto_note = note or f"System automation moved stage due to pipeline status change ({from_status} -> {to_status})."
        old_stage, new_stage = sync_engagement_stage(engagement, to_status, user, note=auto_note)
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
                    'note': auto_note,
                    'changed_by': str(user.id) if user else None,
                    'changed_at': timezone.now().isoformat(),
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
            stage_note = reason or "System automation moved stage due to application rejection."
            old_stage = engagement.stage
            engagement.stage = 'rejected'
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
                    'from_stage': old_stage,
                    'to_stage': 'rejected',
                    'note': stage_note,
                    'changed_by': str(user.id) if user else None,
                    'changed_at': timezone.now().isoformat(),
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
            old_stage = engagement.stage
            engagement.stage = 'offered'
            engagement.priority = 'hot'
            engagement.last_activity_at = timezone.now()
            engagement.save()
            stage_note = (
                offer_data.get('notes')
                or f"System automation moved stage due to offer action ({offer_data.get('currency', 'INR')} {offer_data.get('offer_amount', '')})."
            )
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
                    'from_stage': old_stage,
                    'to_stage': 'offered',
                    'note': stage_note,
                    'changed_by': str(user.id) if user else None,
                    'changed_at': timezone.now().isoformat(),
                }
            )
    except Exception:
        pass


def on_candidate_hired(application, user):
    try:
        from apps.candidates.models import CandidateEngagement
        from apps.candidates.signals import emit_timeline_event
        from apps.pipeline.guarantee import start_guarantee_for_joined_placement
        engagement = CandidateEngagement.objects.filter(
            candidate_id=application.candidate_id,
            tenant_id=application.tenant_id,
            job_id=application.requisition_id,
            is_deleted=False
        ).order_by('-started_at').first()
        if engagement:
            old_stage = engagement.stage
            engagement.stage = 'joined'
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
                payload={
                    'application_id': str(application.id),
                    'from_stage': old_stage,
                    'to_stage': 'joined',
                    'note': 'System automation moved stage due to hired outcome.',
                    'changed_by': str(user.id) if user else None,
                    'changed_at': timezone.now().isoformat(),
                }
            )
        start_guarantee_for_joined_placement(application)
    except Exception:
        pass
