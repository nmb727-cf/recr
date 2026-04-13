"""
Automation Recovery Engine — Test Cases
"""
import uuid

import pytest
from django.utils import timezone

from apps.automation_recovery.models import (
    AttemptStatus,
    DeadLetterStatus,
    FailureType,
    RecoveryStatus,
    RecoveryStrategy,
    WorkflowDeadLetterItem,
    WorkflowFallbackRule,
    WorkflowRecoveryAttempt,
    WorkflowRecoveryCase,
)
from apps.automation_recovery.services.workflow_recovery_engine import WorkflowRecoveryEngine


TENANT_ID = uuid.uuid4()


def make_case(**kwargs):
    defaults = dict(
        tenant_id=TENANT_ID,
        workflow_id=uuid.uuid4(),
        execution_id=uuid.uuid4(),
        failure_node_id=uuid.uuid4(),
        error_message='network timeout',
        execution_snapshot={},
        max_retry_limit=3,
    )
    defaults.update(kwargs)
    return WorkflowRecoveryCase.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Test 1 — Transient notification failure: recovery case created and classified
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestCreateRecoveryCase:
    def test_creates_case_with_open_status(self):
        wf_id = uuid.uuid4()
        exec_id = uuid.uuid4()
        case = WorkflowRecoveryEngine.create_recovery_case(
            tenant_id=TENANT_ID,
            workflow_id=wf_id,
            execution_id=exec_id,
            error_message='network timeout',
        )
        assert case.id is not None
        assert case.recovery_status == RecoveryStatus.OPEN
        assert case.tenant_id == TENANT_ID
        assert case.workflow_id == wf_id

    def test_classify_transient_failure(self):
        failure_type = WorkflowRecoveryEngine.classify_failure('network timeout')
        assert failure_type == FailureType.TRANSIENT

    def test_classify_provider_error(self):
        failure_type = WorkflowRecoveryEngine.classify_failure('whatsapp provider error')
        assert failure_type == FailureType.PROVIDER_ERROR

    def test_classify_permission_error(self):
        failure_type = WorkflowRecoveryEngine.classify_failure('403 forbidden access denied')
        assert failure_type == FailureType.PERMISSION_ERROR

    def test_classify_unrecoverable(self):
        failure_type = WorkflowRecoveryEngine.classify_failure('unknown catastrophic error xyz')
        assert failure_type == FailureType.UNRECOVERABLE

    def test_choose_strategy_transient_immediate_retry(self):
        case = make_case(failure_type=FailureType.TRANSIENT, retry_count=0)
        strategy = WorkflowRecoveryEngine.choose_recovery_strategy(case)
        assert strategy == RecoveryStrategy.IMMEDIATE_RETRY

    def test_choose_strategy_delayed_for_dependency_unavailable(self):
        case = make_case(failure_type=FailureType.DEPENDENCY_UNAVAILABLE, retry_count=0)
        strategy = WorkflowRecoveryEngine.choose_recovery_strategy(case)
        assert strategy == RecoveryStrategy.DELAYED_RETRY


# ---------------------------------------------------------------------------
# Test 2 — Repeated failure exceeds retry limit → dead letter queue
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestRetryExhaustion:
    def test_retry_exhaustion_moves_to_dead_letter(self):
        case = make_case(
            failure_type=FailureType.TRANSIENT,
            retry_count=3,  # already at max
            max_retry_limit=3,
        )
        result = WorkflowRecoveryEngine.retry_execution(
            case_id=case.id, tenant_id=TENANT_ID
        )
        # Should return a dead letter item, not an attempt
        assert isinstance(result, WorkflowDeadLetterItem)
        case.refresh_from_db()
        assert case.recovery_status == RecoveryStatus.DEAD_LETTERED

    def test_strategy_is_dead_letter_when_retries_exhausted(self):
        case = make_case(failure_type=FailureType.TRANSIENT, retry_count=3, max_retry_limit=3)
        strategy = WorkflowRecoveryEngine.choose_recovery_strategy(case)
        assert strategy == RecoveryStrategy.DEAD_LETTER

    def test_unrecoverable_type_goes_to_dead_letter(self):
        case = make_case(failure_type=FailureType.UNRECOVERABLE, retry_count=0)
        strategy = WorkflowRecoveryEngine.choose_recovery_strategy(case)
        assert strategy == RecoveryStrategy.DEAD_LETTER

    def test_dead_letter_item_created_with_correct_data(self):
        wf_id = uuid.uuid4()
        exec_id = uuid.uuid4()
        node_id = uuid.uuid4()
        case = make_case(
            workflow_id=wf_id,
            execution_id=exec_id,
            failure_node_id=node_id,
            failure_type=FailureType.UNRECOVERABLE,
            error_message='fatal error',
            retry_count=3,
            max_retry_limit=3,
        )
        item = WorkflowRecoveryEngine.move_to_dead_letter(case.id, TENANT_ID)
        assert item.workflow_id == wf_id
        assert item.execution_id == exec_id
        assert item.failed_node_id == node_id
        assert item.status == DeadLetterStatus.PENDING
        assert item.failure_reason == 'fatal error'


# ---------------------------------------------------------------------------
# Test 3 — Fallback rule exists for failed node → fallback executed
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestFallbackExecution:
    def test_fallback_executed_when_rule_exists(self):
        node_id = uuid.uuid4()
        wf_id = uuid.uuid4()

        WorkflowFallbackRule.objects.create(
            tenant_id=TENANT_ID,
            workflow_id=wf_id,
            node_id=node_id,
            failure_type=FailureType.PROVIDER_ERROR,
            fallback_action_type='send_email',
            fallback_config={'to': 'manager@company.com'},
            is_active=True,
        )

        case = make_case(
            workflow_id=wf_id,
            failure_node_id=node_id,
            failure_type=FailureType.PROVIDER_ERROR,
            retry_count=1,
        )
        attempt = WorkflowRecoveryEngine.execute_fallback(case.id, TENANT_ID)
        assert attempt.status == AttemptStatus.SUCCEEDED
        assert attempt.strategy_used == RecoveryStrategy.FALLBACK_PATH
        assert attempt.recovery_output['fallback_action'] == 'send_email'

        case.refresh_from_db()
        assert case.recovery_status == RecoveryStatus.RESOLVED

    def test_fallback_returns_error_when_no_rule(self):
        case = make_case(failure_type=FailureType.PROVIDER_ERROR)
        result = WorkflowRecoveryEngine.execute_fallback(case.id, TENANT_ID)
        assert result.get('error') is not None

    def test_choose_strategy_favors_fallback_after_first_retry(self):
        node_id = uuid.uuid4()
        wf_id = uuid.uuid4()

        WorkflowFallbackRule.objects.create(
            tenant_id=TENANT_ID,
            workflow_id=wf_id,
            node_id=node_id,
            failure_type=FailureType.TRANSIENT,
            fallback_action_type='create_task',
            fallback_config={},
            is_active=True,
        )

        case = make_case(
            workflow_id=wf_id,
            failure_node_id=node_id,
            failure_type=FailureType.TRANSIENT,
            retry_count=1,  # already retried once
        )
        strategy = WorkflowRecoveryEngine.choose_recovery_strategy(case)
        assert strategy == RecoveryStrategy.FALLBACK_PATH


# ---------------------------------------------------------------------------
# Test 4 — Resume from failed node without replaying completed nodes
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestResumeFromNode:
    def test_resume_from_failed_node(self):
        node_id = uuid.uuid4()
        completed_node = str(uuid.uuid4())

        case = make_case(
            failure_node_id=node_id,
            execution_snapshot={'completed_nodes': [completed_node]},
        )
        attempt = WorkflowRecoveryEngine.resume_execution_from_node(case.id, TENANT_ID)

        assert attempt.status == AttemptStatus.SUCCEEDED
        assert attempt.strategy_used == RecoveryStrategy.RESUME_FROM_NODE
        assert str(node_id) in attempt.recovery_output['resumed_from_node']
        assert completed_node in attempt.recovery_output['skipped_nodes']

        case.refresh_from_db()
        assert case.recovery_status == RecoveryStatus.RESOLVED

    def test_resume_requires_failure_node(self):
        case = make_case(failure_node_id=None)
        result = WorkflowRecoveryEngine.resume_execution_from_node(case.id, TENANT_ID)
        assert result.get('error') is not None


# ---------------------------------------------------------------------------
# Test 5 — Critical unrecoverable failure → manual intervention + insight
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestManualInterventionAndInsights:
    def test_permission_error_strategy_is_manual(self):
        case = make_case(failure_type=FailureType.PERMISSION_ERROR, retry_count=0)
        strategy = WorkflowRecoveryEngine.choose_recovery_strategy(case)
        assert strategy == RecoveryStrategy.MANUAL

    def test_resolve_recovery_case(self):
        case = make_case()
        WorkflowRecoveryEngine.resolve_recovery_case(case.id, TENANT_ID)
        case.refresh_from_db()
        assert case.recovery_status == RecoveryStatus.RESOLVED
        assert case.resolved_at is not None

    def test_generate_recovery_insights_dead_letter_spike(self):
        wf_id = uuid.uuid4()
        # Create 5 dead-letter items in the last 24 hours to trigger spike insight
        for _ in range(5):
            WorkflowDeadLetterItem.objects.create(
                tenant_id=TENANT_ID,
                workflow_id=wf_id,
                execution_id=uuid.uuid4(),
                failure_reason='provider error',
                status=DeadLetterStatus.PENDING,
            )

        insights_created = WorkflowRecoveryEngine.generate_recovery_insights(TENANT_ID)
        assert insights_created >= 1

        from apps.automation_recovery.models import InsightType, WorkflowRecoveryInsight
        insight = WorkflowRecoveryInsight.objects.filter(
            tenant_id=TENANT_ID,
            workflow_id=wf_id,
            insight_type=InsightType.DEAD_LETTER_SPIKE,
        ).first()
        assert insight is not None
        assert insight.occurrence_count == 5

    def test_rollback_returns_error_without_plan(self):
        case = make_case(execution_snapshot={})
        result = WorkflowRecoveryEngine.attempt_rollback(case.id, TENANT_ID)
        assert result.get('error') is not None

    def test_rollback_succeeds_with_plan(self):
        case = make_case(
            execution_snapshot={'rollback_actions': ['undo_email', 'undo_task_creation']}
        )
        attempt = WorkflowRecoveryEngine.attempt_rollback(case.id, TENANT_ID)
        assert attempt.status == AttemptStatus.SUCCEEDED
        assert 'undo_email' in attempt.recovery_output['rolled_back_actions']


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestRecoveryAnalytics:
    def test_analytics_returns_expected_keys(self):
        analytics = WorkflowRecoveryEngine.get_recovery_analytics(TENANT_ID)
        expected_keys = [
            'total_cases', 'resolved', 'dead_lettered', 'rolled_back',
            'manual_intervention', 'recovery_success_rate', 'retry_success_rate',
            'fallback_success_rate', 'rollback_count', 'dead_letter_count',
            'dead_letter_pending', 'mttr_minutes',
        ]
        for key in expected_keys:
            assert key in analytics

    def test_analytics_zero_state(self):
        # With no data for a fresh tenant_id
        fresh_tid = uuid.uuid4()
        analytics = WorkflowRecoveryEngine.get_recovery_analytics(fresh_tid)
        assert analytics['total_cases'] == 0
        assert analytics['recovery_success_rate'] == 0.0
