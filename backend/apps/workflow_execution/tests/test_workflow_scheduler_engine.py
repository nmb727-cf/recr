import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowInstance,
    WorkflowScheduledTask,
    WorkflowStageExecution,
    WorkflowStageSLA,
)
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.workflow_execution.services.workflow_scheduler_engine import WorkflowSchedulerEngine
from apps.workflow_execution.services.workflow_sla_engine import WorkflowSLAEngine


@pytest.mark.django_db
class TestWorkflowSchedulerEngine:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow_id = uuid.uuid4()
        self.stage_id = uuid.uuid4()
        self.instance = WorkflowInstance.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow_id,
            entity_type='candidate',
            entity_id=uuid.uuid4(),
            status='running',
        )
        self.stage_execution = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_id=self.stage_id,
            stage_name='candidate_follow_up',
            status='waiting',
        )

    def test_1_wait_state_created_schedules_resume_task(self):
        timeout_at = timezone.now() + timedelta(hours=24)
        WorkflowInstanceTracker.create_wait_state(
            self.instance,
            stage_execution=self.stage_execution,
            wait_type='candidate_response',
            wait_reason='awaiting candidate response',
            timeout_at=timeout_at,
            metadata={},
        )
        assert WorkflowScheduledTask.objects.filter(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            task_type='wait_resume',
            status='scheduled',
        ).exists()

    def test_2_retry_scheduled_creates_retry_task(self):
        task = WorkflowSchedulerEngine.schedule_task(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            task_type='retry_stage',
            scheduled_at=timezone.now() + timedelta(hours=2),
            payload={'context': {}, 'max_retries': 2},
        )
        assert task.task_type == 'retry_stage'
        assert task.status == 'scheduled'

    def test_3_sla_check_scheduled_creates_periodic_task(self):
        WorkflowStageSLA.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow_id,
            stage_id=self.stage_id,
            sla_duration=timedelta(hours=48),
            warning_duration=timedelta(hours=24),
            escalation_duration=timedelta(hours=48),
            escalation_role='hiring_manager',
            is_active=True,
        )
        WorkflowSLAEngine.initialize_sla(self.instance, self.stage_execution)
        assert WorkflowScheduledTask.objects.filter(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            task_type='sla_check',
            status='scheduled',
        ).exists()

    def test_4_scheduled_execution_runs_at_scheduled_time(self):
        task = WorkflowSchedulerEngine.schedule_task(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            task_type='notification_dispatch',
            scheduled_at=timezone.now() - timedelta(minutes=1),
            payload={'limit': 10},
        )
        processed = WorkflowSchedulerEngine.process_due_tasks(limit=10)
        task.refresh_from_db()
        assert any(str(item.id) == str(task.id) for item in processed)
        assert task.status == 'completed'
        assert task.executed_at is not None

    def test_5_failed_task_triggers_retry_logic(self, monkeypatch):
        task = WorkflowSchedulerEngine.schedule_task(
            workflow_instance=self.instance,
            stage_execution=self.stage_execution,
            task_type='notification_dispatch',
            scheduled_at=timezone.now() - timedelta(minutes=1),
            payload={'max_retries': 2, 'retry_delay_seconds': 60},
        )

        def _raise(_task):
            raise RuntimeError('forced scheduler failure')

        monkeypatch.setattr(WorkflowSchedulerEngine, '_execute_task_action', staticmethod(_raise))
        WorkflowSchedulerEngine.execute_scheduled_task(task.id)
        task.refresh_from_db()
        assert task.retry_count == 1
        assert task.status == 'scheduled'
