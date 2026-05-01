"""
WorkflowStageEngine — Tests
============================

Test 1  Stage completed → next stage triggered automatically
Test 2  Approval node → WorkflowWaitState created, instance paused
Test 3  approval_received event → wait state resumed, workflow advances
Test 4  Decision logic fail → correct fallback branch selected
Test 5  Manual skip → stage skipped, workflow advances

All tests use real DB (pytest-django @pytest.mark.django_db).
"""
import uuid
import pytest
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowInstance,
    WorkflowStageExecution,
    WorkflowExecutionTimeline,
    WorkflowStageTransition,
    WorkflowWaitState,
    WorkflowTransitionLog,
)
from apps.workflow_execution.services.workflow_stage_engine import WorkflowStageEngine, ConditionEvaluator
from apps.workflow_execution.services.workflow_execution_engine import WorkflowExecutionEngine
from apps.workflow_execution.services.workflow_event_listener import WorkflowEventListener
from apps.orchestration_center.models.workflow import Workflow, WorkflowNode, WorkflowEdge
from apps.orchestration_center.models.event_trigger import (
    WorkflowEventDefinition,
    WorkflowEventSubscription,
)


# ---------------------------------------------------------------------------#
# Shared fixtures                                                              #
# ---------------------------------------------------------------------------#

def make_workflow(tenant_id, name='Test Workflow', trigger_event='job_created'):
    return Workflow.objects.create(
        tenant_id=tenant_id,
        name=name,
        trigger_event=trigger_event,
        status='active',
        is_active=True,
    )


def make_node(workflow, node_type, config=None):
    return WorkflowNode.objects.create(
        workflow=workflow,
        node_type=node_type,
        config=config or {},
    )


def make_edge(workflow, source, target, condition=None):
    return WorkflowEdge.objects.create(
        workflow=workflow,
        source_node=source,
        target_node=target,
        condition=condition or {},
    )


def make_instance(tenant_id, workflow, entity_type='job', context=None):
    return WorkflowInstance.objects.create(
        tenant_id=tenant_id,
        workflow_id=workflow.id,
        entity_type=entity_type,
        entity_id=uuid.uuid4(),
        status='running',
        context_data=context or {},
    )


def make_registry_entry(event_key, module_scope='jobs'):
    obj, _ = WorkflowEventDefinition.objects.get_or_create(
        event_key=event_key,
        defaults={
            'event_name': event_key.replace('_', ' ').title(),
            'module_scope': module_scope,
            'is_active': True,
        },
    )
    return obj


# ===========================================================================
# TEST 1 — Stage completed → next stage triggered
# ===========================================================================
@pytest.mark.django_db
class TestStageCompletedTriggersNext:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.wf = make_workflow(self.tenant_id)
        self.start   = make_node(self.wf, 'start')
        self.action  = make_node(self.wf, 'action')
        self.end     = make_node(self.wf, 'end')

        make_edge(self.wf, self.start, self.action)
        make_edge(self.wf, self.action, self.end)

    def test_auto_edge_completes_workflow(self):
        instance = make_instance(self.tenant_id, self.wf)

        WorkflowStageEngine.complete_stage(instance, self.start)

        instance.refresh_from_db()
        assert instance.status == 'completed'

        actions = list(instance.timeline_events.values_list('action', flat=True))
        assert 'Started execution of start stage' in actions
        assert 'Completed start stage' in actions
        assert 'Workflow completed successfully' in actions

    def test_transition_log_created(self):
        instance = make_instance(self.tenant_id, self.wf)
        WorkflowStageEngine.complete_stage(instance, self.start)

        logs = instance.transition_logs.all()
        assert logs.count() >= 1
        # First log: start → action
        first = logs.order_by('created_at').first()
        assert first.from_stage_id == self.start.id

    def test_stage_execution_record_created(self):
        instance = make_instance(self.tenant_id, self.wf)
        WorkflowStageEngine.complete_stage(instance, self.start)

        execs = instance.stage_executions.all()
        statuses = list(execs.values_list('status', flat=True))
        assert 'completed' in statuses

    def test_named_transition_takes_priority_over_edge(self):
        """WorkflowStageTransition rows override raw edges."""
        instance = make_instance(self.tenant_id, self.wf)

        # Create a typed transition that goes directly to end (skipping action node)
        WorkflowStageTransition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.wf.id,
            from_stage_id=self.start.id,
            to_stage_id=self.end.id,
            transition_type='auto',
            priority=0,
        )

        WorkflowStageEngine.complete_stage(instance, self.start)
        instance.refresh_from_db()
        assert instance.status == 'completed'

        # The action node should NOT have been executed
        executed_stages = list(instance.stage_executions.values_list('stage_id', flat=True))
        assert self.action.id not in executed_stages


# ===========================================================================
# TEST 2 — Approval node → wait state created
# ===========================================================================
@pytest.mark.django_db
class TestApprovalNodeCreatesWaitState:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.wf       = make_workflow(self.tenant_id)
        self.start    = make_node(self.wf, 'start')
        self.approval = make_node(self.wf, 'approval', config={'wait_reason': 'Hiring Manager Approval'})
        self.end      = make_node(self.wf, 'end')

        make_edge(self.wf, self.start, self.approval)
        make_edge(self.wf, self.approval, self.end)

    def test_approval_node_creates_wait_state(self):
        instance = make_instance(self.tenant_id, self.wf)
        WorkflowStageEngine.complete_stage(instance, self.start)

        instance.refresh_from_db()
        assert instance.status == 'waiting'
        assert instance.wait_reason == 'waiting_approval'

        # WorkflowWaitState created
        wait_states = instance.wait_states.filter(status='waiting')
        assert wait_states.count() == 1

        ws = wait_states.first()
        assert ws.wait_type == 'approval'
        assert ws.wait_reason == 'Hiring Manager Approval'

    def test_stage_execution_is_in_waiting_status(self):
        instance = make_instance(self.tenant_id, self.wf)
        WorkflowStageEngine.complete_stage(instance, self.start)

        waiting_exec = instance.stage_executions.filter(
            stage_id=self.approval.id, status='waiting'
        )
        assert waiting_exec.exists()

    def test_timeline_logged_with_wait_metadata(self):
        instance = make_instance(self.tenant_id, self.wf)
        WorkflowStageEngine.complete_stage(instance, self.start)

        pause_entry = instance.timeline_events.filter(
            action__icontains='paused'
        ).first()
        assert pause_entry is not None
        assert pause_entry.metadata.get('wait_type') == 'approval'


# ===========================================================================
# TEST 3 — approval_received event resumes the workflow
# ===========================================================================
@pytest.mark.django_db
class TestApprovalReceivedResumesWorkflow:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.wf       = make_workflow(self.tenant_id)
        self.start    = make_node(self.wf, 'start')
        self.approval = make_node(self.wf, 'approval')
        self.end      = make_node(self.wf, 'end')

        make_edge(self.wf, self.start, self.approval)
        make_edge(self.wf, self.approval, self.end)

        # Register events
        make_registry_entry('job_created', 'jobs')
        make_registry_entry('approval_received', 'approvals')

        # Subscribe workflow to trigger event
        event_def = WorkflowEventDefinition.objects.get(event_key='job_created')
        WorkflowEventSubscription.objects.create(
            tenant_id=self.tenant_id,
            workflow=self.wf,
            event_definition=event_def,
            is_active=True,
        )

    def test_approval_received_resumes_and_completes(self):
        # 1. Start workflow via job_created event
        job_id = uuid.uuid4()
        WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='job_created',
            entity_type='job',
            entity_id=job_id,
            payload={'job_id': str(job_id)},
        )

        instance = WorkflowInstance.objects.filter(
            workflow_id=self.wf.id, tenant_id=self.tenant_id
        ).first()
        assert instance.status == 'waiting'
        assert instance.wait_reason == 'waiting_approval'

        # 2. Fire approval_received → stage engine should resume
        WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='approval_received',
            entity_type='job',
            entity_id=job_id,
            payload={'job_id': str(job_id), 'approver': 'manager'},
        )

        instance.refresh_from_db()
        assert instance.status == 'completed'

        # Wait state is now resumed
        ws = instance.wait_states.first()
        assert ws.status == 'resumed'
        assert ws.resumed_by == 'event'

        # Timeline has "Workflow resumed"
        actions = list(instance.timeline_events.values_list('action', flat=True))
        assert 'Workflow resumed' in actions
        assert 'Workflow completed successfully' in actions

    def test_resume_wait_state_directly(self):
        """Resume via WorkflowStageEngine.resume_wait_state() directly."""
        instance = make_instance(self.tenant_id, self.wf)
        wait_state = WorkflowStageEngine.handle_wait_state(instance, self.approval)

        assert wait_state.status == 'waiting'

        WorkflowStageEngine.resume_wait_state(
            wait_state.id, triggered_by='user', context={'approval_note': 'OK'}
        )

        wait_state.refresh_from_db()
        instance.refresh_from_db()

        assert wait_state.status == 'resumed'
        assert wait_state.resume_context == {'approval_note': 'OK'}
        assert instance.status == 'completed'


# ===========================================================================
# TEST 4 — Decision logic: fail path selects fallback stage
# ===========================================================================
@pytest.mark.django_db
class TestDecisionLogicSelectsFallback:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.wf     = make_workflow(self.tenant_id)
        self.screen = make_node(self.wf, 'condition')
        self.pass_  = make_node(self.wf, 'action')  # "Interview 1"
        self.fail_  = make_node(self.wf, 'action')  # "Reject"
        self.end    = make_node(self.wf, 'end')

        make_edge(self.wf, self.pass_, self.end)
        make_edge(self.wf, self.fail_, self.end)

    def _make_transitions(self):
        WorkflowStageTransition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.wf.id,
            from_stage_id=self.screen.id,
            to_stage_id=self.pass_.id,
            transition_type='decision',
            label='pass',
            condition_config={'field': 'score', 'op': 'gte', 'value': 70},
            priority=0,
        )
        WorkflowStageTransition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.wf.id,
            from_stage_id=self.screen.id,
            to_stage_id=self.fail_.id,
            transition_type='decision',
            label='fail',
            condition_config={},  # matches anything (fallback)
            priority=1,
        )

    def test_high_score_takes_pass_path(self):
        self._make_transitions()
        instance = make_instance(self.tenant_id, self.wf, context={'score': 85})

        WorkflowStageEngine.move_to_next_stage(instance, self.screen)
        instance.refresh_from_db()
        assert instance.status == 'completed'

        # pass_ node was executed
        executed = list(instance.stage_executions.values_list('stage_id', flat=True))
        assert self.pass_.id in executed
        assert self.fail_.id not in executed

    def test_low_score_takes_fail_path(self):
        self._make_transitions()
        instance = make_instance(self.tenant_id, self.wf, context={'score': 45})

        WorkflowStageEngine.move_to_next_stage(instance, self.screen)
        instance.refresh_from_db()
        assert instance.status == 'completed'

        executed = list(instance.stage_executions.values_list('stage_id', flat=True))
        assert self.fail_.id in executed
        assert self.pass_.id not in executed

    def test_transition_log_captures_label(self):
        self._make_transitions()
        instance = make_instance(self.tenant_id, self.wf, context={'score': 85})
        WorkflowStageEngine.move_to_next_stage(instance, self.screen)

        log = instance.transition_logs.filter(label='pass').first()
        assert log is not None

    def test_and_condition_group(self):
        ok, reason, trace = ConditionEvaluator.evaluate(
            {
                'operator': 'and',
                'conditions': [
                    {'field': 'score', 'op': 'gt', 'value': 70},
                    {'field': 'department', 'op': 'eq', 'value': 'engineering'},
                ],
            },
            {'score': 85, 'department': 'engineering'},
        )
        assert ok is True
        assert 'AND' in reason

    def test_and_condition_group_fails_if_one_fails(self):
        ok, _, _ = ConditionEvaluator.evaluate(
            {
                'operator': 'and',
                'conditions': [
                    {'field': 'score', 'op': 'gt', 'value': 70},
                    {'field': 'department', 'op': 'eq', 'value': 'engineering'},
                ],
            },
            {'score': 85, 'department': 'marketing'},
        )
        assert ok is False

    def test_or_condition_group(self):
        ok, _, _ = ConditionEvaluator.evaluate(
            {
                'operator': 'or',
                'conditions': [
                    {'field': 'source', 'op': 'eq', 'value': 'agency'},
                    {'field': 'score', 'op': 'gte', 'value': 90},
                ],
            },
            {'source': 'direct', 'score': 95},
        )
        assert ok is True


# ===========================================================================
# TEST 5 — Manual skip → stage skipped, workflow advances
# ===========================================================================
@pytest.mark.django_db
class TestManualSkipAdvancesWorkflow:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.wf       = make_workflow(self.tenant_id)
        self.start    = make_node(self.wf, 'start')
        self.approval = make_node(self.wf, 'approval')
        self.action   = make_node(self.wf, 'action')
        self.end      = make_node(self.wf, 'end')

        make_edge(self.wf, self.start, self.approval)
        make_edge(self.wf, self.approval, self.action)
        make_edge(self.wf, self.action, self.end)

    def test_skip_waiting_stage_advances_to_next(self):
        instance = make_instance(self.tenant_id, self.wf)

        # Move to wait state at approval
        WorkflowStageEngine.complete_stage(instance, self.start)
        instance.refresh_from_db()
        assert instance.status == 'waiting'

        # Skip the approval stage
        WorkflowStageEngine.skip_stage(
            instance,
            stage_id=self.approval.id,
            reason='Client waived approval',
            triggered_by='user',
        )

        instance.refresh_from_db()
        assert instance.status == 'completed'

        # Approval stage exec is skipped
        approval_exec = instance.stage_executions.filter(stage_id=self.approval.id).first()
        assert approval_exec is not None
        assert approval_exec.status == 'skipped'

        # Wait state cancelled
        ws = instance.wait_states.filter(stage_execution=approval_exec).first()
        if ws:
            assert ws.status == 'cancelled'

    def test_skip_creates_transition_log(self):
        instance = make_instance(self.tenant_id, self.wf)
        WorkflowStageEngine.complete_stage(instance, self.start)

        WorkflowStageEngine.skip_stage(
            instance,
            stage_id=self.approval.id,
            reason='Bypass for testing',
        )

        skip_log = instance.transition_logs.filter(label='skip').first()
        assert skip_log is not None
        assert skip_log.reason == 'Bypass for testing'

    def test_skip_timeline_entry_created(self):
        instance = make_instance(self.tenant_id, self.wf)
        WorkflowStageEngine.complete_stage(instance, self.start)

        WorkflowStageEngine.skip_stage(instance, stage_id=self.approval.id)

        skip_event = instance.timeline_events.filter(action__icontains='skipped').first()
        assert skip_event is not None


# ===========================================================================
# Regression — existing execution engine tests still pass
# ===========================================================================
@pytest.mark.django_db
class TestExecutionEngineBackwardsCompat:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.wf      = make_workflow(self.tenant_id)
        self.start   = make_node(self.wf, 'start')
        self.action  = make_node(self.wf, 'action')
        self.wait    = make_node(self.wf, 'approval')
        self.end     = make_node(self.wf, 'end')

        make_edge(self.wf, self.start, self.action)
        make_edge(self.wf, self.action, self.wait)
        make_edge(self.wf, self.wait, self.end)

    def test_start_instance_reaches_wait(self):
        instance = WorkflowExecutionEngine.start_workflow_instance(
            self.tenant_id, self.wf.id, 'job', uuid.uuid4()
        )
        instance.refresh_from_db()
        assert instance.status == 'waiting'
        assert instance.wait_reason == 'waiting_approval'

    def test_resume_workflow_completes(self):
        instance = WorkflowExecutionEngine.start_workflow_instance(
            self.tenant_id, self.wf.id, 'job', uuid.uuid4()
        )
        assert instance.status == 'waiting'

        WorkflowExecutionEngine.resume_workflow(instance.id)
        instance.refresh_from_db()
        assert instance.status == 'completed'
