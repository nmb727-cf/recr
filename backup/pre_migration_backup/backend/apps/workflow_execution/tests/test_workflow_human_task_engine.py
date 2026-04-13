import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.orchestration_center.models.workflow import Workflow, WorkflowNode
from apps.workflow_execution.models import (
    WorkflowApprovalRule,
    WorkflowHumanTask,
    WorkflowInstance,
    WorkflowStageExecution,
)
from apps.workflow_execution.services.workflow_human_task_engine import WorkflowHumanTaskEngine


def make_workflow(tenant_id):
    workflow = Workflow.objects.create(
        tenant_id=tenant_id,
        name='Human Task WF',
        trigger_event='job_created',
        status='active',
        is_active=True,
    )
    stage = WorkflowNode.objects.create(workflow=workflow, node_type='approval')
    return workflow, stage


class TestWorkflowHumanTaskEngine(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.workflow, self.stage = make_workflow(self.tenant_id)
        self.instance = WorkflowInstance.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='candidate',
            entity_id=uuid.uuid4(),
            current_stage_id=self.stage.id,
            status='running',
            context_data={},
        )
        self.stage_execution = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_id=self.stage.id,
            stage_name='approval',
            status='waiting',
        )

    def test_1_stage_requires_recruiter_review_human_task_created(self):
        task = WorkflowHumanTaskEngine.create_human_task(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            task_type='review',
            title='Recruiter review required',
            assigned_to_type='recruiter',
            due_at=timezone.now() + timedelta(hours=12),
        )

        self.instance.refresh_from_db()
        assert task.id is not None
        assert task.task_type == 'review'
        assert self.instance.status == 'waiting'
        assert WorkflowHumanTask.objects.filter(workflow_instance=self.instance).count() == 1

    def test_2_user_completes_task_workflow_resumes(self):
        task = WorkflowHumanTaskEngine.create_human_task(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            task_type='feedback',
            title='Submit interview feedback',
            wait_for_completion=True,
        )

        result = WorkflowHumanTaskEngine.complete_human_task(
            task=task,
            completed_by_type='interviewer',
            comments='Feedback submitted',
        )
        self.instance.refresh_from_db()
        task.refresh_from_db()

        assert result['outcome'] == 'completed'
        assert task.status == 'completed'
        assert self.instance.status != 'waiting'

    def test_3_multiple_approvals_required_wait_until_all_approve(self):
        WorkflowApprovalRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            approval_type='multiple',
            required_approvals=2,
            approval_role='hiring_manager',
            escalation_role='hr',
            timeout_hours=24,
            is_active=True,
        )
        task = WorkflowHumanTaskEngine.create_human_task(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            task_type='approval',
            title='Offer approval',
            wait_for_completion=True,
        )

        first = WorkflowHumanTaskEngine.complete_human_task(
            task=task,
            completed_by_type='hiring_manager',
            completed_by_id=uuid.uuid4(),
            comments='Approved by manager 1',
        )
        task.refresh_from_db()
        assert first['finalized'] is False
        assert task.status == 'in_progress'

        second = WorkflowHumanTaskEngine.complete_human_task(
            task=task,
            completed_by_type='hiring_manager',
            completed_by_id=uuid.uuid4(),
            comments='Approved by manager 2',
        )
        task.refresh_from_db()

        assert second['finalized'] is True
        assert second['outcome'] == 'approved'
        assert task.status == 'completed'

    def test_4_approval_rejected_failure_path_triggered(self):
        WorkflowApprovalRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            approval_type='single',
            required_approvals=1,
            approval_role='hiring_manager',
            escalation_role='hr',
            timeout_hours=24,
            is_active=True,
        )
        task = WorkflowHumanTaskEngine.create_human_task(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            task_type='approval',
            title='Critical approval',
            wait_for_completion=True,
        )

        result = WorkflowHumanTaskEngine.reject_human_task(
            task=task,
            rejected_by_type='hiring_manager',
            comments='Rejected due to policy mismatch',
        )
        self.instance.refresh_from_db()
        task.refresh_from_db()

        assert result['outcome'] == 'rejected'
        assert task.status == 'rejected'
        assert self.instance.status == 'failed'

    def test_5_task_expired_escalation_triggered(self):
        task = WorkflowHumanTaskEngine.create_human_task(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            task_type='review',
            title='Expiring review task',
            due_at=timezone.now() - timedelta(minutes=5),
            wait_for_completion=True,
        )

        task = WorkflowHumanTaskEngine.expire_human_task(task=task)
        task.refresh_from_db()

        assert task.status == 'expired'
        assert bool((task.metadata or {}).get('escalated')) is True
