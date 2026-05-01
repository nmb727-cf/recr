import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.orchestration_center.models.workflow import Workflow, WorkflowEdge, WorkflowNode
from apps.workflow_execution.models import (
    WorkflowInstance,
    WorkflowSLAEvent,
    WorkflowSLATracker,
    WorkflowStageExecution,
    WorkflowStageSLA,
)
from apps.workflow_execution.services.workflow_sla_engine import WorkflowSLAEngine


def make_workflow(tenant_id):
    workflow = Workflow.objects.create(
        tenant_id=tenant_id,
        name='SLA Engine WF',
        trigger_event='job_created',
        status='active',
        is_active=True,
    )
    start = WorkflowNode.objects.create(workflow=workflow, node_type='start')
    action = WorkflowNode.objects.create(workflow=workflow, node_type='action')
    WorkflowEdge.objects.create(workflow=workflow, source_node=start, target_node=action)
    return workflow, start, action


@pytest.mark.django_db
class TestWorkflowSLAEngine:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow, self.start, self.action = make_workflow(self.tenant_id)
        self.instance = WorkflowInstance.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='job',
            entity_id=uuid.uuid4(),
            status='running',
        )
        self.stage_execution = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_id=self.action.id,
            stage_name='action',
            status='running',
        )
        self.stage_sla = WorkflowStageSLA.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.action.id,
            sla_duration=timedelta(hours=48),
            warning_duration=timedelta(hours=36),
            escalation_duration=timedelta(hours=48),
            escalation_role='hiring_manager',
            is_active=True,
        )

    def test_1_stage_starts_sla_initialized(self):
        tracker = WorkflowSLAEngine.initialize_sla(self.instance, self.stage_execution)
        assert tracker is not None
        assert tracker.status == 'active'

    def test_2_warning_reached_warning_event(self):
        tracker = WorkflowSLAEngine.initialize_sla(self.instance, self.stage_execution)
        tracker.warning_at = timezone.now() - timedelta(minutes=1)
        tracker.breach_at = timezone.now() + timedelta(hours=1)
        tracker.save(update_fields=['warning_at', 'breach_at', 'updated_at'])

        events = WorkflowSLAEngine.check_sla_status(tracker=tracker)
        tracker.refresh_from_db()

        assert any(e['event'] == 'warning' for e in events)
        assert tracker.status == 'warning'
        assert WorkflowSLAEvent.objects.filter(workflow_instance=self.instance, event_type='warning').exists()

    def test_3_breach_reached_breach_event(self):
        tracker = WorkflowSLAEngine.initialize_sla(self.instance, self.stage_execution)
        tracker.warning_at = timezone.now() - timedelta(hours=2)
        tracker.breach_at = timezone.now() - timedelta(minutes=1)
        tracker.stage_sla.escalation_duration = timedelta(days=10)
        tracker.stage_sla.save(update_fields=['escalation_duration', 'updated_at'])
        tracker.save(update_fields=['warning_at', 'breach_at', 'updated_at'])

        events = WorkflowSLAEngine.check_sla_status(tracker=tracker)
        tracker.refresh_from_db()

        assert any(e['event'] == 'breach' for e in events)
        assert tracker.status == 'breached'
        assert WorkflowSLAEvent.objects.filter(workflow_instance=self.instance, event_type='breach').exists()

    def test_4_escalation_reached_escalation_triggered(self):
        tracker = WorkflowSLAEngine.initialize_sla(self.instance, self.stage_execution)
        tracker.status = 'breached'
        tracker.sla_start = timezone.now() - timedelta(hours=2)
        tracker.stage_sla.escalation_duration = timedelta(minutes=30)
        tracker.stage_sla.save(update_fields=['escalation_duration', 'updated_at'])
        tracker.save(update_fields=['status', 'sla_start', 'updated_at'])

        events = WorkflowSLAEngine.check_sla_status(tracker=tracker)
        tracker.refresh_from_db()

        assert any(e['event'] == 'escalation' for e in events)
        assert tracker.status == 'escalated'
        assert WorkflowSLAEvent.objects.filter(workflow_instance=self.instance, event_type='escalation').exists()

    def test_5_stage_completes_sla_resolved(self):
        tracker = WorkflowSLAEngine.initialize_sla(self.instance, self.stage_execution)
        resolved = WorkflowSLAEngine.resolve_sla(self.instance, self.stage_execution)

        tracker.refresh_from_db()
        assert resolved is not None
        assert tracker.status == 'resolved'
        assert WorkflowSLAEvent.objects.filter(workflow_instance=self.instance, event_type='resolved').exists()
