import logging
from django.utils import timezone
from apps.orchestration_center.models.orchestration_engine import (
    WorkflowProcessInstance,
    WorkflowStageExecution,
    WorkflowApprovalCheckpoint,
    WorkflowSchedulerCheckpoint,
    WorkflowNegotiationCheckpoint,
    WorkflowHandoffRecord
)

logger = logging.getLogger(__name__)

class WorkflowOrchestrationEngine:
    @staticmethod
    def start_process_instance(tenant_id, workflow_id, entity_type, entity_id, created_by=None):
        """Initializes a new business process orchestration instance."""
        instance = WorkflowProcessInstance.objects.create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            entity_type=entity_type,
            entity_id=entity_id,
            process_status='running',
            created_by=created_by
        )
        logger.info(f"Started process instance {instance.id} for {entity_type} {entity_id}")
        return instance

    @staticmethod
    def create_stage_execution(process_instance, stage_key, stage_type, metadata=None):
        """Creates a specific execution stage within a process."""
        stage = WorkflowStageExecution.objects.create(
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

        return WorkflowOrchestrationEngine.create_stage_execution(
            process_instance, next_stage_key, next_stage_type, metadata
        )

    @staticmethod
    def wait_for_human_action(process_instance, reason='waiting_human'):
        """Pauses process execution for human intervention."""
        process_instance.process_status = reason
        process_instance.save()
        
        current_stage = process_instance.stages.filter(status='running').first()
        if current_stage:
            current_stage.status = 'waiting'
            current_stage.save()

    @staticmethod
    def request_approval(stage_execution, approval_type, user_id):
        """Creates an approval checkpoint."""
        checkpoint = WorkflowApprovalCheckpoint.objects.create(
            tenant_id=stage_execution.tenant_id,
            process_instance=stage_execution.process_instance,
            stage_execution=stage_execution,
            approval_type=approval_type,
            requested_from_user_id=user_id,
            status='pending'
        )
        stage_execution.process_instance.process_status = 'waiting_approval'
        stage_execution.process_instance.save()
        return checkpoint

    @staticmethod
    def handle_approval_response(checkpoint_id, status, notes=None):
        """Processes an approval/rejection response."""
        checkpoint = WorkflowApprovalCheckpoint.objects.get(id=checkpoint_id)
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
        
        # Resume process status
        stage.process_instance.process_status = 'running'
        stage.process_instance.save()
        return checkpoint

    @staticmethod
    def create_interview_round(process_instance, round_number, metadata=None):
        """Orchestrates an interview round."""
        stage_key = f"interview_round_{round_number}"
        return WorkflowOrchestrationEngine.create_stage_execution(
            process_instance, stage_key, 'interview_round', metadata
        )

    @staticmethod
    def evaluate_round_outcome(stage_execution, passed):
        """Evaluates interview round results to determine next steps."""
        if passed:
            stage_execution.status = 'completed'
        else:
            stage_execution.status = 'failed'
        stage_execution.completed_at = timezone.now()
        stage_execution.save()
        return passed

    @staticmethod
    def check_scheduler_availability(stage_execution, scheduling_type, target_user_ids, mode='online'):
        """Initiates availability check for scheduling."""
        checkpoint = WorkflowSchedulerCheckpoint.objects.create(
            tenant_id=stage_execution.tenant_id,
            process_instance=stage_execution.process_instance,
            stage_execution=stage_execution,
            scheduling_type=scheduling_type,
            target_user_ids=[str(uid) for uid in target_user_ids],
            target_mode=mode,
            status='pending'
        )
        stage_execution.process_instance.process_status = 'waiting_schedule'
        stage_execution.process_instance.save()
        return checkpoint

    @staticmethod
    def book_scheduler_slot(checkpoint_id, slot_data):
        """Confirms a selected slot and updates checkpoint."""
        checkpoint = WorkflowSchedulerCheckpoint.objects.get(id=checkpoint_id)
        checkpoint.selected_slot = slot_data
        checkpoint.status = 'booked'
        checkpoint.save()

        stage = checkpoint.stage_execution
        stage.status = 'completed'
        stage.completed_at = timezone.now()
        stage.save()

        stage.process_instance.process_status = 'running'
        stage.process_instance.save()
        return checkpoint

    @staticmethod
    def start_negotiation(process_instance, offer_id, amount, band_min, band_max):
        """Initializes a negotiation loop."""
        checkpoint = WorkflowNegotiationCheckpoint.objects.create(
            tenant_id=process_instance.tenant_id,
            process_instance=process_instance,
            offer_id=offer_id,
            proposed_amount=amount,
            allowed_band_min=band_min,
            allowed_band_max=band_max,
            status='pending'
        )
        process_instance.process_status = 'waiting_candidate'
        process_instance.save()
        return checkpoint

    @staticmethod
    def evaluate_negotiation_band(checkpoint_id):
        """Checks if proposed amount is within allowed band."""
        checkpoint = WorkflowNegotiationCheckpoint.objects.get(id=checkpoint_id)
        if checkpoint.allowed_band_min <= checkpoint.proposed_amount <= checkpoint.allowed_band_max:
            checkpoint.status = 'within_band'
        else:
            checkpoint.status = 'approval_required'
        checkpoint.save()
        return checkpoint.status

    @staticmethod
    def complete_negotiation(checkpoint_id, status):
        """Finalizes negotiation stage."""
        checkpoint = WorkflowNegotiationCheckpoint.objects.get(id=checkpoint_id)
        checkpoint.status = status
        checkpoint.save()
        
        checkpoint.process_instance.process_status = 'running'
        checkpoint.process_instance.save()
        return checkpoint

    @staticmethod
    def create_handoff_record(process_instance, handoff_type, payload, destination=''):
        """Creates a record for downstream system handoff."""
        record = WorkflowHandoffRecord.objects.create(
            tenant_id=process_instance.tenant_id,
            process_instance=process_instance,
            handoff_type=handoff_type,
            payload=payload,
            destination_system=destination,
            status='pending'
        )
        return record

    @staticmethod
    def complete_process_instance(process_instance):
        """Marks the entire process as successfully finished."""
        process_instance.process_status = 'completed'
        process_instance.completed_at = timezone.now()
        process_instance.save()
        logger.info(f"Process instance {process_instance.id} completed")

    @staticmethod
    def fail_process_instance(process_instance, reason='failed'):
        """Marks the process as failed."""
        process_instance.process_status = reason
        process_instance.completed_at = timezone.now()
        process_instance.save()
        logger.warning(f"Process instance {process_instance.id} failed with status {reason}")
