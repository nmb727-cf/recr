import uuid
import pytest
from django.utils import timezone
from apps.agency_workflows.models import (
    AgencyWorkflowDefinition,
)
from apps.agency_workflows.models.orchestration import (
    AgencyWorkflowProcessInstance,
    AgencyWorkflowStageExecution,
    AgencyInternalApprovalCheckpoint,
    AgencyClientResponseCheckpoint,
    AgencyOfferProgressCheckpoint,
    AgencyPlacementGuaranteeRecord
)
from apps.agency_workflows.services.agency_workflow_orchestration_engine import AgencyWorkflowOrchestrationEngine

@pytest.mark.django_db
class TestAgencyWorkflowOrchestrationEngine:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow = AgencyWorkflowDefinition.objects.create(
            tenant_id=self.tenant_id,
            name="End-to-End Test Workflow",
            scope="submission",
            status="active"
        )
        self.entity_id = uuid.uuid4()
        self.candidate_id = uuid.uuid4()
        self.client_id = uuid.uuid4()
        self.job_id = uuid.uuid4()

    def test_full_agency_orchestration_flow(self):
        # 1. Start process
        instance = AgencyWorkflowOrchestrationEngine.start_agency_process_instance(
            self.tenant_id, self.workflow.id, 'candidate', self.entity_id,
            self.candidate_id, self.client_id, self.job_id
        )
        assert instance.process_status == 'running'
        
        # 2. Candidate readiness validation and internal approval
        stage1 = AgencyWorkflowOrchestrationEngine.create_stage_execution(
            instance, 'internal_review', 'recruiter_review'
        )
        assert instance.current_stage == 'internal_review'
        
        checkpoint = AgencyWorkflowOrchestrationEngine.request_internal_approval(
            stage1, 'submission_approval', uuid.uuid4()
        )
        instance.refresh_from_db()
        assert instance.process_status == 'waiting_internal'
        
        AgencyWorkflowOrchestrationEngine.handle_internal_approval_response(
            checkpoint.id, 'approved', 'Looks good to submit'
        )
        stage1.refresh_from_db()
        assert stage1.status == 'approved'
        instance.refresh_from_db()
        assert instance.process_status == 'running'
        
        # 3. Submission to Client
        stage2 = AgencyWorkflowOrchestrationEngine.move_to_next_stage(
            instance, 'submission_to_client', 'submission_stage'
        )
        stage1.refresh_from_db()
        assert stage1.status == 'approved'
        
        client_wait_checkpoint = AgencyWorkflowOrchestrationEngine.wait_for_client_response(
            instance, stage2, 'submission_feedback'
        )
        instance.refresh_from_db()
        assert instance.process_status == 'waiting_client'
        
        # Simulate Follow-up
        AgencyWorkflowOrchestrationEngine.trigger_client_followup(client_wait_checkpoint.id)
        client_wait_checkpoint.refresh_from_db()
        assert client_wait_checkpoint.status == 'reminded'
        
        # Complete client wait
        client_wait_checkpoint.status = 'responded'
        client_wait_checkpoint.save()
        stage2.status = 'completed'
        stage2.completed_at = timezone.now()
        stage2.save()
        instance.process_status = 'running'
        instance.save()
        
        # 4. Interview Coordination
        client_interview_checkpoint = AgencyWorkflowOrchestrationEngine.coordinate_interview_stage(instance)
        instance.refresh_from_db()
        assert instance.process_status == 'waiting_client'
        assert client_interview_checkpoint.response_type == 'interview_confirmation'
        
        # Complete interview wait
        client_interview_checkpoint.status = 'responded'
        client_interview_checkpoint.save()
        client_interview_checkpoint.stage_execution.status = 'completed'
        client_interview_checkpoint.stage_execution.save()
        instance.process_status = 'running'
        instance.save()
        
        # 5. Offer Progress
        offer_checkpoint = AgencyWorkflowOrchestrationEngine.record_offer_progress(
            instance, 'received', 100000
        )
        assert offer_checkpoint.offer_status == 'received'
        assert offer_checkpoint.status == 'active'
        
        AgencyWorkflowOrchestrationEngine.record_offer_progress(
            instance, 'accepted'
        )
        offer_checkpoint.refresh_from_db()
        assert offer_checkpoint.offer_status == 'accepted'
        assert offer_checkpoint.status == 'accepted'
        
        # 6. Placement & Guarantee
        placement_record = AgencyWorkflowOrchestrationEngine.record_placement_joining(instance)
        assert placement_record.placement_status == 'joining_pending'
        
        AgencyWorkflowOrchestrationEngine.start_guarantee_tracking(placement_record.id)
        placement_record.refresh_from_db()
        assert placement_record.placement_status == 'joined'
        assert placement_record.guarantee_status == 'active'
        
        # 7. Closure
        AgencyWorkflowOrchestrationEngine.close_agency_process_instance(instance)
        instance.refresh_from_db()
        assert instance.process_status == 'completed'

    def test_failed_approval_path(self):
        instance = AgencyWorkflowOrchestrationEngine.start_agency_process_instance(
            self.tenant_id, self.workflow.id, 'candidate', self.entity_id
        )
        stage = AgencyWorkflowOrchestrationEngine.create_stage_execution(
            instance, 'internal_review', 'recruiter_review'
        )
        checkpoint = AgencyWorkflowOrchestrationEngine.request_internal_approval(
            stage, 'submission_approval', uuid.uuid4()
        )
        
        AgencyWorkflowOrchestrationEngine.handle_internal_approval_response(
            checkpoint.id, 'rejected', 'Candidate missing skills'
        )
        stage.refresh_from_db()
        assert stage.status == 'rejected'
        
        AgencyWorkflowOrchestrationEngine.fail_agency_process_instance(instance, 'rejected')
        instance.refresh_from_db()
        assert instance.process_status == 'rejected'
