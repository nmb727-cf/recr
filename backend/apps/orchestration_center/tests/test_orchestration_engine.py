import uuid
import pytest
from django.utils import timezone
from apps.orchestration_center.models.orchestration_engine import (
    WorkflowProcessInstance,
    WorkflowStageExecution,
    WorkflowApprovalCheckpoint,
    WorkflowSchedulerCheckpoint,
    WorkflowNegotiationCheckpoint,
    WorkflowHandoffRecord
)
from apps.orchestration_center.services.workflow_orchestration_engine import WorkflowOrchestrationEngine

@pytest.mark.django_db
class TestWorkflowOrchestrationEngine:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow_id = uuid.uuid4()
        self.entity_id = uuid.uuid4()

    def test_full_orchestration_flow(self):
        # 1. Start process
        instance = WorkflowOrchestrationEngine.start_process_instance(
            self.tenant_id, self.workflow_id, 'candidate', self.entity_id
        )
        assert instance.process_status == 'running'
        assert instance.tenant_id == self.tenant_id

        # 2. Agency Submission (Stage 1)
        stage1 = WorkflowOrchestrationEngine.create_stage_execution(
            instance, 'agency_submission', 'process_stage'
        )
        assert instance.current_stage == 'agency_submission'
        assert stage1.status == 'running'

        # 3. Prequalification Approval (Stage 2)
        stage2 = WorkflowOrchestrationEngine.move_to_next_stage(
            instance, 'prequalification', 'approval_gate'
        )
        stage1.refresh_from_db()
        assert stage1.status == 'completed'
        
        checkpoint = WorkflowOrchestrationEngine.request_approval(
            stage2, 'prequalification_approval', uuid.uuid4()
        )
        instance.refresh_from_db()
        assert instance.process_status == 'waiting_approval'

        WorkflowOrchestrationEngine.handle_approval_response(checkpoint.id, 'approved', 'Looks good')
        stage2.refresh_from_db()
        assert stage2.status == 'approved'
        instance.refresh_from_db()
        assert instance.process_status == 'running'

        # 4. Interview Round 1 (Stage 3)
        stage3 = WorkflowOrchestrationEngine.create_interview_round(instance, 1)
        WorkflowOrchestrationEngine.evaluate_round_outcome(stage3, True)
        assert stage3.status == 'completed'

        # 5. Scheduling (Stage 4)
        stage4 = WorkflowOrchestrationEngine.move_to_next_stage(
            instance, 'personal_interview', 'scheduler'
        )
        sched_checkpoint = WorkflowOrchestrationEngine.check_scheduler_availability(
            stage4, 'personal_interview', [uuid.uuid4()]
        )
        instance.refresh_from_db()
        assert instance.process_status == 'waiting_schedule'

        WorkflowOrchestrationEngine.book_scheduler_slot(sched_checkpoint.id, {'start': '2026-04-10T10:00:00Z'})
        stage4.refresh_from_db()
        assert stage4.status == 'completed'
        instance.refresh_from_db()
        assert instance.process_status == 'running'

        # 6. Negotiation (Stage 5)
        neg_checkpoint = WorkflowOrchestrationEngine.start_negotiation(
            instance, uuid.uuid4(), 100000, 90000, 110000
        )
        band_status = WorkflowOrchestrationEngine.evaluate_negotiation_band(neg_checkpoint.id)
        assert band_status == 'within_band'
        
        WorkflowOrchestrationEngine.complete_negotiation(neg_checkpoint.id, 'accepted')
        instance.refresh_from_db()
        assert instance.process_status == 'running'

        # 7. Handoff
        handoff = WorkflowOrchestrationEngine.create_handoff_record(
            instance, 'onboarding', {'candidate_name': 'John Doe'}
        )
        assert handoff.status == 'pending'

        # 8. Complete Process
        WorkflowOrchestrationEngine.complete_process_instance(instance)
        assert instance.process_status == 'completed'
        assert instance.completed_at is not None

    def test_failed_approval_path(self):
        instance = WorkflowOrchestrationEngine.start_process_instance(
            self.tenant_id, self.workflow_id, 'candidate', self.entity_id
        )
        stage = WorkflowOrchestrationEngine.create_stage_execution(
            instance, 'prequalification', 'approval_gate'
        )
        checkpoint = WorkflowOrchestrationEngine.request_approval(
            stage, 'prequalification_approval', uuid.uuid4()
        )
        
        WorkflowOrchestrationEngine.handle_approval_response(checkpoint.id, 'rejected', 'Salary too high')
        stage.refresh_from_db()
        assert stage.status == 'rejected'
        
        WorkflowOrchestrationEngine.fail_process_instance(instance, reason='rejected')
        instance.refresh_from_db()
        assert instance.process_status == 'rejected'
