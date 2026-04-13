import uuid
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from apps.agency_candidates.models import (
    AgencyCandidate,
    AgencyCandidateActivity,
    AgencyCandidateOwnership,
    AgencyCandidateSubmission,
    AgencyCandidatePipelineRegistry
)
from apps.candidates.models import Candidate
from apps.agencies.models import AgencyClientRelationship, AgencyJobAssignment
from apps.pipeline.models import Application
from apps.communications.notification_service import NotificationService
from apps.communications.communication_service import ThreadService


class AgencyCandidateCRMService:
    @staticmethod
    @transaction.atomic
    def create_agency_candidate(tenant_id, candidate_data, recruiter_id):
        """
        Creates a core Candidate and an AgencyCandidate overlay.
        """
        email = candidate_data.get('email')
        phone = candidate_data.get('phone')
        
        # 1. Find or create core candidate
        candidate = None
        if email or phone:
            # Simple deduplication logic
            candidate = Candidate.objects.filter(
                Q(email=email) | Q(phone=phone)
            ).first()
            
        if not candidate:
            candidate = Candidate.objects.create(
                first_name=candidate_data.get('first_name'),
                last_name=candidate_data.get('last_name'),
                email=email,
                phone=phone,
                current_title=candidate_data.get('current_title', ''),
                tenant_id=None, # Global candidate
                source='agency',
                source_detail='Staffing Agency CRM'
            )
            
        # 2. Create Agency Overlay
        agency_candidate, created = AgencyCandidate.objects.get_or_create(
            tenant_id=tenant_id,
            candidate=candidate,
            defaults={
                'owner_id': recruiter_id,
                'source': candidate_data.get('source', 'manual'),
                'expected_salary_min': candidate_data.get('expected_salary_min'),
                'expected_salary_max': candidate_data.get('expected_salary_max'),
                'currency': candidate_data.get('currency', 'INR'),
                'availability': candidate_data.get('availability', 'immediate'),
                'status': 'active'
            }
        )
        
        if created:
            # Set initial pipeline stage (Registry driven)
            initial_stage = AgencyCandidatePipelineRegistry.objects.filter(
                tenant_id=tenant_id, stage_key='new_lead'
            ).first() or AgencyCandidatePipelineRegistry.objects.filter(
                is_system=True, stage_key='new_lead'
            ).first()
            
            if initial_stage:
                agency_candidate.pipeline_stage = initial_stage
                agency_candidate.save()
            
            # Initial Ownership
            AgencyCandidateOwnership.objects.create(
                tenant_id=tenant_id,
                agency_candidate=agency_candidate,
                owner_id=recruiter_id,
                is_current=True
            )
            
            # Log activity
            AgencyCandidateActivity.objects.create(
                agency_candidate=agency_candidate,
                tenant_id=tenant_id,
                activity_type='created',
                actor_id=recruiter_id,
                payload={'method': 'manual_add'}
            )

            # Trigger Notification
            NotificationService.create_notification(
                user_id=recruiter_id,
                tenant_id=tenant_id,
                title="New Candidate Added",
                body=f"Candidate {candidate.full_name} has been added to your talent pool.",
                notification_type="agency_candidate_created",
                related_entity_type="agency_candidate",
                related_entity_id=agency_candidate.id
            )
            
        return agency_candidate

    @staticmethod
    @transaction.atomic
    def transfer_ownership(agency_candidate_id, new_owner_id, actor_id):
        """
        Transfers ownership of a candidate to another recruiter.
        """
        candidate = AgencyCandidate.objects.get(id=agency_candidate_id)
        old_owner_id = candidate.owner_id
        tenant_id = candidate.tenant_id

        if str(old_owner_id) == str(new_owner_id):
            return candidate

        # 1. Update current ownership record
        AgencyCandidateOwnership.objects.filter(
            agency_candidate=candidate, is_current=True
        ).update(
            is_current=False, ended_at=timezone.now()
        )
        
        candidate.owner_id = new_owner_id
        candidate.save()
        
        # 2. Create new ownership record
        AgencyCandidateOwnership.objects.create(
            tenant_id=tenant_id,
            agency_candidate=candidate,
            owner_id=new_owner_id,
            is_current=True
        )
        
        # 3. Log activity
        AgencyCandidateActivity.objects.create(
            agency_candidate=candidate,
            tenant_id=tenant_id,
            activity_type='owner_transferred',
            actor_id=actor_id,
            payload={
                'old_owner_id': str(old_owner_id),
                'new_owner_id': str(new_owner_id)
            }
        )

        # 4. Trigger Notifications
        # Notify new owner
        NotificationService.create_notification(
            user_id=new_owner_id,
            tenant_id=tenant_id,
            title="Candidate Assigned",
            body=f"Candidate {candidate.candidate.full_name} has been assigned to you.",
            notification_type="agency_candidate_assigned",
            related_entity_type="agency_candidate",
            related_entity_id=candidate.id
        )

        return candidate

    @staticmethod
    @transaction.atomic
    def submit_to_client(agency_candidate_id, client_tenant_id, job_id, recruiter_id):
        """
        Submits a candidate to a client for a specific job.
        """
        agency_candidate = AgencyCandidate.objects.get(id=agency_candidate_id)
        agency_tenant_id = agency_candidate.tenant_id
        
        # 1. Validate relationship
        relationship = AgencyClientRelationship.objects.filter(
            agency_tenant_id=agency_tenant_id,
            company_tenant_id=client_tenant_id,
            status='active'
        ).first()
        if not relationship:
            raise ValueError("No active relationship with this client.")
            
        # 2. Validate job assignment
        assignment = AgencyJobAssignment.objects.filter(
            agency_tenant_id=agency_tenant_id,
            requisition_id=job_id,
            status='active'
        ).first()
        if not assignment:
            raise ValueError("No active job assignment for this job.")
            
        # 3. Create Application in Client Tenant
        application = Application.objects.create(
            tenant_id=client_tenant_id,
            candidate_id=agency_candidate.candidate.id,
            requisition_id=job_id,
            agency_id=agency_tenant_id,
            is_agency_submission=True,
            submitted_by=recruiter_id,
            submitted_by_tenant_id=agency_tenant_id,
            status='applied'
        )
        
        # 4. Create Agency Submission Record
        submission = AgencyCandidateSubmission.objects.create(
            tenant_id=agency_tenant_id,
            agency_candidate=agency_candidate,
            client_tenant_id=client_tenant_id,
            job_id=job_id,
            status='submitted'
        )
        
        # 5. Update Agency Candidate Status/Stage
        submitted_stage = AgencyCandidatePipelineRegistry.objects.filter(
            tenant_id=agency_tenant_id, stage_key='submitted'
        ).first()
        if submitted_stage:
            agency_candidate.pipeline_stage = submitted_stage
            agency_candidate.save()
            
        # 6. Log activity
        AgencyCandidateActivity.objects.create(
            agency_candidate=agency_candidate,
            tenant_id=agency_tenant_id,
            activity_type='submitted_to_client',
            actor_id=recruiter_id,
            payload={
                'client_tenant_id': str(client_tenant_id),
                'job_id': str(job_id),
                'application_id': str(application.id)
            }
        )

        # 7. Create/Get Message Thread for Coordination
        # We create a thread between the agency recruiter and the client
        # In a real staffing scenario, there's usually a "staffing coordinator" on client side
        # For now, we'll just create the thread.
        ThreadService.get_or_create_context_thread(
            tenant_id=agency_tenant_id,
            related_entity_type="agency_submission",
            related_entity_id=submission.id,
            subject=f"Submission: {agency_candidate.candidate.full_name} for Job {job_id}",
            created_by_user_id=recruiter_id,
            participant_user_ids=[recruiter_id]
        )

        # 8. Trigger Notification
        NotificationService.create_notification(
            user_id=recruiter_id,
            tenant_id=agency_tenant_id,
            title="Candidate Submitted",
            body=f"Candidate {agency_candidate.candidate.full_name} submitted to client.",
            notification_type="agency_candidate_submitted",
            related_entity_type="agency_candidate",
            related_entity_id=agency_candidate.id
        )
        
        return submission
