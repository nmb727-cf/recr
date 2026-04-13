"""
Tests for the Automation Learning Engine.

Covers:
- LearningEvaluator rule logic and threshold boundaries
- AutomationLearningService.run_for_tenant: suggestion creation, idempotency,
  tenant isolation
- Edge cases: insufficient sample, all rules suppressed, zero-data policies
"""
import uuid

from django.test import TestCase
from django.utils import timezone

from apps.orchestration_center.models import AISuggestion, AutomationIntelligencePolicy
from apps.orchestration_center.services.automation_learning_service import (
    AutomationLearningService,
    LearningEvaluator,
    PolicyMetrics,
)


ISO_WEEK = '2026-W14'  # fixed for deterministic idempotency keys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _policy_metrics(**kwargs) -> PolicyMetrics:
    defaults = dict(
        policy_id=str(uuid.uuid4()),
        suggestion_type='followup_recommendation',
        module_scope='',
        auto_approve=False,
        auto_apply=False,
        total=10,
        approved=0,
        rejected=0,
        applied=0,
        apply_failed=0,
    )
    defaults.update(kwargs)
    return PolicyMetrics(**defaults)


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


def _make_suggestion(tenant_id, *, category, status, source_module='', last_apply_status='',
                     idempotency_key=None):
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
        last_apply_status=last_apply_status,
        idempotency_key=idempotency_key or f'test-{uuid.uuid4()}',
    )


# ---------------------------------------------------------------------------
# LearningEvaluator unit tests
# ---------------------------------------------------------------------------

class LearningEvaluatorTests(TestCase):

    def test_no_rules_fire_on_insufficient_sample(self):
        metrics = _policy_metrics(total=2, approved=2, rejected=0)
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        self.assertEqual(recs, [])

    def test_enable_auto_approve_fires_above_threshold(self):
        metrics = _policy_metrics(
            auto_approve=False,
            total=10, approved=10, rejected=1,  # 90.9%
        )
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        keys = [r.rule_key for r in recs]
        self.assertIn('enable_auto_approve', keys)
        rec = next(r for r in recs if r.rule_key == 'enable_auto_approve')
        self.assertEqual(rec.category, 'automation_recommendation')
        self.assertGreater(rec.confidence_score, 0.9)

    def test_enable_auto_approve_does_not_fire_at_boundary(self):
        # exactly 90% — rule requires > 90%, so should NOT fire
        metrics = _policy_metrics(
            auto_approve=False,
            total=10, approved=9, rejected=1,  # 90.0%
        )
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        self.assertNotIn('enable_auto_approve', [r.rule_key for r in recs])

    def test_enable_auto_approve_suppressed_when_already_enabled(self):
        metrics = _policy_metrics(
            auto_approve=True,  # already on
            total=10, approved=10, rejected=0,
        )
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        self.assertNotIn('enable_auto_approve', [r.rule_key for r in recs])

    def test_enable_auto_apply_fires_above_threshold(self):
        metrics = _policy_metrics(
            auto_apply=False,
            applied=20, apply_failed=0,  # 100%
            total=20,
        )
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        self.assertIn('enable_auto_apply', [r.rule_key for r in recs])
        rec = next(r for r in recs if r.rule_key == 'enable_auto_apply')
        self.assertEqual(rec.category, 'automation_recommendation')

    def test_enable_auto_apply_does_not_fire_below_threshold(self):
        metrics = _policy_metrics(
            auto_apply=False,
            applied=19, apply_failed=1,  # 95.0% — not > 95%
            total=20,
        )
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        self.assertNotIn('enable_auto_apply', [r.rule_key for r in recs])

    def test_enable_auto_apply_requires_min_sample(self):
        metrics = _policy_metrics(
            auto_apply=False,
            applied=2, apply_failed=0,  # only 2 applied, below MIN_SAMPLE_APPLIED=3
            total=2,
        )
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        self.assertNotIn('enable_auto_apply', [r.rule_key for r in recs])

    def test_disable_auto_approve_fires_on_low_approval_rate(self):
        metrics = _policy_metrics(
            auto_approve=True,
            total=10, approved=2, rejected=8,  # 20%
        )
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        self.assertIn('disable_auto_approve', [r.rule_key for r in recs])
        rec = next(r for r in recs if r.rule_key == 'disable_auto_approve')
        self.assertEqual(rec.category, 'policy_improvement')

    def test_disable_auto_approve_not_fire_above_threshold(self):
        metrics = _policy_metrics(
            auto_approve=True,
            total=10, approved=4, rejected=6,  # 40%
        )
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        self.assertNotIn('disable_auto_approve', [r.rule_key for r in recs])

    def test_high_rejection_rate_fires(self):
        metrics = _policy_metrics(
            auto_approve=False,
            total=10, approved=2, rejected=8,  # 80% rejection
        )
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        self.assertIn('high_rejection_rate', [r.rule_key for r in recs])
        rec = next(r for r in recs if r.rule_key == 'high_rejection_rate')
        self.assertEqual(rec.category, 'policy_improvement')

    def test_idempotency_keys_are_unique_per_rule(self):
        metrics = _policy_metrics(
            auto_approve=False,
            total=20, approved=19, rejected=1,  # triggers enable_auto_approve
            applied=18, apply_failed=0,          # triggers enable_auto_apply
        )
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        idem_keys = [r.idempotency_key for r in recs]
        self.assertEqual(len(idem_keys), len(set(idem_keys)), 'Idempotency keys must be unique')

    def test_multiple_rules_can_fire_simultaneously(self):
        # High approval rate → enable_auto_approve; high rejection on no auto → both can't
        # fire simultaneously (approve ↑ and reject ↑ are mutually exclusive), so let's
        # test two non-exclusive rules: enable_auto_approve + enable_auto_apply.
        metrics = _policy_metrics(
            auto_approve=False,
            auto_apply=False,
            total=20, approved=19, rejected=1,   # 95% approve → fires rule 1
            applied=10, apply_failed=0,           # 100% apply → fires rule 2
        )
        recs = LearningEvaluator.evaluate(metrics, ISO_WEEK)
        rule_keys = [r.rule_key for r in recs]
        self.assertIn('enable_auto_approve', rule_keys)
        self.assertIn('enable_auto_apply', rule_keys)


# ---------------------------------------------------------------------------
# AutomationLearningService integration tests
# ---------------------------------------------------------------------------

class AutomationLearningServiceTests(TestCase):

    def setUp(self):
        self.tenant_id = uuid.UUID('00000000-0000-0000-0000-000000000401')
        self.other_tenant_id = uuid.UUID('00000000-0000-0000-0000-000000000402')

    def test_no_suggestions_created_for_empty_policy(self):
        _make_policy(self.tenant_id)
        result = AutomationLearningService.run_for_tenant(self.tenant_id)
        self.assertEqual(result['suggestions_created'], 0)

    def test_high_approval_rate_creates_auto_approve_suggestion(self):
        policy = _make_policy(self.tenant_id, suggestion_type='followup_recommendation', auto_approve=False)
        # Create 10 approved, 0 rejected (100% approval)
        for _ in range(10):
            _make_suggestion(self.tenant_id, category='followup_recommendation', status='approved')
        _make_suggestion(self.tenant_id, category='followup_recommendation', status='rejected')

        result = AutomationLearningService.run_for_tenant(self.tenant_id)
        self.assertGreaterEqual(result['suggestions_created'], 1)

        learning_suggestion = AISuggestion.objects.filter(
            tenant_id=self.tenant_id,
            category='automation_recommendation',
            source_module='automation_learning_engine',
        ).first()
        self.assertIsNotNone(learning_suggestion)
        self.assertIn('auto-approve', learning_suggestion.title.lower())
        self.assertEqual(learning_suggestion.source_entity_id, str(policy.id))

    def test_high_apply_success_rate_creates_auto_apply_suggestion(self):
        _make_policy(self.tenant_id, suggestion_type='followup_recommendation', auto_apply=False)
        # 10 applied, 0 failed (100%)
        for _ in range(10):
            _make_suggestion(self.tenant_id, category='followup_recommendation',
                             status='applied', last_apply_status='success')

        result = AutomationLearningService.run_for_tenant(self.tenant_id)
        self.assertGreaterEqual(result['suggestions_created'], 1)

        learning_suggestion = AISuggestion.objects.filter(
            tenant_id=self.tenant_id,
            category='automation_recommendation',
            suggestion_key='enable_auto_apply',
        ).first()
        self.assertIsNotNone(learning_suggestion)
        self.assertIn('auto-apply', learning_suggestion.title.lower())

    def test_low_approval_rate_on_auto_approved_policy_creates_policy_improvement(self):
        _make_policy(self.tenant_id, suggestion_type='followup_recommendation', auto_approve=True)
        # 2 approved, 8 rejected (20%)
        for _ in range(2):
            _make_suggestion(self.tenant_id, category='followup_recommendation', status='approved')
        for _ in range(8):
            _make_suggestion(self.tenant_id, category='followup_recommendation', status='rejected')

        result = AutomationLearningService.run_for_tenant(self.tenant_id)
        self.assertGreaterEqual(result['suggestions_created'], 1)

        rec = AISuggestion.objects.filter(
            tenant_id=self.tenant_id,
            category='policy_improvement',
            suggestion_key='disable_auto_approve',
        ).first()
        self.assertIsNotNone(rec)

    def test_idempotency_prevents_duplicate_suggestions(self):
        _make_policy(self.tenant_id, suggestion_type='followup_recommendation', auto_approve=False)
        for _ in range(10):
            _make_suggestion(self.tenant_id, category='followup_recommendation', status='approved')
        _make_suggestion(self.tenant_id, category='followup_recommendation', status='rejected')

        result1 = AutomationLearningService.run_for_tenant(self.tenant_id)
        result2 = AutomationLearningService.run_for_tenant(self.tenant_id)

        self.assertGreaterEqual(result1['suggestions_created'], 1)
        self.assertEqual(result2['suggestions_created'], 0)
        self.assertGreaterEqual(result2['suggestions_skipped_idempotent'], 1)

    def test_tenant_isolation(self):
        """Tenant A's data must not generate suggestions for Tenant B."""
        # Tenant A: high approval policy
        _make_policy(self.tenant_id, suggestion_type='followup_recommendation', auto_approve=False)
        for _ in range(10):
            _make_suggestion(self.tenant_id, category='followup_recommendation', status='approved')
        _make_suggestion(self.tenant_id, category='followup_recommendation', status='rejected')

        # Tenant B: policy exists but no suggestion data
        _make_policy(self.other_tenant_id, suggestion_type='followup_recommendation', auto_approve=False)

        result_b = AutomationLearningService.run_for_tenant(self.other_tenant_id)
        self.assertEqual(result_b['suggestions_created'], 0)

        # No learning suggestions should exist for Tenant B
        b_suggestions = AISuggestion.objects.filter(
            tenant_id=self.other_tenant_id,
            source_module='automation_learning_engine',
        )
        self.assertEqual(b_suggestions.count(), 0)

    def test_disabled_policy_is_skipped(self):
        _make_policy(self.tenant_id, suggestion_type='followup_recommendation',
                     auto_approve=False, is_enabled=False)
        for _ in range(10):
            _make_suggestion(self.tenant_id, category='followup_recommendation', status='approved')

        result = AutomationLearningService.run_for_tenant(self.tenant_id)
        self.assertEqual(result['suggestions_created'], 0)

    def test_module_scope_filter_applied(self):
        """Policy scoped to 'communications' should only consider suggestions from that module."""
        _make_policy(self.tenant_id, suggestion_type='followup_recommendation',
                     module_scope='communications', auto_approve=False)
        # 10 approved suggestions from a different module — should NOT count
        for _ in range(10):
            _make_suggestion(self.tenant_id, category='followup_recommendation',
                             status='approved', source_module='pipeline')
        _make_suggestion(self.tenant_id, category='followup_recommendation',
                         status='rejected', source_module='pipeline')

        result = AutomationLearningService.run_for_tenant(self.tenant_id)
        # No suggestions visible for this scoped policy → no learning suggestion
        self.assertEqual(result['suggestions_created'], 0)

    def test_run_for_all_tenants_processes_multiple_tenants(self):
        _make_policy(self.tenant_id, suggestion_type='followup_recommendation', auto_approve=False)
        for _ in range(10):
            _make_suggestion(self.tenant_id, category='followup_recommendation', status='approved')
        _make_suggestion(self.tenant_id, category='followup_recommendation', status='rejected')

        _make_policy(self.other_tenant_id, suggestion_type='escalation_recommendation', auto_approve=False)
        for _ in range(10):
            _make_suggestion(self.other_tenant_id, category='escalation_recommendation', status='approved')
        _make_suggestion(self.other_tenant_id, category='escalation_recommendation', status='rejected')

        result = AutomationLearningService.run_for_all_tenants()
        self.assertEqual(result['tenants_processed'], 2)
        self.assertGreaterEqual(result['total_suggestions_created'], 2)

    def test_learning_suggestions_have_correct_fields(self):
        policy = _make_policy(self.tenant_id, suggestion_type='followup_recommendation', auto_approve=False)
        for _ in range(10):
            _make_suggestion(self.tenant_id, category='followup_recommendation', status='approved')
        _make_suggestion(self.tenant_id, category='followup_recommendation', status='rejected')

        AutomationLearningService.run_for_tenant(self.tenant_id)

        s = AISuggestion.objects.filter(
            tenant_id=self.tenant_id,
            source_module='automation_learning_engine',
        ).first()
        self.assertIsNotNone(s)
        self.assertEqual(s.status, 'pending')
        self.assertEqual(s.source_entity_type, 'automation_intelligence_policy')
        self.assertEqual(s.source_entity_id, str(policy.id))
        self.assertFalse(s.requires_approval)
        self.assertTrue(s.manual_override_allowed)
        self.assertNotEqual(s.idempotency_key, '')
        self.assertIn(s.category, ['automation_recommendation', 'policy_improvement'])
        self.assertGreater(float(s.confidence_score), 0)
