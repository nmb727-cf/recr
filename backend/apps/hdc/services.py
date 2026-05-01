import uuid
from django.utils import timezone
from apps.core import events
from apps.hdc.models import (
    HiringCommittee, DecisionApproval,
    OfferRecommendation, NegotiationCase,
    OfferReleasePacket, JoiningCase,
    HDCAuditLog
)
from apps.pipeline.models import Application, ApplicationStageHistory

class HDCOperationalService:
    """
    Central service for handling state transitions across the HDC modules.
    Ensures that when one stage completes, the next is initialized if needed.
    Also syncs with the central Pipeline Application status.
    """

    @staticmethod
    def update_application_status(tenant_id, application_id, new_status, moved_by, reason='', notes=''):
        """
        Updates the status of an application in the pipeline and records history.
        """
        try:
            app = Application.objects.get(id=application_id, tenant_id=tenant_id)
            old_status = app.status
            if old_status == new_status:
                return app

            app.status = new_status
            app.save(update_fields=['status', 'updated_at'])

            ApplicationStageHistory.objects.create(
                tenant_id=tenant_id,
                application_id=application_id,
                from_status=old_status,
                to_status=new_status,
                moved_by=moved_by,
                reason=reason,
                notes=notes
            )
            return app
        except Application.DoesNotExist:
            return None

    @staticmethod
    def handle_committee_completion(committee: HiringCommittee):
        """
        Transition from Committee to Approval or Rejection.
        """
        if committee.status != 'completed':
            return

        if committee.result == 'hire':
            # Create a pending approval
            DecisionApproval.objects.get_or_create(
                tenant_id=committee.tenant_id,
                application_id=committee.application_id,
                defaults={
                    'requisition_id': committee.requisition_id,
                    'status': 'pending',
                    'approver_id': committee.created_by,
                }
            )
            # Sync with pipeline if needed, but usually stays in 'interview' until approved for offer
        elif committee.result == 'reject':
            # Mark application as rejected
            HDCOperationalService.update_application_status(
                tenant_id=committee.tenant_id,
                application_id=committee.application_id,
                new_status='rejected',
                moved_by=committee.created_by,
                reason='Hiring Committee Decision: Reject'
            )

    @staticmethod
    def handle_approval_completion(approval: DecisionApproval):
        """
        Transition from Approval to Offer Intelligence.
        """
        if approval.status != 'approved':
            return

        # Initialize Offer Recommendation
        OfferRecommendation.objects.get_or_create(
            tenant_id=approval.tenant_id,
            application_id=approval.application_id,
            defaults={
                'status': 'scenario_modeling'
            }
        )

        # Update pipeline status to 'offer'
        HDCOperationalService.update_application_status(
            tenant_id=approval.tenant_id,
            application_id=approval.application_id,
            new_status='offer',
            moved_by=approval.approver_id,
            reason='HDC Approval for Offer'
        )

    @staticmethod
    def handle_offer_selection(recommendation: OfferRecommendation):
        """
        Transition from Offer Recommendation to Negotiation or Release.
        """
        if recommendation.status != 'recommended':
            return

        # Initialize Negotiation Case
        NegotiationCase.objects.get_or_create(
            tenant_id=recommendation.tenant_id,
            application_id=recommendation.application_id,
            defaults={
                'status': 'active'
            }
        )

    @staticmethod
    def finalize_negotiation(case: NegotiationCase):
        """
        Transition from Negotiation to Offer Release.
        """
        if case.status != 'agreed':
            return

        # Initialize Offer Release Packet
        OfferReleasePacket.objects.get_or_create(
            tenant_id=case.tenant_id,
            application_id=case.application_id,
            defaults={
                'status': 'draft'
            }
        )

    @staticmethod
    def handle_offer_acceptance(packet: OfferReleasePacket, user_id):
        """
        Handles offer acceptance logic and joining initialization.
        """
        if packet.status != 'accepted':
            return

        # Initialize Joining Case
        app = Application.objects.filter(id=packet.application_id, tenant_id=packet.tenant_id).first()
        HDCOperationalService.ensure_onboarding_case(
            tenant_id=packet.tenant_id,
            application_id=packet.application_id,
            candidate_id=getattr(app, 'candidate_id', None),
            job_id=getattr(app, 'requisition_id', None),
            offer_id=packet.id,
            joining_date=getattr(app, 'joining_date', None),
            accepted_at=timezone.now(),
            actor_id=user_id,
        )

        # Update pipeline acceptance data
        try:
            app = Application.objects.get(id=packet.application_id, tenant_id=packet.tenant_id)
            app.offer_accepted_at = timezone.now()
            app.save(update_fields=['offer_accepted_at', 'updated_at'])
        except Application.DoesNotExist:
            pass

    @staticmethod
    def record_joining(joining_case: JoiningCase, user_id):
        """
        Final transition to 'Joined'.
        """
        if joining_case.status == 'joined':
            # Update central pipeline status to 'joined'
            HDCOperationalService.update_application_status(
                tenant_id=joining_case.tenant_id,
                application_id=joining_case.application_id,
                new_status='joined',
                moved_by=user_id,
                reason='HDC Joining Confirmation'
            )
            
            # Update application joining date
            try:
                app = Application.objects.get(id=joining_case.application_id, tenant_id=joining_case.tenant_id)
                app.joined_at = timezone.now()
                if joining_case.actual_joining_date:
                    app.joining_date = joining_case.actual_joining_date
                app.save(update_fields=['joined_at', 'joining_date', 'updated_at'])
                events.onboarding.completed.send(sender=HDCOperationalService, application=app)
            except Application.DoesNotExist:
                pass

    @staticmethod
    def log_action(tenant_id, application_id, requisition_id, action_type, user_id, previous_status='', new_status='', comments='', metadata=None):
        """
        Records an audit log entry for HDC actions.
        """
        return HDCAuditLog.objects.create(
            tenant_id=tenant_id,
            application_id=application_id,
            requisition_id=requisition_id,
            action_type=action_type,
            previous_status=previous_status,
            new_status=new_status,
            performed_by_id=user_id,
            comments=comments,
            metadata=metadata or {}
        )
    @staticmethod
    def build_default_onboarding_checklist():
        return [
            {'task_name': 'documents received', 'assigned_to': '', 'due_date': None, 'status': 'pending'},
            {'task_name': 'background verification', 'assigned_to': '', 'due_date': None, 'status': 'pending'},
            {'task_name': 'IT provisioning', 'assigned_to': '', 'due_date': None, 'status': 'pending'},
            {'task_name': 'HR documentation', 'assigned_to': '', 'due_date': None, 'status': 'pending'},
            {'task_name': 'joining confirmation', 'assigned_to': '', 'due_date': None, 'status': 'pending'},
        ]

    @staticmethod
    def ensure_onboarding_case(
        *,
        tenant_id,
        application_id,
        candidate_id=None,
        job_id=None,
        offer_id=None,
        joining_date=None,
        accepted_at=None,
        actor_id=None,
    ):
        defaults = {
            'candidate_id': candidate_id,
            'job_id': job_id,
            'offer_id': offer_id,
            'joining_date': joining_date,
            'status': 'pending',
            'metadata': {
                'accepted_at': (accepted_at or timezone.now()).isoformat(),
                'checklist': HDCOperationalService.build_default_onboarding_checklist(),
                'documents': {},
                'hrms_handoff': {'status': 'pending'},
            },
        }
        case, created = JoiningCase.objects.update_or_create(
            tenant_id=tenant_id,
            application_id=application_id,
            defaults=defaults,
        )
        if not created:
            metadata = dict(case.metadata or {})
            metadata.setdefault('checklist', HDCOperationalService.build_default_onboarding_checklist())
            metadata.setdefault('documents', {})
            metadata.setdefault('hrms_handoff', {'status': 'pending'})
            if accepted_at:
                metadata['accepted_at'] = accepted_at.isoformat()
            case.metadata = metadata
            dirty_fields = ['metadata', 'updated_at']
            if candidate_id and not case.candidate_id:
                case.candidate_id = candidate_id
                dirty_fields.append('candidate_id')
            if job_id and not case.job_id:
                case.job_id = job_id
                dirty_fields.append('job_id')
            if offer_id:
                case.offer_id = offer_id
                dirty_fields.append('offer_id')
            if joining_date and not case.joining_date:
                case.joining_date = joining_date
                dirty_fields.append('joining_date')
            if case.status in {'joined', 'postponed', 'withdrawn', 'no_show'}:
                case.status = 'pending'
                dirty_fields.append('status')
            case.save(update_fields=dirty_fields)
        if created:
            application_proxy = type(
                'OnboardingApplicationProxy',
                (),
                {
                    'id': application_id,
                    'tenant_id': tenant_id,
                    'candidate_id': candidate_id,
                },
            )()
            events.onboarding.started.send(sender=HDCOperationalService, application=application_proxy)
        return case
