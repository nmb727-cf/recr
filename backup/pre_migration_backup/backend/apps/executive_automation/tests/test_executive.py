"""
Tests for Executive Control Tower (PHASE27).

Run with:
    pytest apps/executive_automation/tests/test_executive.py -v
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

import apps.executive_automation.services.automation_executive_engine as exec_engine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TENANT_ID = str(uuid.uuid4())
ENGINE_MOD = 'apps.executive_automation.services.automation_executive_engine'


def _mock_collect(
    total_wf=10, active_wf=8, total_exec=200, success_exec=180,
    failed_exec=20, dead_letter=2, no_sla=3, no_perm=2,
    no_gate=1, module_no_wf=None, ai_sugg=None, anomalies=0,
    critical_events=0, observations=None, sla_policies=5,
    cross_module_workflows=2, playbook_count=1,
):
    """Return a dict that mimics what _collect() produces."""
    return {
        'total_workflows': total_wf,
        'active_workflows': active_wf,
        'total_executions_today': total_exec,
        'successful_executions_today': success_exec,
        'failed_executions_today': total_exec - success_exec,
        'failed_exec_count': failed_exec,
        'dead_letter_count': dead_letter,
        'no_sla_workflows': no_sla,
        'no_permission_policies': no_perm,
        'no_approval_gates': no_gate,
        'modules_without_workflows': module_no_wf if module_no_wf is not None else ['candidate_screening'],
        'ai_suggestions': ai_sugg if ai_sugg is not None else [],
        'anomaly_count': anomalies,
        'critical_event_count': critical_events,
        'observation_count': 0 if observations is None else observations,
        'sla_policy_count': sla_policies,
        'executions_30d': 3000,
        'successful_30d': 2700,
        'department_data': {},
        'maturity_level': 'structured',
        'cross_module_workflows': cross_module_workflows,
        'playbook_count': playbook_count,
    }


# ---------------------------------------------------------------------------
# 1. Executive Summary generation
# ---------------------------------------------------------------------------

class TestExecutiveSummaryGeneration:

    def test_coverage_percent_full(self):
        d = _mock_collect(total_wf=10, active_wf=10)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            result = exec_engine.generate_executive_summary(TENANT_ID)
        assert result['automation_coverage_percent'] == 100.0

    def test_coverage_percent_partial(self):
        d = _mock_collect(total_wf=10, active_wf=4)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            result = exec_engine.generate_executive_summary(TENANT_ID)
        assert result['automation_coverage_percent'] == 40.0

    def test_coverage_zero_when_no_workflows(self):
        d = _mock_collect(total_wf=0, active_wf=0)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            result = exec_engine.generate_executive_summary(TENANT_ID)
        assert result['automation_coverage_percent'] == 0.0

    def test_time_saved_hours_calculation(self):
        # 180 successes × 3 min / 60 = 9 hours
        d = _mock_collect(total_exec=200, success_exec=180)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            result = exec_engine.generate_executive_summary(TENANT_ID)
        assert result['time_saved_hours'] == pytest.approx(9.0, rel=1e-3)

    def test_business_impact_score_range(self):
        d = _mock_collect()
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            result = exec_engine.generate_executive_summary(TENANT_ID)
        score = result['business_impact_score']
        assert 0.0 <= score <= 100.0


# ---------------------------------------------------------------------------
# 2. ROI calculation
# ---------------------------------------------------------------------------

class TestROICalculation:

    def test_roi_monthly_basic(self):
        d = _mock_collect(total_exec=200, success_exec=180)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            roi = exec_engine.calculate_roi(TENANT_ID, 'monthly')
        assert roi['hours_saved'] > 0
        assert roi['operational_cost_reduction'] > 0
        assert roi['success_rate'] == pytest.approx(90.0, rel=1e-2)

    def test_roi_cost_equals_hours_times_rate(self):
        d = _mock_collect(total_exec=200, success_exec=180)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            roi = exec_engine.calculate_roi(TENANT_ID, 'monthly')
        expected_cost = roi['hours_saved'] * exec_engine.HOURLY_LABOUR_COST_USD
        assert roi['operational_cost_reduction'] == pytest.approx(expected_cost, rel=1e-3)

    def test_roi_zero_executions(self):
        d = _mock_collect(total_exec=0, success_exec=0)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            roi = exec_engine.calculate_roi(TENANT_ID, 'monthly')
        assert roi['hours_saved'] == 0
        assert roi['success_rate'] == 0


# ---------------------------------------------------------------------------
# 3. Risk detection
# ---------------------------------------------------------------------------

class TestRiskDetection:

    def test_failure_spike_detected(self):
        # 50% failure rate should trigger failure_spike risk
        d = _mock_collect(total_exec=100, success_exec=50, failed_exec=50)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            risks = exec_engine.detect_operational_risks(TENANT_ID)
        types = [r['risk_type'] for r in risks]
        assert 'failure_spike' in types

    def test_dead_letter_risk(self):
        d = _mock_collect(dead_letter=15)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            risks = exec_engine.detect_operational_risks(TENANT_ID)
        types = [r['risk_type'] for r in risks]
        assert any(t in types for t in ['dependency_risk', 'failure_spike', 'governance_gap'])

    def test_governance_gap_no_permissions(self):
        d = _mock_collect(no_perm=10, no_gate=5)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            risks = exec_engine.detect_operational_risks(TENANT_ID)
        types = [r['risk_type'] for r in risks]
        assert 'governance_gap' in types

    def test_manual_gap_detected(self):
        d = _mock_collect(module_no_wf=['candidate_screening', 'offer_management', 'onboarding'])
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            risks = exec_engine.detect_operational_risks(TENANT_ID)
        types = [r['risk_type'] for r in risks]
        assert 'manual_gap' in types

    def test_no_risk_clean_state(self):
        d = _mock_collect(
            total_exec=100, success_exec=99, failed_exec=1,
            dead_letter=0, no_perm=0, no_gate=0,
            module_no_wf=[], anomalies=0, critical_events=0,
            no_sla=0,
        )
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            risks = exec_engine.detect_operational_risks(TENANT_ID)
        assert len(risks) <= 1


# ---------------------------------------------------------------------------
# 4. Opportunities
# ---------------------------------------------------------------------------

class TestOpportunityGeneration:

    def test_manual_process_opportunity(self):
        d = _mock_collect(module_no_wf=['candidate_screening', 'offer_management'])
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            opps = exec_engine.generate_opportunities(TENANT_ID)
        types = [o['opportunity_type'] for o in opps]
        assert 'automate_manual_process' in types

    def test_ai_opportunity_from_suggestions(self):
        ai_sugg = [MagicMock(id=uuid.uuid4(), workflow__name='Job Screening')]
        d = _mock_collect(ai_sugg=ai_sugg)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            opps = exec_engine.generate_opportunities(TENANT_ID)
        types = [o['opportunity_type'] for o in opps]
        assert 'enable_ai' in types

    def test_no_opportunities_near_perfect_state(self):
        d = _mock_collect(
            module_no_wf=[], ai_sugg=[],
            total_exec=100, success_exec=99,
            cross_module_workflows=5, playbook_count=3, no_sla=0,
        )
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            opps = exec_engine.generate_opportunities(TENANT_ID)
        assert len(opps) <= 2


# ---------------------------------------------------------------------------
# 5. Department scores
# ---------------------------------------------------------------------------

class TestDepartmentScores:

    def test_returns_list_of_dicts(self):
        d = _mock_collect()
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            depts = exec_engine.compute_department_scores(TENANT_ID)
        assert isinstance(depts, list)
        for dept in depts:
            assert 'department_name' in dept
            assert 'automation_coverage' in dept
            assert 0 <= dept['automation_coverage'] <= 100

    def test_department_coverage_range(self):
        d = _mock_collect()
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            depts = exec_engine.compute_department_scores(TENANT_ID)
        for dept in depts:
            assert dept['manual_gap_percent'] >= 0


# ---------------------------------------------------------------------------
# 6. Executive insights
# ---------------------------------------------------------------------------

class TestExecutiveInsights:

    def test_insights_is_list_of_strings(self):
        d = _mock_collect()
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            insights = exec_engine.generate_executive_insights(TENANT_ID)
        assert isinstance(insights, list)
        assert all(isinstance(i, str) for i in insights)
        assert len(insights) > 0

    def test_high_failure_insight_present(self):
        d = _mock_collect(total_exec=100, success_exec=50, failed_exec=50)
        with patch(f'{ENGINE_MOD}._collect', return_value=d):
            insights = exec_engine.generate_executive_insights(TENANT_ID)
        combined = ' '.join(insights).lower()
        assert 'failure' in combined or 'reliability' in combined or 'error' in combined


# ---------------------------------------------------------------------------
# 7. Model serialization (unit – no DB)
# ---------------------------------------------------------------------------

class TestSerializers:

    def _make_summary(self):
        from apps.executive_automation.models import ExecutiveAutomationSummary
        import datetime
        obj = ExecutiveAutomationSummary.__new__(ExecutiveAutomationSummary)
        obj.id = uuid.uuid4()
        obj.snapshot_date = datetime.date.today()
        obj.total_workflows = 10
        obj.active_workflows = 8
        obj.total_executions_today = 200
        obj.successful_executions_today = 180
        obj.automation_coverage_percent = Decimal('80.00')
        obj.automation_maturity_level = 'structured'
        obj.time_saved_hours = Decimal('9.00')
        obj.tasks_automated = 180
        obj.sla_improvement_percent = Decimal('12.50')
        obj.open_risks = 3
        obj.open_opportunities = 5
        obj.business_impact_score = Decimal('72.50')
        obj.created_at = None
        return obj

    def test_summary_serializer_fields(self):
        from apps.executive_automation.serializers import ExecutiveAutomationSummarySerializer
        obj = self._make_summary()
        data = ExecutiveAutomationSummarySerializer(obj).data
        assert data['total_workflows'] == 10
        assert data['automation_maturity_level'] == 'structured'
        assert 'business_impact_score' in data

    def test_risk_status_update_serializer_valid(self):
        from apps.executive_automation.serializers import RiskStatusUpdateSerializer
        ser = RiskStatusUpdateSerializer(data={'status': 'acknowledged'})
        assert ser.is_valid()

    def test_risk_status_update_serializer_invalid(self):
        from apps.executive_automation.serializers import RiskStatusUpdateSerializer
        ser = RiskStatusUpdateSerializer(data={'status': 'banana'})
        assert not ser.is_valid()

    def test_opportunity_status_update_serializer(self):
        from apps.executive_automation.serializers import OpportunityStatusUpdateSerializer
        ser = OpportunityStatusUpdateSerializer(data={'status': 'in_progress', 'assigned_to': str(uuid.uuid4())})
        assert ser.is_valid()
