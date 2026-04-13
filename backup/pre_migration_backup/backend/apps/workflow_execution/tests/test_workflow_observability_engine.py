import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.orchestration_center.models.workflow import Workflow, WorkflowNode
from apps.workflow_execution.models import (
    WorkflowActionDefinition,
    WorkflowExecutionTimelineEntry,
    WorkflowExecutionTrace,
    WorkflowObservabilitySnapshot,
    WorkflowStageSLA,
)
from apps.workflow_execution.services.workflow_action_handlers_engine import WorkflowActionHandlersEngine
from apps.workflow_execution.services.workflow_execution_engine import WorkflowExecutionEngine
from apps.workflow_execution.services.workflow_execution_orchestrator import WorkflowExecutionOrchestrator
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.workflow_execution.services.workflow_observability_engine import WorkflowObservabilityEngine
from apps.workflow_execution.services.workflow_sla_engine import WorkflowSLAEngine


class TestWorkflowObservabilityEngine(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Observability WF',
            trigger_event='job_created',
            status='active',
            is_active=True,
        )
        self.start = WorkflowNode.objects.create(workflow=self.workflow, node_type='start', config={'label': 'Start'})
        self.stage = WorkflowNode.objects.create(workflow=self.workflow, node_type='action', config={'label': 'Review'})
        self.end = WorkflowNode.objects.create(workflow=self.workflow, node_type='end', config={'label': 'End'})

    def _create_instance(self):
        return WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='candidate',
            entity_id=uuid.uuid4(),
            status='running',
        )

    def test_1_workflow_start_creates_workflow_started_timeline_entry(self):
        instance = self._create_instance()
        assert WorkflowExecutionTimelineEntry.objects.filter(
            workflow_instance=instance,
            entry_type='workflow_started',
        ).exists()

    def test_2_stage_transition_creates_stage_completed_and_transition_taken_entries(self):
        instance = self._create_instance()
        stage_execution = WorkflowInstanceTracker.start_stage_execution(
            instance,
            stage_id=self.stage.id,
            stage_name='Review Candidate',
        )
        WorkflowInstanceTracker.complete_stage_execution(stage_execution)
        WorkflowInstanceTracker.log_transition(
            instance,
            from_stage='Review Candidate',
            to_stage='Interview',
            transition_type='automatic',
            triggered_by='system',
        )

        entry_types = set(
            WorkflowExecutionTimelineEntry.objects.filter(workflow_instance=instance).values_list('entry_type', flat=True)
        )
        assert 'stage_completed' in entry_types
        assert 'transition_taken' in entry_types

    def test_3_wait_state_created_and_resumed_entries_present(self):
        instance = self._create_instance()
        stage_execution = WorkflowInstanceTracker.start_stage_execution(
            instance,
            stage_id=self.stage.id,
            stage_name='Approval Stage',
        )
        wait_state = WorkflowInstanceTracker.create_wait_state(
            instance,
            stage_execution=stage_execution,
            wait_type='approval',
            wait_reason='Waiting for hiring manager approval',
        )
        WorkflowInstanceTracker.resume_wait_state(wait_state, actor_type='user')

        entry_types = set(
            WorkflowExecutionTimelineEntry.objects.filter(workflow_instance=instance).values_list('entry_type', flat=True)
        )
        assert 'wait_started' in entry_types
        assert 'wait_resumed' in entry_types

    def test_4_action_executed_records_action_trace_and_timeline(self):
        instance = self._create_instance()
        stage_execution = WorkflowInstanceTracker.start_stage_execution(
            instance,
            stage_id=self.stage.id,
            stage_name='Action Stage',
        )
        action = WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            action_name='Create Task',
            action_type='create_task',
            action_config={'title': 'Review profile'},
            execution_order=1,
            run_mode='immediate',
            is_active=True,
        )
        WorkflowActionHandlersEngine.execute_action(
            instance=instance,
            stage_execution=stage_execution,
            action_definition=action,
            action_context={},
        )

        assert WorkflowExecutionTimelineEntry.objects.filter(
            workflow_instance=instance,
            entry_type='action_executed',
        ).exists()
        assert WorkflowExecutionTrace.objects.filter(
            workflow_instance=instance,
            trace_type='action',
        ).exists()

    def test_5_failure_logs_timeline_error_trace_and_snapshot_flag(self):
        instance = self._create_instance()
        stage_execution = WorkflowInstanceTracker.start_stage_execution(
            instance,
            stage_id=self.stage.id,
            stage_name='Fail Stage',
        )
        WorkflowInstanceTracker.log_failure(
            instance,
            stage_execution=stage_execution,
            error_message='Action crashed',
            error_type='runtime_error',
            retry_count=0,
            status='failed',
        )
        snapshot = WorkflowObservabilityEngine.get_instance_snapshot(instance.id)
        assert WorkflowExecutionTimelineEntry.objects.filter(
            workflow_instance=instance,
            entry_type='failure_logged',
        ).exists()
        assert WorkflowExecutionTrace.objects.filter(
            workflow_instance=instance,
            trace_type='failure',
            severity='error',
        ).exists()
        assert snapshot is not None and snapshot.has_failure is True

    def test_6_sla_warning_recorded_and_health_shows_risk(self):
        instance = self._create_instance()
        stage_execution = WorkflowInstanceTracker.start_stage_execution(
            instance,
            stage_id=self.stage.id,
            stage_name='SLA Stage',
        )
        WorkflowStageSLA.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            sla_duration=timedelta(hours=24),
            warning_duration=timedelta(hours=1),
            escalation_duration=timedelta(hours=24),
            escalation_role='hiring_manager',
            is_active=True,
        )
        tracker = WorkflowSLAEngine.initialize_sla(instance, stage_execution)
        tracker.warning_at = timezone.now() - timedelta(minutes=1)
        tracker.breach_at = timezone.now() + timedelta(hours=1)
        tracker.save(update_fields=['warning_at', 'breach_at', 'updated_at'])
        WorkflowSLAEngine.check_sla_status(tracker=tracker)

        health = WorkflowObservabilityEngine.summarize_execution_health(instance.id)
        assert WorkflowExecutionTimelineEntry.objects.filter(
            workflow_instance=instance,
            entry_type='sla_warning',
        ).exists()
        assert health is not None and health['has_sla_risk'] is True

    def test_7_workflow_complete_creates_final_timeline_and_snapshot(self):
        instance = self._create_instance()
        WorkflowExecutionOrchestrator.complete_workflow_instance(instance, reason='Workflow finished')
        instance.refresh_from_db()
        snapshot = WorkflowObservabilityEngine.get_instance_snapshot(instance.id)
        assert WorkflowExecutionTimelineEntry.objects.filter(
            workflow_instance=instance,
            entry_type='workflow_completed',
        ).exists()
        assert snapshot is not None
        assert snapshot.current_status == 'completed'
