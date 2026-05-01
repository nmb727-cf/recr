"""
Workflow Trigger Registry + Event Mapping — Tests
==================================================

Test 1  job_created event → matching workflow instance starts
Test 2  candidate_applied with filter source=agency mismatch → filtered_out trace
Test 3  agency_submission_created → agency workflow starts
Test 4  workflow waiting on approval receives approval_received → resumes and advances
Test 5  invalid event key → rejected and logged as invalid / ignored
Test 6  (existing) job_created starts workflow and reaches wait node
Test 7  (existing) resume from waiting state completes workflow
"""
import uuid
import pytest
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowInstance,
    WorkflowStageExecution,
    WorkflowExecutionTimeline,
    WorkflowEventTrigger,
)
from apps.workflow_execution.services.workflow_execution_engine import WorkflowExecutionEngine
from apps.workflow_execution.services.workflow_event_listener import WorkflowEventListener
from apps.orchestration_center.models.workflow import Workflow, WorkflowNode, WorkflowEdge
from apps.orchestration_center.models.event_trigger import (
    WorkflowEventDefinition,
    WorkflowEventSubscription,
    WorkflowEventLog,
    WorkflowEventDebugTrace,
)


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def make_workflow(tenant_id, name, trigger_event):
    """Create an active workflow with start → action → wait → end nodes."""
    workflow = Workflow.objects.create(
        tenant_id=tenant_id,
        name=name,
        trigger_event=trigger_event,
        status='active',
        is_active=True,
    )
    start_node = WorkflowNode.objects.create(workflow=workflow, node_type='start')
    action_node = WorkflowNode.objects.create(workflow=workflow, node_type='action')
    approval_node = WorkflowNode.objects.create(workflow=workflow, node_type='approval')
    end_node = WorkflowNode.objects.create(workflow=workflow, node_type='end')

    WorkflowEdge.objects.create(workflow=workflow, source_node=start_node, target_node=action_node)
    WorkflowEdge.objects.create(workflow=workflow, source_node=action_node, target_node=approval_node)
    WorkflowEdge.objects.create(workflow=workflow, source_node=approval_node, target_node=end_node)

    return workflow, start_node, action_node, approval_node, end_node


def make_registry_entry(event_key, event_name, module_scope):
    obj, _ = WorkflowEventDefinition.objects.get_or_create(
        event_key=event_key,
        defaults={
            'event_name': event_name,
            'module_scope': module_scope,
            'is_active': True,
        },
    )
    return obj


def make_subscription(tenant_id, workflow, event_def, filters=None):
    return WorkflowEventSubscription.objects.create(
        tenant_id=tenant_id,
        workflow=workflow,
        event_definition=event_def,
        trigger_filters=filters or {},
        is_active=True,
    )


# ------------------------------------------------------------------ #
# Test 1: job_created starts matching workflow                        #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestJobCreatedStartsWorkflow:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow, *_ = make_workflow(self.tenant_id, 'Hiring Workflow', 'job_created')
        self.event_def = make_registry_entry('job_created', 'Job Created', 'jobs')
        make_subscription(self.tenant_id, self.workflow, self.event_def)

    def test_job_created_event_starts_workflow(self):
        job_id = uuid.uuid4()
        event_log = WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='job_created',
            entity_type='job',
            entity_id=job_id,
            payload={'job_id': str(job_id), 'title': 'Software Engineer'},
        )

        # Event log consumed
        assert event_log.status == 'consumed'

        # Workflow instance created and paused at approval node
        instance = WorkflowInstance.objects.filter(
            workflow_id=self.workflow.id, tenant_id=self.tenant_id
        ).first()
        assert instance is not None
        assert instance.status == 'waiting'
        assert instance.wait_reason == 'waiting_approval'

        # Debug trace shows 'started'
        traces = WorkflowEventDebugTrace.objects.filter(
            event_log=event_log, workflow=self.workflow
        )
        decisions = [t.decision for t in traces]
        assert 'started' in decisions or 'matched' in decisions


# ------------------------------------------------------------------ #
# Test 2: candidate_applied with filter mismatch → filtered_out       #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestCandidateAppliedFilterMismatch:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow, *_ = make_workflow(self.tenant_id, 'Agency Application Workflow', 'candidate_applied')
        self.event_def = make_registry_entry('candidate_applied', 'Candidate Applied', 'pipeline')
        # Filter: only trigger when source == 'agency'
        make_subscription(self.tenant_id, self.workflow, self.event_def, filters={'source': 'agency'})

    def test_non_agency_source_is_filtered_out(self):
        app_id = uuid.uuid4()
        event_log = WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='candidate_applied',
            entity_type='application',
            entity_id=app_id,
            payload={
                'application_id': str(app_id),
                'candidate_id': str(uuid.uuid4()),
                'source': 'direct',   # not 'agency' → should be filtered out
            },
        )

        # No instances created
        assert not WorkflowInstance.objects.filter(
            workflow_id=self.workflow.id, tenant_id=self.tenant_id
        ).exists()

        # Trace shows filtered_out
        trace = WorkflowEventDebugTrace.objects.filter(
            event_log=event_log, workflow=self.workflow
        ).first()
        assert trace is not None
        assert trace.decision == 'filtered_out'

        # Event log is ignored (all filtered out)
        assert event_log.status == 'ignored'

    def test_agency_source_is_matched(self):
        app_id = uuid.uuid4()
        event_log = WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='candidate_applied',
            entity_type='application',
            entity_id=app_id,
            payload={
                'application_id': str(app_id),
                'candidate_id': str(uuid.uuid4()),
                'source': 'agency',
            },
        )

        assert WorkflowInstance.objects.filter(
            workflow_id=self.workflow.id, tenant_id=self.tenant_id
        ).exists()
        assert event_log.status == 'consumed'


# ------------------------------------------------------------------ #
# Test 3: agency_submission_created starts agency workflow            #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestAgencySubmissionStartsWorkflow:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow, *_ = make_workflow(
            self.tenant_id, 'Agency Submission Workflow', 'agency_submission_created'
        )
        self.event_def = make_registry_entry(
            'agency_submission_created', 'Agency Submission Created', 'agencies'
        )
        make_subscription(self.tenant_id, self.workflow, self.event_def)

    def test_agency_submission_starts_workflow(self):
        submission_id = uuid.uuid4()
        event_log = WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='agency_submission_created',
            entity_type='agency_submission',
            entity_id=submission_id,
            payload={
                'submission_id': str(submission_id),
                'agency_id': str(uuid.uuid4()),
                'candidate_id': str(uuid.uuid4()),
                'job_id': str(uuid.uuid4()),
                'source': 'agency',
            },
        )

        assert event_log.status == 'consumed'

        instance = WorkflowInstance.objects.filter(
            workflow_id=self.workflow.id, tenant_id=self.tenant_id
        ).first()
        assert instance is not None
        assert instance.status == 'waiting'
        assert instance.entity_type == 'agency_submission'

        timeline_actions = list(
            instance.timeline_events.values_list('action', flat=True)
        )
        assert any('start' in a.lower() for a in timeline_actions)


# ------------------------------------------------------------------ #
# Test 4: waiting on approval → approval_received resumes instance   #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestApprovalReceivedResumesWorkflow:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow, *_ = make_workflow(self.tenant_id, 'Approval Workflow', 'job_created')
        self.event_def = make_registry_entry('job_created', 'Job Created', 'jobs')
        make_subscription(self.tenant_id, self.workflow, self.event_def)
        # Also register the resume event so it doesn't get rejected
        make_registry_entry('approval_received', 'Approval Received', 'approvals')

    def test_approval_received_resumes_waiting_instance(self):
        job_id = uuid.uuid4()

        # 1. Start workflow via job_created
        WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='job_created',
            entity_type='job',
            entity_id=job_id,
            payload={'job_id': str(job_id)},
        )

        instance = WorkflowInstance.objects.filter(
            workflow_id=self.workflow.id, tenant_id=self.tenant_id
        ).first()
        assert instance.status == 'waiting'
        assert instance.wait_reason == 'waiting_approval'

        # 2. Fire approval_received — should resume the waiting instance
        WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='approval_received',
            entity_type='job',
            entity_id=job_id,
            payload={'job_id': str(job_id), 'approver': 'manager'},
        )

        instance.refresh_from_db()
        assert instance.status == 'completed'

        actions = list(instance.timeline_events.values_list('action', flat=True))
        assert 'Workflow resumed' in actions
        assert 'Workflow completed successfully' in actions


# ------------------------------------------------------------------ #
# Test 5: invalid event key → rejected / logged as invalid           #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestInvalidEventKeyIsRejected:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()

    def test_unknown_event_key_is_ignored(self):
        event_log = WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='completely_made_up_event_xyz',
            entity_type='unknown',
            entity_id=uuid.uuid4(),
            payload={'foo': 'bar'},
        )

        # Event log must exist and be marked ignored
        assert event_log is not None
        assert event_log.status == 'ignored'

        # No workflow instances created
        assert not WorkflowInstance.objects.filter(tenant_id=self.tenant_id).exists()


# ------------------------------------------------------------------ #
# Test 6 (original): job_created reaches wait node                   #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestWorkflowExecutionEngine:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Test E2E Flow',
            trigger_event='job_created',
            status='active',
        )
        self.start_node = WorkflowNode.objects.create(workflow=self.workflow, node_type='start')
        self.action_node = WorkflowNode.objects.create(workflow=self.workflow, node_type='action')
        self.wait_node = WorkflowNode.objects.create(workflow=self.workflow, node_type='approval')
        self.end_node = WorkflowNode.objects.create(workflow=self.workflow, node_type='end')

        WorkflowEdge.objects.create(workflow=self.workflow, source_node=self.start_node, target_node=self.action_node)
        WorkflowEdge.objects.create(workflow=self.workflow, source_node=self.action_node, target_node=self.wait_node)
        WorkflowEdge.objects.create(workflow=self.workflow, source_node=self.wait_node, target_node=self.end_node)

        make_registry_entry('job_created', 'Job Created', 'jobs')

    def test_job_created_event_starts_workflow(self):
        event_def = WorkflowEventDefinition.objects.get(event_key='job_created')
        make_subscription(self.tenant_id, self.workflow, event_def)

        event_log = WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='job_created',
            entity_type='job',
            entity_id=uuid.uuid4(),
            payload={'job_title': 'Software Engineer'},
        )

        assert WorkflowInstance.objects.filter(workflow_id=self.workflow.id).exists()
        instance = WorkflowInstance.objects.filter(workflow_id=self.workflow.id).first()
        assert instance.status == 'waiting'
        assert instance.wait_reason == 'waiting_approval'
        assert instance.current_stage_id == self.wait_node.id

        actions = list(instance.timeline_events.values_list('action', flat=True))
        assert 'Started execution of start stage' in actions
        assert 'Started execution of action stage' in actions
        assert 'Workflow paused at approval stage' in actions

    def test_resume_waiting_stage(self):
        event_def = WorkflowEventDefinition.objects.get(event_key='job_created')
        make_subscription(self.tenant_id, self.workflow, event_def)

        WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='job_created',
            entity_type='job',
            entity_id=uuid.uuid4(),
            payload={'job_title': 'Software Engineer'},
        )

        instance = WorkflowInstance.objects.filter(workflow_id=self.workflow.id).first()
        assert instance.status == 'waiting'

        WorkflowExecutionEngine.resume_workflow(instance.id)
        instance.refresh_from_db()
        assert instance.status == 'completed'

        actions = list(instance.timeline_events.values_list('action', flat=True))
        assert 'Workflow resumed' in actions
        assert 'Workflow completed successfully' in actions


# ------------------------------------------------------------------ #
# Test 7: evaluate_trigger_filters numeric operators                  #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestTriggerFilterEvaluation:
    def test_gt_filter_passes(self):
        is_match, _, _ = WorkflowEventListener.evaluate_trigger_filters(
            {'score__gt': '70'}, {'score': 85}
        )
        assert is_match is True

    def test_gt_filter_fails(self):
        is_match, _, _ = WorkflowEventListener.evaluate_trigger_filters(
            {'score__gt': '70'}, {'score': 60}
        )
        assert is_match is False

    def test_contains_filter(self):
        is_match, _, _ = WorkflowEventListener.evaluate_trigger_filters(
            {'title__contains': 'Engineer'}, {'title': 'Software Engineer'}
        )
        assert is_match is True

    def test_no_filters_always_matches(self):
        is_match, reason, _ = WorkflowEventListener.evaluate_trigger_filters({}, {'any': 'payload'})
        assert is_match is True
        assert 'No filters' in reason
