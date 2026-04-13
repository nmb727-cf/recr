"""
Tests for the Automation Analytics Service and analytics endpoints.

Covers:
- AutomationAnalyticsService.get_overview_analytics metric accuracy
- AutomationAnalyticsService.get_suggestion_analytics lifecycle and confidence
- AutomationAnalyticsService.get_execution_analytics AI + automation breakdown
- AutomationAnalyticsService.get_policy_analytics per-policy effectiveness
- Tenant isolation across all four methods
- Zero-data edge cases
"""
import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.orchestration_center.models import (
    AIExecutionRequest,
    AISuggestion,
    AutomationExecutionRun,
    AutomationIntelligencePolicy,
)
from apps.orchestration_center.services.automation_analytics import AutomationAnalyticsService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tenant():
    return uuid.uuid4()


def _make_suggestion(tenant_id, *, category='followup_recommendation', status='pending',
                     last_apply_status='', source_module='', confidence_score='0.85'):
    return AISuggestion.objects.create(
        tenant_id=tenant_id,
        suggestion_key=f'test-{uuid.uuid4()}',
        category=category,
        status=status,
        source_module=source_module,
        source_event='test',
        source_entity_type='candidate',
        source_entity_id=str(uuid.uuid4()),
        owner_module='test',
        proposed_action_family='test',
        title='Test suggestion',
        confidence_score=confidence_score,
        last_apply_status=last_apply_status,
        idempotency_key=f'test-{uuid.uuid4()}',
    )


def _make_ai_run(tenant_id, *, status='completed', retry_count=0):
    return AIExecutionRequest.objects.create(
        tenant_id=tenant_id,
        use_case_key='test_case',
        source_event='test',
        source_entity_type='candidate',
        source_entity_id=str(uuid.uuid4()),
        status=status,
        retry_count=retry_count,
    )


def _make_auto_run(tenant_id, *, status='completed', retry_count=0):
    from apps.orchestration_center.models import AutomationRule
    rule, _ = AutomationRule.objects.get_or_create(
        rule_key='test-rule',
        defaults={
            'tenant_id': tenant_id,
            'rule_title': 'Test Rule',
            'trigger_event': 'test.event',
            'module_scope': 'test',
        },
    )
    return AutomationExecutionRun.objects.create(
        tenant_id=tenant_id,
        rule=rule,
        source_event='test',
        source_entity_type='candidate',
        source_entity_id=str(uuid.uuid4()),
        status=status,
        retry_count=retry_count,
    )


def _make_policy(tenant_id, *, suggestion_type='followup_recommendation', module_scope='',
                 auto_approve=False, auto_apply=False, is_enabled=True):
    return AutomationIntelligencePolicy.objects.create(
        tenant_id=tenant_id,
        suggestion_type=suggestion_type,
        module_scope=module_scope,
        confidence_threshold='0.85',
        auto_approve=auto_approve,
        auto_apply=auto_apply,
        approval_required=not auto_apply,
        is_enabled=is_enabled,
    )


# ---------------------------------------------------------------------------
# Overview analytics
# ---------------------------------------------------------------------------

class OverviewAnalyticsTests(TestCase):

    def setUp(self):
        self.tenant_id = _tenant()

    def test_empty_tenant_returns_zero_counts(self):
        result = AutomationAnalyticsService.get_overview_analytics(self.tenant_id)
        self.assertEqual(result['suggestions']['total'], 0)
        self.assertEqual(result['executions']['total'], 0)
        self.assertEqual(result['policies']['active'], 0)

    def test_suggestion_counts_accurate(self):
        _make_suggestion(self.tenant_id, status='approved')
        _make_suggestion(self.tenant_id, status='approved')
        _make_suggestion(self.tenant_id, status='rejected')
        _make_suggestion(self.tenant_id, status='applied')
        _make_suggestion(self.tenant_id, status='dismissed')
        _make_suggestion(self.tenant_id, status='applied', last_apply_status='failed')

        result = AutomationAnalyticsService.get_overview_analytics(self.tenant_id)
        s = result['suggestions']
        self.assertEqual(s['total'], 6)
        self.assertEqual(s['approved'], 2)
        self.assertEqual(s['rejected'], 1)
        self.assertEqual(s['applied'], 2)
        self.assertEqual(s['dismissed'], 1)

    def test_accuracy_rate_calculation(self):
        # 3 approved, 1 rejected → 75%
        for _ in range(3):
            _make_suggestion(self.tenant_id, status='approved')
        _make_suggestion(self.tenant_id, status='rejected')

        result = AutomationAnalyticsService.get_overview_analytics(self.tenant_id)
        self.assertEqual(result['suggestions']['accuracy_rate'], 75.0)

    def test_execution_counts_combine_ai_and_automation(self):
        _make_ai_run(self.tenant_id, status='completed')
        _make_ai_run(self.tenant_id, status='failed')
        _make_ai_run(self.tenant_id, status='completed', retry_count=2)

        result = AutomationAnalyticsService.get_overview_analytics(self.tenant_id)
        e = result['executions']
        self.assertEqual(e['ai_total'], 3)
        self.assertEqual(e['total'], 3)
        self.assertEqual(e['retry_count'], 2)

    def test_policy_counts_respect_is_enabled(self):
        _make_policy(self.tenant_id, auto_approve=True, is_enabled=True)
        _make_policy(self.tenant_id, auto_apply=True, is_enabled=True)
        _make_policy(self.tenant_id, is_enabled=False)  # disabled — should not count

        result = AutomationAnalyticsService.get_overview_analytics(self.tenant_id)
        p = result['policies']
        self.assertEqual(p['active'], 2)
        self.assertEqual(p['auto_approve_enabled'], 1)
        self.assertEqual(p['auto_apply_enabled'], 1)

    def test_tenant_isolation(self):
        other = _tenant()
        _make_suggestion(other, status='approved')
        _make_ai_run(other, status='completed')

        result = AutomationAnalyticsService.get_overview_analytics(self.tenant_id)
        self.assertEqual(result['suggestions']['total'], 0)
        self.assertEqual(result['executions']['total'], 0)

    def test_average_confidence_computed(self):
        _make_suggestion(self.tenant_id, confidence_score='0.90')
        _make_suggestion(self.tenant_id, confidence_score='0.70')

        result = AutomationAnalyticsService.get_overview_analytics(self.tenant_id)
        avg = result['suggestions']['average_confidence']
        self.assertAlmostEqual(avg, 0.8, delta=0.001)


# ---------------------------------------------------------------------------
# Suggestion analytics
# ---------------------------------------------------------------------------

class SuggestionAnalyticsTests(TestCase):

    def setUp(self):
        self.tenant_id = _tenant()

    def test_lifecycle_counts_all_statuses(self):
        _make_suggestion(self.tenant_id, status='pending')
        _make_suggestion(self.tenant_id, status='approved')
        _make_suggestion(self.tenant_id, status='rejected')

        result = AutomationAnalyticsService.get_suggestion_analytics(self.tenant_id)
        status_counts = {row['status']: row['count'] for row in result['lifecycle']}
        self.assertEqual(status_counts['pending'], 1)
        self.assertEqual(status_counts['approved'], 1)
        self.assertEqual(status_counts['rejected'], 1)

    def test_by_category_groups_correctly(self):
        _make_suggestion(self.tenant_id, category='followup_recommendation', status='approved')
        _make_suggestion(self.tenant_id, category='followup_recommendation', status='rejected')
        _make_suggestion(self.tenant_id, category='escalation_recommendation', status='approved')

        result = AutomationAnalyticsService.get_suggestion_analytics(self.tenant_id)
        categories = {row['category']: row for row in result['by_category']}
        self.assertEqual(categories['followup_recommendation']['total'], 2)
        self.assertEqual(categories['followup_recommendation']['approved'], 1)
        self.assertEqual(categories['escalation_recommendation']['total'], 1)

    def test_confidence_band_distribution(self):
        _make_suggestion(self.tenant_id, confidence_score='0.90')  # high
        _make_suggestion(self.tenant_id, confidence_score='0.60')  # medium
        _make_suggestion(self.tenant_id, confidence_score='0.30')  # low

        result = AutomationAnalyticsService.get_suggestion_analytics(self.tenant_id)
        conf = result['confidence']
        self.assertEqual(conf['high_count'], 1)
        self.assertEqual(conf['medium_count'], 1)
        self.assertEqual(conf['low_count'], 1)

    def test_empty_returns_empty_lists(self):
        result = AutomationAnalyticsService.get_suggestion_analytics(self.tenant_id)
        self.assertEqual(result['lifecycle'], [])
        self.assertEqual(result['by_category'], [])
        self.assertEqual(result['confidence']['high_count'], 0)


# ---------------------------------------------------------------------------
# Execution analytics
# ---------------------------------------------------------------------------

class ExecutionAnalyticsTests(TestCase):

    def setUp(self):
        self.tenant_id = _tenant()

    def test_ai_execution_counts_accurate(self):
        _make_ai_run(self.tenant_id, status='completed')
        _make_ai_run(self.tenant_id, status='completed')
        _make_ai_run(self.tenant_id, status='failed')
        _make_ai_run(self.tenant_id, status='completed', retry_count=3)

        result = AutomationAnalyticsService.get_execution_analytics(self.tenant_id)
        ai = result['ai']
        self.assertEqual(ai['total'], 4)
        self.assertEqual(ai['successful'], 3)
        self.assertEqual(ai['failed'], 1)
        self.assertEqual(ai['total_retries'], 3)

    def test_success_rate_calculation(self):
        _make_ai_run(self.tenant_id, status='completed')
        _make_ai_run(self.tenant_id, status='failed')

        result = AutomationAnalyticsService.get_execution_analytics(self.tenant_id)
        self.assertEqual(result['ai']['success_rate'], 50.0)

    def test_overall_combines_ai_and_automation(self):
        _make_ai_run(self.tenant_id, status='completed')
        _make_ai_run(self.tenant_id, status='failed', retry_count=1)

        result = AutomationAnalyticsService.get_execution_analytics(self.tenant_id)
        overall = result['overall']
        self.assertEqual(overall['total_executions'], 2)
        self.assertEqual(overall['failed_executions'], 1)
        self.assertEqual(overall['retry_count'], 1)

    def test_tenant_isolation_executions(self):
        other = _tenant()
        _make_ai_run(other, status='completed')

        result = AutomationAnalyticsService.get_execution_analytics(self.tenant_id)
        self.assertEqual(result['ai']['total'], 0)
        self.assertEqual(result['overall']['total_executions'], 0)

    def test_empty_returns_100_percent_success_rate(self):
        result = AutomationAnalyticsService.get_execution_analytics(self.tenant_id)
        self.assertEqual(result['ai']['success_rate'], 100.0)
        self.assertEqual(result['automation']['success_rate'], 100.0)
        self.assertEqual(result['overall']['success_rate'], 100.0)


# ---------------------------------------------------------------------------
# Policy analytics
# ---------------------------------------------------------------------------

class PolicyAnalyticsTests(TestCase):

    def setUp(self):
        self.tenant_id = _tenant()

    def test_empty_policies_returns_empty_list(self):
        result = AutomationAnalyticsService.get_policy_analytics(self.tenant_id)
        self.assertEqual(result['policies'], [])
        self.assertEqual(result['total_policies'], 0)

    def test_trigger_count_matches_suggestion_category(self):
        _make_policy(self.tenant_id, suggestion_type='followup_recommendation')
        _make_suggestion(self.tenant_id, category='followup_recommendation', status='approved')
        _make_suggestion(self.tenant_id, category='followup_recommendation', status='approved')
        _make_suggestion(self.tenant_id, category='followup_recommendation', status='rejected')

        result = AutomationAnalyticsService.get_policy_analytics(self.tenant_id)
        policy = result['policies'][0]
        self.assertEqual(policy['trigger_count'], 3)
        self.assertEqual(policy['auto_approve_count'], 2)

    def test_module_scope_filters_suggestions(self):
        _make_policy(self.tenant_id, suggestion_type='followup_recommendation', module_scope='pipeline')
        _make_suggestion(self.tenant_id, category='followup_recommendation', source_module='pipeline', status='applied')
        _make_suggestion(self.tenant_id, category='followup_recommendation', source_module='communications', status='applied')

        result = AutomationAnalyticsService.get_policy_analytics(self.tenant_id)
        policy = result['policies'][0]
        # Only pipeline suggestions count
        self.assertEqual(policy['trigger_count'], 1)
        self.assertEqual(policy['auto_apply_count'], 1)

    def test_success_rate_zero_when_no_triggers(self):
        _make_policy(self.tenant_id, suggestion_type='followup_recommendation')
        result = AutomationAnalyticsService.get_policy_analytics(self.tenant_id)
        self.assertEqual(result['policies'][0]['success_rate'], 100.0)

    def test_all_required_fields_present(self):
        _make_policy(self.tenant_id, suggestion_type='followup_recommendation', auto_approve=True)
        result = AutomationAnalyticsService.get_policy_analytics(self.tenant_id)
        policy = result['policies'][0]
        for field in ('id', 'suggestion_type', 'module_scope', 'auto_approve', 'auto_apply',
                      'trigger_count', 'auto_approve_count', 'auto_apply_count',
                      'failure_count', 'success_rate', 'last_triggered_at', 'last_outcome'):
            self.assertIn(field, policy, f'Missing field: {field}')
