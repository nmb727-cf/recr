"""
WorkflowCrossEntityRoutingEngine — Tests
==========================================

Test 1  Agency submission routed to company recruiter → route created, workflow continues
Test 2  Company→agency interview coordination → handoff checkpoint created, resumes on response
Test 3  Offer accepted → HR actor assignment created + onboarding handoff initiated
Test 4  Cross-tenant/invalid route pair → blocked, logged as failed, no route persisted
Test 5  HRMS handoff completed via event → workflow instance advances to completed

All tests use real DB (pytest-django @pytest.mark.django_db).
"""
import uuid
import pytest

from apps.workflow_execution.models import (
    WorkflowInstance,
    WorkflowStageExecution,
    WorkflowEntityRoute,
    WorkflowActorAssignment,
    WorkflowHandoffCheckpoint,
    WorkflowRoutingRule,
    WorkflowRouteTimelineLog,
)
from apps.workflow_execution.services.workflow_cross_entity_routing_engine import (
    WorkflowCrossEntityRoutingEngine,
    ALLOWED_ROUTE_PAIRS,
)
from apps.orchestration_center.models.workflow import Workflow, WorkflowNode


# ---------------------------------------------------------------------------#
# Shared fixtures                                                              #
# ---------------------------------------------------------------------------#

def make_workflow(tenant_id, name='Routing Test Workflow'):
    return Workflow.objects.create(
        tenant_id=tenant_id,
        name=name,
        trigger_event='application_submitted',
        status='active',
        is_active=True,
    )


def make_node(workflow, node_type, config=None):
    return WorkflowNode.objects.create(
        workflow=workflow,
        node_type=node_type,
        config=config or {},
    )


def make_instance(tenant_id, workflow, entity_type='company', status='running', context=None):
    return WorkflowInstance.objects.create(
        tenant_id=tenant_id,
        workflow_id=workflow.id,
        entity_type=entity_type,
        entity_id=uuid.uuid4(),
        status=status,
        context_data=context or {},
    )


def make_stage_execution(instance, node, status='completed'):
    return WorkflowStageExecution.objects.create(
        tenant_id=instance.tenant_id,
        workflow_instance=instance,
        stage_id=node.id,
        status=status,
    )


# ===========================================================================
# TEST 1 — Agency submission routed to company recruiter
# ===========================================================================
@pytest.mark.django_db
class TestAgencyToCompanyRecruiterRoute:
    """
    Scenario: Agency submits a candidate → system creates a company→agency route
    and assigns a recruiter actor for the intake stage.
    """

    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.wf = make_workflow(self.tenant_id, name='Agency Intake Workflow')
        self.intake_node = make_node(self.wf, 'human_task')
        self.instance = make_instance(self.tenant_id, self.wf, entity_type='company')

    def test_route_created_from_agency_to_company(self):
        route, error = WorkflowCrossEntityRoutingEngine.create_entity_route(
            self.instance,
            from_entity_type='agency',
            to_entity_type='company',
            route_type='action_handoff',
            route_reason='Agency submitted candidate for review',
            stage_id=self.intake_node.id,
        )

        assert error is None
        assert route is not None
        assert route.from_entity_type == 'agency'
        assert route.to_entity_type == 'company'
        assert route.status == 'active'
        assert route.workflow_instance == self.instance

    def test_recruiter_actor_assigned_to_intake_stage(self):
        recruiter_id = uuid.uuid4()

        assignment = WorkflowCrossEntityRoutingEngine.assign_actor_for_stage(
            self.instance,
            stage_id=self.intake_node.id,
            actor_type='recruiter',
            actor_id=recruiter_id,
            assignment_type='responsible',
            notes='Company recruiter assigned for agency intake review',
        )

        assert assignment.status == 'active'
        assert assignment.actor_type == 'recruiter'
        assert assignment.actor_id == recruiter_id
        assert assignment.assignment_type == 'responsible'

    def test_previous_responsible_revoked_on_reassign(self):
        old_recruiter = uuid.uuid4()
        new_recruiter = uuid.uuid4()

        WorkflowCrossEntityRoutingEngine.assign_actor_for_stage(
            self.instance,
            stage_id=self.intake_node.id,
            actor_type='recruiter',
            actor_id=old_recruiter,
            assignment_type='responsible',
        )
        WorkflowCrossEntityRoutingEngine.assign_actor_for_stage(
            self.instance,
            stage_id=self.intake_node.id,
            actor_type='recruiter',
            actor_id=new_recruiter,
            assignment_type='responsible',
        )

        active = WorkflowActorAssignment.objects.filter(
            workflow_instance=self.instance,
            stage_id=self.intake_node.id,
            assignment_type='responsible',
            status='active',
        )
        assert active.count() == 1
        assert active.first().actor_id == new_recruiter

    def test_route_timeline_log_written(self):
        WorkflowCrossEntityRoutingEngine.create_entity_route(
            self.instance,
            from_entity_type='agency',
            to_entity_type='company',
            route_type='action_handoff',
            route_reason='Agency submission',
        )

        logs = WorkflowRouteTimelineLog.objects.filter(workflow_instance=self.instance)
        assert logs.exists()
        assert 'agency' in logs.first().from_actor

    def test_routing_rule_matches_context_and_assigns_recruiter(self):
        WorkflowRoutingRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.wf.id,
            stage_id=self.intake_node.id,
            condition_config={'field': 'source', 'op': 'eq', 'value': 'agency'},
            route_to_entity_type='company',
            route_to_actor_type='recruiter',
            route_config={'assignment_type': 'responsible'},
            priority=0,
            label='Agency→Company recruiter rule',
            is_active=True,
        )

        instance_with_context = make_instance(
            self.tenant_id, self.wf,
            context={'source': 'agency'},
        )

        matched_rule = WorkflowCrossEntityRoutingEngine.determine_next_route(
            instance_with_context, stage_id=self.intake_node.id
        )

        assert matched_rule is not None
        assert matched_rule.route_to_actor_type == 'recruiter'


# ===========================================================================
# TEST 2 — Company→agency interview coordination handoff
# ===========================================================================
@pytest.mark.django_db
class TestCompanyToAgencyInterviewHandoff:
    """
    Scenario: Company coordinates an interview through an agency → handoff
    checkpoint created, workflow waits for agency's scheduling response.
    """

    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.wf = make_workflow(self.tenant_id, name='Interview Coordination Workflow')
        self.schedule_node = make_node(self.wf, 'scheduling')
        self.instance = make_instance(self.tenant_id, self.wf, entity_type='company')
        self.stage_exec = make_stage_execution(self.instance, self.schedule_node, status='waiting')

    def test_handoff_checkpoint_created_for_agency_coordination(self):
        checkpoint, route = WorkflowCrossEntityRoutingEngine.handoff_stage_control(
            self.instance,
            stage_execution=self.stage_exec,
            from_entity='company',
            to_entity='agency',
            handoff_type='company_to_agency',
            payload={'interview_date': '2026-05-01', 'candidate_id': str(uuid.uuid4())},
            expected_response_event='interview_scheduled',
            reason='Agency to schedule interview with candidate',
        )

        assert checkpoint is not None
        assert checkpoint.handoff_type == 'company_to_agency'
        assert checkpoint.expected_response_event == 'interview_scheduled'
        assert checkpoint.status == 'pending'
        assert route is not None
        assert route.to_entity_type == 'agency'

    def test_checkpoint_resumes_on_event_completion(self):
        checkpoint, _ = WorkflowCrossEntityRoutingEngine.handoff_stage_control(
            self.instance,
            stage_execution=self.stage_exec,
            from_entity='company',
            to_entity='agency',
            handoff_type='company_to_agency',
            expected_response_event='interview_scheduled',
        )

        # Agency responds — complete the handoff
        completed = WorkflowCrossEntityRoutingEngine.complete_handoff(
            checkpoint.id,
            response_payload={'scheduled_at': '2026-05-01T10:00:00Z'},
        )

        assert completed.status == 'completed'
        checkpoint.refresh_from_db()
        assert checkpoint.status == 'completed'
        assert 'scheduled_at' in checkpoint.response_payload

    def test_bulk_complete_handoffs_by_event_key(self):
        checkpoint, _ = WorkflowCrossEntityRoutingEngine.handoff_stage_control(
            self.instance,
            stage_execution=self.stage_exec,
            from_entity='company',
            to_entity='agency',
            handoff_type='company_to_agency',
            expected_response_event='interview_scheduled',
        )

        completed_ids = WorkflowCrossEntityRoutingEngine.complete_handoff_by_event(
            event_key='interview_scheduled',
            tenant_id=self.tenant_id,
            payload={'result': 'scheduled'},
        )

        assert checkpoint.id in completed_ids
        checkpoint.refresh_from_db()
        assert checkpoint.status == 'completed'

    def test_failed_handoff_marks_route_and_checkpoint_failed(self):
        checkpoint, _ = WorkflowCrossEntityRoutingEngine.handoff_stage_control(
            self.instance,
            stage_execution=self.stage_exec,
            from_entity='company',
            to_entity='agency',
            handoff_type='company_to_agency',
            expected_response_event='interview_scheduled',
        )

        WorkflowCrossEntityRoutingEngine.fail_handoff(
            checkpoint.id, reason='Agency did not respond'
        )

        checkpoint.refresh_from_db()
        assert checkpoint.status == 'failed'

        route = self.instance.entity_routes.filter(to_entity_type='agency').first()
        assert route is not None
        assert route.status == 'failed'


# ===========================================================================
# TEST 3 — Offer accepted → HR actor assignment + onboarding handoff
# ===========================================================================
@pytest.mark.django_db
class TestOfferAcceptedRoutesToOnboarding:
    """
    Scenario: Candidate accepts offer → route_to_onboarding() shortcut assigns
    HR actor and creates company → onboarding handoff checkpoint.
    """

    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.wf = make_workflow(self.tenant_id, name='Offer + Onboarding Workflow')
        self.onboarding_node = make_node(self.wf, 'action')
        self.instance = make_instance(
            self.tenant_id, self.wf,
            entity_type='company',
            status='running',
            context={'candidate_name': 'Alice', 'offer_id': str(uuid.uuid4())},
        )

    def test_route_to_onboarding_creates_hr_assignment(self):
        hr_actor_id = uuid.uuid4()

        WorkflowCrossEntityRoutingEngine.route_to_onboarding(
            self.instance,
            stage_id=self.onboarding_node.id,
            hr_actor_id=hr_actor_id,
        )

        assignment = WorkflowActorAssignment.objects.filter(
            workflow_instance=self.instance,
            stage_id=self.onboarding_node.id,
            actor_type='hr',
            status='active',
        ).first()

        assert assignment is not None
        assert assignment.actor_id == hr_actor_id
        assert assignment.assignment_type == 'responsible'

    def test_route_to_onboarding_creates_company_hr_route(self):
        WorkflowCrossEntityRoutingEngine.route_to_onboarding(
            self.instance,
            stage_id=self.onboarding_node.id,
        )

        route = self.instance.entity_routes.filter(
            from_entity_type='company',
            to_entity_type='hr',
        ).first()

        assert route is not None
        assert route.route_type == 'onboarding_handoff'

    def test_route_to_onboarding_creates_checkpoint_with_correct_event(self):
        WorkflowCrossEntityRoutingEngine.route_to_onboarding(
            self.instance,
            stage_id=self.onboarding_node.id,
            payload={'offer_accepted': True},
        )

        checkpoint = self.instance.handoff_checkpoints.filter(
            handoff_type='company_to_hr',
        ).first()

        assert checkpoint is not None
        assert checkpoint.expected_response_event == 'onboarding_started'
        assert checkpoint.status == 'pending'

    def test_actor_assignment_not_created_without_stage_id(self):
        WorkflowCrossEntityRoutingEngine.route_to_onboarding(
            self.instance,
            stage_id=None,
        )

        assignments = WorkflowActorAssignment.objects.filter(
            workflow_instance=self.instance,
            actor_type='hr',
        )
        assert assignments.count() == 0  # No stage_id → no assignment


# ===========================================================================
# TEST 4 — Cross-tenant / invalid route pair blocked
# ===========================================================================
@pytest.mark.django_db
class TestInvalidRoutePairBlocked:
    """
    Scenario: Code tries to create a route between disallowed entity pairs
    (e.g. candidate → hrms directly, or agency → hr).
    The engine must reject this and write a failed timeline entry.
    """

    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.wf = make_workflow(self.tenant_id)
        self.instance = make_instance(self.tenant_id, self.wf)

    def test_candidate_to_hrms_direct_is_blocked(self):
        route, error = WorkflowCrossEntityRoutingEngine.create_entity_route(
            self.instance,
            from_entity_type='candidate',
            to_entity_type='hrms',
        )

        assert route is None
        assert error is not None
        assert 'not permitted' in error

    def test_agency_to_hr_direct_is_blocked(self):
        route, error = WorkflowCrossEntityRoutingEngine.create_entity_route(
            self.instance,
            from_entity_type='agency',
            to_entity_type='hr',
        )

        assert route is None
        assert error is not None

    def test_blocked_route_writes_timeline_log(self):
        before_count = WorkflowRouteTimelineLog.objects.filter(
            workflow_instance=self.instance
        ).count()

        WorkflowCrossEntityRoutingEngine.create_entity_route(
            self.instance,
            from_entity_type='candidate',
            to_entity_type='hrms',
        )

        after_count = WorkflowRouteTimelineLog.objects.filter(
            workflow_instance=self.instance
        ).count()

        assert after_count == before_count + 1
        log = WorkflowRouteTimelineLog.objects.filter(
            workflow_instance=self.instance
        ).latest('created_at')
        assert 'blocked' in log.action.lower()

    def test_same_entity_type_is_always_allowed(self):
        """Intra-entity routing (e.g., company → company) must always pass validation."""
        is_valid, error = WorkflowCrossEntityRoutingEngine.validate_cross_entity_route(
            self.instance, 'company', 'company'
        )
        assert is_valid is True
        assert error is None

    def test_validate_returns_error_for_disallowed_pair(self):
        is_valid, error = WorkflowCrossEntityRoutingEngine.validate_cross_entity_route(
            self.instance, 'candidate', 'hrms'
        )
        assert is_valid is False
        assert "not permitted" in error

    def test_no_entity_route_row_created_for_blocked_route(self):
        before = WorkflowEntityRoute.objects.filter(workflow_instance=self.instance).count()

        WorkflowCrossEntityRoutingEngine.create_entity_route(
            self.instance,
            from_entity_type='agency',
            to_entity_type='hr',
        )

        after = WorkflowEntityRoute.objects.filter(workflow_instance=self.instance).count()
        assert after == before  # Nothing persisted


# ===========================================================================
# TEST 5 — HRMS handoff completed → workflow moves to completed
# ===========================================================================
@pytest.mark.django_db
class TestHrmsHandoffCompletesWorkflow:
    """
    Scenario: route_to_hrms() creates onboarding→HRMS handoff.
    Completing it via complete_handoff_by_event() merges response payload
    into instance context and resumes the waiting instance.
    """

    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.wf = make_workflow(self.tenant_id, name='HRMS Closure Workflow')
        self.close_node = make_node(self.wf, 'end')
        self.instance = make_instance(
            self.tenant_id, self.wf,
            entity_type='company',
            status='waiting',
            context={'employee_id': str(uuid.uuid4())},
        )

    def test_route_to_hrms_creates_onboarding_hrms_route(self):
        WorkflowCrossEntityRoutingEngine.route_to_hrms(
            self.instance,
            stage_id=self.close_node.id,
            hrms_payload={'employee_id': str(uuid.uuid4())},
        )

        route = self.instance.entity_routes.filter(
            from_entity_type='onboarding',
            to_entity_type='hrms',
        ).first()

        assert route is not None
        assert route.route_type == 'onboarding_handoff'

    def test_route_to_hrms_creates_checkpoint_with_hrms_event(self):
        WorkflowCrossEntityRoutingEngine.route_to_hrms(
            self.instance,
            stage_id=self.close_node.id,
        )

        checkpoint = self.instance.handoff_checkpoints.filter(
            handoff_type='workflow_to_hrms',
        ).first()

        assert checkpoint is not None
        assert checkpoint.expected_response_event == 'hrms_handoff_ready'
        assert checkpoint.status == 'pending'

    def test_complete_hrms_handoff_merges_response_into_context(self):
        WorkflowCrossEntityRoutingEngine.route_to_hrms(
            self.instance,
            stage_id=self.close_node.id,
        )
        checkpoint = self.instance.handoff_checkpoints.filter(
            handoff_type='workflow_to_hrms'
        ).first()
        assert checkpoint is not None

        hrms_response = {'hrms_record_id': 'HRMS-12345', 'status': 'created'}
        WorkflowCrossEntityRoutingEngine.complete_handoff(
            checkpoint.id,
            response_payload=hrms_response,
        )

        self.instance.refresh_from_db()
        assert self.instance.context_data.get('hrms_record_id') == 'HRMS-12345'

    def test_bulk_complete_hrms_handoff_by_event(self):
        WorkflowCrossEntityRoutingEngine.route_to_hrms(
            self.instance,
            stage_id=self.close_node.id,
        )
        checkpoint = self.instance.handoff_checkpoints.filter(
            handoff_type='workflow_to_hrms'
        ).first()

        completed_ids = WorkflowCrossEntityRoutingEngine.complete_handoff_by_event(
            event_key='hrms_handoff_ready',
            tenant_id=self.tenant_id,
            payload={'hrms_record_id': 'HRMS-99999'},
        )

        assert checkpoint.id in completed_ids
        checkpoint.refresh_from_db()
        assert checkpoint.status == 'completed'

    def test_hrms_route_completed_after_handoff(self):
        WorkflowCrossEntityRoutingEngine.route_to_hrms(
            self.instance,
            stage_id=self.close_node.id,
        )
        checkpoint = self.instance.handoff_checkpoints.filter(
            handoff_type='workflow_to_hrms'
        ).first()

        WorkflowCrossEntityRoutingEngine.complete_handoff(
            checkpoint.id,
            response_payload={'hrms_record_id': 'HRMS-00001'},
        )

        # The associated onboarding→HRMS route should be completed
        route = self.instance.entity_routes.filter(
            from_entity_type='onboarding',
            to_entity_type='hrms',
        ).first()
        assert route is not None
        assert route.status == 'completed'
