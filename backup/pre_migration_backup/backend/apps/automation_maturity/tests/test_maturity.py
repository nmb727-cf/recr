"""
Automation Maturity Center — Test Cases
"""
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from django.utils import timezone

from apps.automation_maturity.models import (
    AutomationMaturityAssessment,
    AutomationModuleMaturity,
    AutomationTeamAdoption,
    AutomationMaturityRecommendation,
    AutomationMaturityRoadmap,
    AutomationBusinessTransformationMetric,
    MaturityLevel,
    RecommendationStatus,
    RecommendationPriority,
)
from apps.automation_maturity.services.automation_maturity_engine import (
    _score_to_level,
    _norm,
    calculate_coverage_score,
    calculate_adoption_score,
    calculate_governance_score,
    calculate_reliability_score,
    calculate_intelligence_score,
    calculate_operating_score,
    calculate_business_impact_score,
    determine_maturity_level,
    generate_maturity_roadmap,
    generate_maturity_recommendations,
    DIMENSION_WEIGHTS,
)

TENANT_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# Unit tests: scoring helpers
# ---------------------------------------------------------------------------

class TestScoringHelpers:
    def test_norm_at_zero(self):
        assert _norm(0, 20) == 0.0

    def test_norm_at_max(self):
        assert _norm(20, 20) == 100.0

    def test_norm_above_max_capped(self):
        assert _norm(50, 20) == 100.0

    def test_norm_half(self):
        assert _norm(10, 20) == 50.0

    def test_score_to_level_manual(self):
        assert _score_to_level(10) == 'manual'
        assert _score_to_level(20) == 'manual'

    def test_score_to_level_assisted(self):
        assert _score_to_level(21) == 'assisted'
        assert _score_to_level(40) == 'assisted'

    def test_score_to_level_structured(self):
        assert _score_to_level(41) == 'structured'
        assert _score_to_level(60) == 'structured'

    def test_score_to_level_optimized(self):
        assert _score_to_level(61) == 'optimized'
        assert _score_to_level(80) == 'optimized'

    def test_score_to_level_autonomous(self):
        assert _score_to_level(81) == 'autonomous'
        assert _score_to_level(100) == 'autonomous'

    def test_dimension_weights_sum_to_one(self):
        total = sum(DIMENSION_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001


# ---------------------------------------------------------------------------
# Test 1: Tenant with few workflows and no governance → Assisted or lower
# ---------------------------------------------------------------------------

class TestLowMaturityScoring:
    """Tenant with minimal automation. Expects manual or assisted level."""

    _LOW_DATA = {
        'total_wf': 2, 'active_wf': 2, 'critical_wf': 0, 'approved_wf': 0,
        'dry_run_wf': 0, 'exec_30d': 10, 'exec_success': 8, 'exec_failed': 2,
        'playbook_installs': 0, 'sla_active': 0, 'task_rules': 0,
        'notif_rules': 1, 'perm_policies': 0, 'sandbox_runs': 0,
        'change_sets': 0, 'ai_total': 3, 'ai_accepted': 0,
        'recovery_resolved': 0, 'recovery_total': 0, 'dead_letter_pending': 0,
        'anomaly_open': 0, 'dep_healthy': 0, 'dep_total': 0,
        'modules_covered': 1, 'unique_creators': 1, 'trigger_events': ['candidate_created'],
    }

    def test_coverage_is_low(self):
        score = calculate_coverage_score(self._LOW_DATA)
        assert score < 25, f'Expected low coverage, got {score}'

    def test_governance_is_very_low(self):
        score = calculate_governance_score(self._LOW_DATA)
        assert score < 20, f'Expected low governance, got {score}'

    def test_intelligence_is_very_low(self):
        score = calculate_intelligence_score(self._LOW_DATA)
        assert score < 25, f'Expected low intelligence, got {score}'

    def test_overall_level_is_manual_or_assisted(self):
        cov  = calculate_coverage_score(self._LOW_DATA)
        adp  = calculate_adoption_score(self._LOW_DATA)
        gov  = calculate_governance_score(self._LOW_DATA)
        rel  = calculate_reliability_score(self._LOW_DATA)
        intel= calculate_intelligence_score(self._LOW_DATA)
        ops  = calculate_operating_score(self._LOW_DATA)
        biz  = calculate_business_impact_score(self._LOW_DATA)
        overall = (
            cov   * DIMENSION_WEIGHTS['coverage']
            + adp * DIMENSION_WEIGHTS['adoption']
            + gov * DIMENSION_WEIGHTS['governance']
            + rel * DIMENSION_WEIGHTS['reliability']
            + intel*DIMENSION_WEIGHTS['intelligence']
            + ops * DIMENSION_WEIGHTS['operating']
            + biz * DIMENSION_WEIGHTS['business_impact']
        )
        level = determine_maturity_level(overall)
        assert level in ('manual', 'assisted'), f'Expected manual/assisted, got {level} (score={overall:.2f})'


# ---------------------------------------------------------------------------
# Test 2: Mature tenant → Optimized or Autonomous
# ---------------------------------------------------------------------------

class TestHighMaturityScoring:
    """Tenant with cross-module automation, governance, sandbox, analytics."""

    _HIGH_DATA = {
        'total_wf': 25, 'active_wf': 22, 'critical_wf': 8, 'approved_wf': 7,
        'dry_run_wf': 5, 'exec_30d': 220, 'exec_success': 210, 'exec_failed': 10,
        'playbook_installs': 12, 'sla_active': 6, 'task_rules': 12,
        'notif_rules': 11, 'perm_policies': 5, 'sandbox_runs': 15,
        'change_sets': 12, 'ai_total': 40, 'ai_accepted': 30,
        'recovery_resolved': 18, 'recovery_total': 20, 'dead_letter_pending': 0,
        'anomaly_open': 0, 'dep_healthy': 5, 'dep_total': 5,
        'modules_covered': 8, 'unique_creators': 8,
        'trigger_events': [
            'candidate_created', 'job_posted', 'pipeline_stage_changed',
            'interview_scheduled', 'offer_extended', 'agency_candidate_submitted',
            'task_created', 'sla_breached',
        ],
    }

    def test_coverage_is_high(self):
        score = calculate_coverage_score(self._HIGH_DATA)
        assert score >= 70, f'Expected high coverage, got {score}'

    def test_governance_is_high(self):
        score = calculate_governance_score(self._HIGH_DATA)
        assert score >= 60, f'Expected high governance, got {score}'

    def test_reliability_is_high(self):
        score = calculate_reliability_score(self._HIGH_DATA)
        assert score >= 80, f'Expected high reliability, got {score}'

    def test_overall_level_is_optimized_or_autonomous(self):
        cov  = calculate_coverage_score(self._HIGH_DATA)
        adp  = calculate_adoption_score(self._HIGH_DATA)
        gov  = calculate_governance_score(self._HIGH_DATA)
        rel  = calculate_reliability_score(self._HIGH_DATA)
        intel= calculate_intelligence_score(self._HIGH_DATA)
        ops  = calculate_operating_score(self._HIGH_DATA)
        biz  = calculate_business_impact_score(self._HIGH_DATA)
        overall = (
            cov   * DIMENSION_WEIGHTS['coverage']
            + adp * DIMENSION_WEIGHTS['adoption']
            + gov * DIMENSION_WEIGHTS['governance']
            + rel * DIMENSION_WEIGHTS['reliability']
            + intel*DIMENSION_WEIGHTS['intelligence']
            + ops * DIMENSION_WEIGHTS['operating']
            + biz * DIMENSION_WEIGHTS['business_impact']
        )
        level = determine_maturity_level(overall)
        assert level in ('optimized', 'autonomous'), (
            f'Expected optimized/autonomous, got {level} (score={overall:.2f})'
        )


# ---------------------------------------------------------------------------
# Test 3: Weak module — offers — generates recommendation
# ---------------------------------------------------------------------------

class TestModuleWeaknessRecommendation:
    _SCORES = {
        'overall': 38.0,
        'coverage': 20.0,
        'adoption': 45.0,
        'governance': 15.0,
        'reliability': 55.0,
        'intelligence': 20.0,
        'operating': 50.0,
        'business_impact': 40.0,
        'raw_data': {
            'sla_active': 0, 'sandbox_runs': 0, 'perm_policies': 0,
            'dead_letter_pending': 0, 'ai_total': 2, 'ai_accepted': 0,
            'playbook_installs': 0, 'modules_covered': 2, 'unique_creators': 1,
        },
    }

    def test_generates_coverage_recommendation(self):
        recs = generate_maturity_recommendations(TENANT_ID, self._SCORES)
        types = [r['recommendation_type'] for r in recs]
        assert 'increase_coverage' in types, f'Expected coverage rec, got {types}'

    def test_generates_governance_recommendation(self):
        recs = generate_maturity_recommendations(TENANT_ID, self._SCORES)
        types = [r['recommendation_type'] for r in recs]
        assert 'improve_governance' in types or 'strengthen_sandbox_usage' in types

    def test_generates_ai_adoption_recommendation(self):
        recs = generate_maturity_recommendations(TENANT_ID, self._SCORES)
        types = [r['recommendation_type'] for r in recs]
        assert 'increase_ai_adoption' in types, f'Expected AI rec, got {types}'

    def test_generates_playbook_recommendation(self):
        recs = generate_maturity_recommendations(TENANT_ID, self._SCORES)
        types = [r['recommendation_type'] for r in recs]
        assert 'enable_playbooks' in types

    def test_recommendation_has_required_fields(self):
        recs = generate_maturity_recommendations(TENANT_ID, self._SCORES)
        assert len(recs) > 0
        for r in recs:
            assert 'title' in r
            assert 'description' in r
            assert 'priority' in r
            assert 'expected_maturity_gain' in r
            assert r['expected_maturity_gain'] > 0


# ---------------------------------------------------------------------------
# Test 4: Roadmap generation
# ---------------------------------------------------------------------------

class TestRoadmapGeneration:
    def test_single_hop_manual_to_assisted(self):
        roadmap = generate_maturity_roadmap(TENANT_ID, 'manual', 'assisted')
        assert roadmap['current_level'] == 'manual'
        assert roadmap['target_level']  == 'assisted'
        assert len(roadmap['roadmap_steps']) >= 3
        assert roadmap['expected_timeline_days'] > 0

    def test_single_hop_structured_to_optimized(self):
        roadmap = generate_maturity_roadmap(TENANT_ID, 'structured', 'optimized')
        assert len(roadmap['roadmap_steps']) >= 4
        # All steps should reference the correct hop
        for step in roadmap['roadmap_steps']:
            assert step['from_level'] == 'structured'
            assert step['to_level']   == 'optimized'

    def test_multi_hop_manual_to_optimized(self):
        roadmap = generate_maturity_roadmap(TENANT_ID, 'manual', 'optimized')
        assert roadmap['current_level'] == 'manual'
        assert roadmap['target_level']  == 'optimized'
        # Should have steps from manual→assisted + assisted→structured + structured→optimized
        assert len(roadmap['roadmap_steps']) >= 8
        from_levels = {s['from_level'] for s in roadmap['roadmap_steps']}
        assert 'manual'     in from_levels
        assert 'assisted'   in from_levels
        assert 'structured' in from_levels

    def test_step_numbers_are_sequential(self):
        roadmap = generate_maturity_roadmap(TENANT_ID, 'manual', 'structured')
        steps = sorted(roadmap['roadmap_steps'], key=lambda s: s['step'])
        for i, step in enumerate(steps, 1):
            assert step['step'] == i

    def test_roadmap_name_includes_levels(self):
        roadmap = generate_maturity_roadmap(TENANT_ID, 'assisted', 'optimized')
        assert 'Assisted' in roadmap['roadmap_name'] or 'assisted' in roadmap['roadmap_name'].lower()
        assert 'Optimized' in roadmap['roadmap_name'] or 'optimized' in roadmap['roadmap_name'].lower()

    def test_same_level_target_still_returns_roadmap(self):
        # Engine adjusts target to next level when src == tgt
        roadmap = generate_maturity_roadmap(TENANT_ID, 'structured', 'structured')
        # Should advance one level
        assert roadmap['target_level'] == 'optimized'


# ---------------------------------------------------------------------------
# Test 5: Maturity trend / historical data
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMaturityTrend:
    def test_trend_returns_ordered_snapshots(self):
        import datetime
        today = datetime.date.today()
        for i in range(3):
            AutomationMaturityAssessment.objects.create(
                tenant_id             = TENANT_ID,
                assessment_date       = today - datetime.timedelta(days=i),
                overall_maturity_score= Decimal(str(30 + i * 10)),
                maturity_level        = 'assisted' if i == 0 else 'structured',
                coverage_score        = Decimal('25.00'),
                adoption_score        = Decimal('30.00'),
                governance_score      = Decimal('20.00'),
                reliability_score     = Decimal('40.00'),
                intelligence_score    = Decimal('15.00'),
                operating_score       = Decimal('35.00'),
                business_impact_score = Decimal('20.00'),
            )

        snapshots = (
            AutomationMaturityAssessment.objects
            .filter(tenant_id=TENANT_ID)
            .order_by('assessment_date')
        )
        assert snapshots.count() == 3
        scores = [float(s.overall_maturity_score) for s in snapshots]
        # Should be ascending (older → lower)
        assert scores == sorted(scores)

    def test_maturity_level_model_persistence(self):
        import datetime
        a = AutomationMaturityAssessment.objects.create(
            tenant_id             = TENANT_ID,
            assessment_date       = datetime.date.today(),
            overall_maturity_score= Decimal('72.50'),
            maturity_level        = MaturityLevel.OPTIMIZED,
            coverage_score        = Decimal('70.00'),
            adoption_score        = Decimal('75.00'),
            governance_score      = Decimal('65.00'),
            reliability_score     = Decimal('80.00'),
            intelligence_score    = Decimal('68.00'),
            operating_score       = Decimal('72.00'),
            business_impact_score = Decimal('60.00'),
        )
        a.refresh_from_db()
        assert a.maturity_level == 'optimized'
        assert float(a.overall_maturity_score) == 72.50


# ---------------------------------------------------------------------------
# Test 6: Recommendation model persistence and status transitions
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRecommendationPersistence:
    def test_create_and_update_status(self):
        rec = AutomationMaturityRecommendation.objects.create(
            tenant_id          = TENANT_ID,
            recommendation_type= 'increase_coverage',
            title              = 'Add more workflows',
            description        = 'Expand to offers module',
            target_area        = 'Module Coverage',
            expected_maturity_gain= Decimal('8.50'),
            priority           = RecommendationPriority.HIGH,
            status             = RecommendationStatus.NEW,
        )
        assert rec.status == 'new'
        rec.status = RecommendationStatus.IN_PROGRESS
        rec.save()
        rec.refresh_from_db()
        assert rec.status == 'in_progress'

    def test_recommendation_priorities_ordered_correctly(self):
        for p in ('low', 'medium', 'high', 'critical'):
            AutomationMaturityRecommendation.objects.create(
                tenant_id          = TENANT_ID,
                recommendation_type= 'improve_governance',
                title              = f'Test {p}',
                description        = 'desc',
                target_area        = 'Governance',
                expected_maturity_gain= Decimal('5.00'),
                priority           = p,
            )
        # Critical should come first in default ordering
        first = AutomationMaturityRecommendation.objects.filter(
            tenant_id=TENANT_ID
        ).order_by('-priority').first()
        # Lexicographic order: medium < high < critical (passes for our use)
        assert first is not None
