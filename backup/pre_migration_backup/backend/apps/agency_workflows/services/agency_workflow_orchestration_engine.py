import logging
from django.utils import timezone
from ..models.orchestration import (
    AgencyWorkflowProcessInstance,
    AgencyWorkflowStageExecution,
    AgencyInternalApprovalCheckpoint,
    AgencyClientResponseCheckpoint,
    AgencyOfferProgressCheckpoint,
    AgencyPlacementGuaranteeRecord
)

logger = logging.getLogger(__name__)

class AgencyWorkflowOrchestrationEngine:
    @staticmethod
    def start_agency_process_instance(tenant_id, workflow_id, entity_type, entity_id, 
                                      candidate_id=None, client_id=None, job_id=None, assigned_recruiter_id=None):
        """Initializes a new agency business process orchestration instance."""
        instance = AgencyWorkflowProcessInstance.objects.create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            entity_type=entity_type,
            entity_id=entity_id,
            candidate_id=candidate_id,
            client_id=client_id,
            job_id=job_id,
            assigned_recruiter_id=assigned_recruiter_id,
            process_status='running'
        )
        logger.info(f"Started agency process instance {instance.id} for {entity_type} {entity_id}")
        return instance

    @staticmethod
    def create_stage_execution(process_instance, stage_key, stage_type, metadata=None):
        """Creates a specific execution stage within an agency process."""
        stage = AgencyWorkflowStageExecution.objects.create(
            tenant_id=process_instance.tenant_id,
            process_instance=process_instance,
            stage_key=stage_key,
            stage_type=stage_type,
            status='running',
            metadata=metadata or {}
        )
        process_instance.current_stage = stage_key
        process_instance.save()
        return stage

    @staticmethod
    def move_to_next_stage(process_instance, next_stage_key, next_stage_type, metadata=None):
        """Completes current stage and transitions to the next."""
        current_stage = process_instance.stages.filter(status='running').first()
        if current_stage:
            current_stage.status = 'completed'
            current_stage.completed_at = timezone.now()
            current_stage.save()

        return AgencyWorkflowOrchestrationEngine.create_stage_execution(
            process_instance, next_stage_key, next_stage_type, metadata
        )

    @staticmethod
    def wait_for_internal_action(process_instance, reason='waiting_internal'):
        """Pauses process execution for internal recruiter/manager action."""
        process_instance.process_status = reason
        process_instance.save()
        
        current_stage = process_instance.stages.filter(status='running').first()
        if current_stage:
            current_stage.status = 'waiting'
            current_stage.save()

    @staticmethod
    def request_internal_approval(stage_execution, approval_type, user_id):
        """Creates an internal approval checkpoint."""
        checkpoint = AgencyInternalApprovalCheckpoint.objects.create(
            tenant_id=stage_execution.tenant_id,
            process_instance=stage_execution.process_instance,
            stage_execution=stage_execution,
            approval_type=approval_type,
            requested_from_user_id=user_id,
            status='pending'
        )
        stage_execution.process_instance.process_status = 'waiting_internal'
        stage_execution.process_instance.save()
        return checkpoint

    @staticmethod
    def handle_internal_approval_response(checkpoint_id, status, notes=None):
        """Processes an internal approval/rejection response."""
        checkpoint = AgencyInternalApprovalCheckpoint.objects.get(id=checkpoint_id)
        checkpoint.status = status
        checkpoint.responded_at = timezone.now()
        checkpoint.notes = notes or ""
        checkpoint.save()

        stage = checkpoint.stage_execution
        if status == 'approved':
            stage.status = 'approved'
        else:
            stage.status = 'rejected'
        stage.save()
        
        stage.process_instance.process_status = 'running'
        stage.process_instance.save()
        return checkpoint

    @staticmethod
    def create_submission_stage(process_instance, metadata=None):
        """Orchestrates candidate submission to client."""
        stage_key = "submission_to_client"
        return AgencyWorkflowOrchestrationEngine.create_stage_execution(
            process_instance, stage_key, 'submission_stage', metadata
        )

    @staticmethod
    def validate_submission_readiness(process_instance):
        """Validates if a candidate is ready to be submitted."""
        # Add logic to check qualification, interest, salary alignment
        return True

    @staticmethod
    def submit_candidate_to_client(process_instance):
        """Action to actually submit the candidate."""
        if not AgencyWorkflowOrchestrationEngine.validate_submission_readiness(process_instance):
            raise Exception("Candidate not ready for submission")
        stage = AgencyWorkflowOrchestrationEngine.create_submission_stage(process_instance)
        # Mock submission action
        stage.status = 'completed'
        stage.completed_at = timezone.now()
        stage.save()
        return AgencyWorkflowOrchestrationEngine.wait_for_client_response(process_instance, stage, 'submission_feedback')

    @staticmethod
    def wait_for_client_response(process_instance, stage_execution, response_type):
        """Creates a checkpoint waiting for client action."""
        checkpoint = AgencyClientResponseCheckpoint.objects.create(
            tenant_id=process_instance.tenant_id,
            process_instance=process_instance,
            stage_execution=stage_execution,
            response_type=response_type,
            status='pending'
        )
        process_instance.process_status = 'waiting_client'
        process_instance.save()
        return checkpoint

    @staticmethod
    def trigger_client_followup(checkpoint_id):
        """Updates client response checkpoint for follow-up."""
        checkpoint = AgencyClientResponseCheckpoint.objects.get(id=checkpoint_id)
        checkpoint.status = 'reminded'
        checkpoint.last_followup_at = timezone.now()
        checkpoint.save()
        return checkpoint

    @staticmethod
    def coordinate_interview_stage(process_instance, metadata=None):
        """Orchestrates interview coordination flow."""
        stage_key = "interview_coordination"
        stage = AgencyWorkflowOrchestrationEngine.create_stage_execution(
            process_instance, stage_key, 'interview_coordination', metadata
        )
        return AgencyWorkflowOrchestrationEngine.wait_for_client_response(process_instance, stage, 'interview_confirmation')

    @staticmethod
    def record_offer_progress(process_instance, offer_status, proposed_amount=None):
        """Updates or creates an offer progress checkpoint."""
        checkpoint, created = AgencyOfferProgressCheckpoint.objects.get_or_create(
            tenant_id=process_instance.tenant_id,
            process_instance=process_instance,
            candidate_id=process_instance.candidate_id,
            client_id=process_instance.client_id,
            job_id=process_instance.job_id,
            defaults={
                'offer_status': offer_status,
                'proposed_amount': proposed_amount
            }
        )
        if not created:
            checkpoint.offer_status = offer_status
            if proposed_amount:
                checkpoint.proposed_amount = proposed_amount
                checkpoint.negotiation_round += 1
            checkpoint.save()
        
        if offer_status == 'accepted':
            checkpoint.status = 'accepted'
        elif offer_status == 'rejected':
            checkpoint.status = 'rejected'
            
        checkpoint.save()
        return checkpoint

    @staticmethod
    def record_placement_joining(process_instance):
        """Creates placement guarantee record on joining."""
        record, created = AgencyPlacementGuaranteeRecord.objects.get_or_create(
            tenant_id=process_instance.tenant_id,
            process_instance=process_instance,
            candidate_id=process_instance.candidate_id,
            client_id=process_instance.client_id,
            job_id=process_instance.job_id,
            defaults={
                'placement_status': 'joining_pending'
            }
        )
        return record

    @staticmethod
    def start_guarantee_tracking(record_id):
        """Starts the guarantee period after confirmed joining."""
        record = AgencyPlacementGuaranteeRecord.objects.get(id=record_id)
        record.placement_status = 'joined'
        record.guarantee_status = 'active'
        record.joined_at = timezone.now()
        record.guarantee_start_date = timezone.now().date()
        record.save()
        return record

    @staticmethod
    def close_agency_process_instance(process_instance):
        """Marks the entire process as successfully finished."""
        process_instance.process_status = 'completed'
        process_instance.completed_at = timezone.now()
        process_instance.save()
        logger.info(f"Agency process instance {process_instance.id} completed")

    @staticmethod
    def fail_agency_process_instance(process_instance, reason='failed'):
        """Marks the process as failed."""
        process_instance.process_status = reason
        process_instance.completed_at = timezone.now()
        process_instance.save()
        logger.warning(f"Agency process instance {process_instance.id} failed with status {reason}")
