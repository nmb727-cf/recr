import uuid
from unittest.mock import patch

from django.test import TestCase

from apps.orchestration_center.models.workflow import Workflow, WorkflowNode
from apps.workflow_execution.models import (
    WorkflowRecoveryActionLog,
    WorkflowRecoveryCase,
    WorkflowRecoveryPolicy,
)
from apps.workflow_execution.services.workflow_failure_recovery_engine import WorkflowFailureRecoveryEngine
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker


class TestWorkflowFailureRecoveryEngine(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Recovery WF',
            trigger_event='job_created',
            status='active',
            is_active=True,
        )
        self.stage = WorkflowNode.objects.create(workflow=self.workflow, node_type='action', config={'label': 'Review'})
        self.instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='candidate',
            entity_id=uuid.uuid4(),
            status='running',
        )
        self.stage_execution = WorkflowInstanceTracker.start_stage_execution(
            self.instance,
            stage_id=self.stage.id,
            stage_name='Review',
        )

    def test_1_notification_failure_transient_creates_case_and_retry_scheduled(self):
        case = WorkflowFailureRecoveryEngine.create_recovery_case(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            recovery_type='notification_failure',
            error_message='SMTP timeout while sending invite',
            error_code='timeout',
        )
        case.refresh_from_db()
        assert case.failure_type in {'transient', 'timeout'}
        assert case.status == 'retry_scheduled'
        assert case.next_retry_at is not None

    def test_2_retry_succeeds_marks_case_recovered(self):
        case = WorkflowFailureRecoveryEngine.create_recovery_case(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            recovery_type='stage_failure',
            error_message='Temporary transition timeout',
            error_code='timeout',
        )
        with patch.object(WorkflowFailureRecoveryEngine, 'retry_stage_execution', return_value=True):
            attempt = WorkflowFailureRecoveryEngine.run_retry_attempt(case)
        case.refresh_from_db()
        assert attempt.status == 'succeeded'
        assert case.status == 'recovered'

    def test_3_retry_limit_exceeded_escalates_or_permanent_failure(self):
        policy = WorkflowRecoveryPolicy.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            failure_type='transient',
            retry_strategy='immediate',
            retry_limit=1,
            retry_delay_seconds=0,
            escalate_after_failures=1,
            requires_manual_review=False,
            is_active=True,
        )
        case = WorkflowRecoveryCase.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            recovery_type='stage_failure',
            failure_type='transient',
            error_message='Repeated temporary failure',
            error_code='timeout',
            status='open',
            retry_strategy='immediate',
            retry_limit=1,
            retry_count=0,
            metadata={'policy_id': str(policy.id)},
        )
        with patch.object(WorkflowFailureRecoveryEngine, 'retry_stage_execution', side_effect=RuntimeError('still failing')):
            attempt = WorkflowFailureRecoveryEngine.run_retry_attempt(case)
        case.refresh_from_db()
        assert attempt.status == 'failed'
        assert case.status in {'escalated', 'failed_permanently'}

    def test_4_validation_error_no_infinite_retry_manual_or_permanent(self):
        case = WorkflowFailureRecoveryEngine.create_recovery_case(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            recovery_type='stage_failure',
            error_message='Validation error: required field missing',
            error_code='validation',
        )
        case.refresh_from_db()
        assert case.failure_type == 'validation'
        assert case.status in {'manual_intervention_required', 'failed_permanently'}
        assert case.retry_strategy in {'manual_only', 'no_retry'}

    def test_5_manual_resume_recovers_case(self):
        case = WorkflowRecoveryCase.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            recovery_type='stage_failure',
            failure_type='unknown',
            error_message='Needs manual resume',
            error_code='',
            status='manual_intervention_required',
            retry_strategy='manual_only',
            retry_limit=0,
            retry_count=0,
            metadata={},
        )
        self.instance.status = 'waiting'
        self.instance.save(update_fields=['status', 'updated_at'])
        case = WorkflowFailureRecoveryEngine.manual_resume(case, action_taken_by='qa_user')
        case.refresh_from_db()
        self.instance.refresh_from_db()
        assert case.status == 'recovered'
        assert self.instance.status in {'running', 'waiting', 'completed'}

    def test_6_repeated_stage_failure_preserves_retry_history(self):
        case = WorkflowRecoveryCase.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            recovery_type='stage_failure',
            failure_type='transient',
            error_message='Intermittent service error',
            error_code='timeout',
            status='open',
            retry_strategy='immediate',
            retry_limit=2,
            retry_count=0,
            metadata={},
        )
        with patch.object(WorkflowFailureRecoveryEngine, 'retry_stage_execution', side_effect=RuntimeError('downstream down')):
            WorkflowFailureRecoveryEngine.run_retry_attempt(case)
            WorkflowFailureRecoveryEngine.run_retry_attempt(case)
        case.refresh_from_db()
        assert case.retry_attempts.count() >= 2
        assert WorkflowRecoveryActionLog.objects.filter(recovery_case=case, action_type='retry_failed').count() >= 2
