import uuid
from django.test import TestCase
from apps.automation_system_completion.automation_system_completion_engine import AutomationSystemCompletionEngine
from apps.automation_system_completion.models import (
    AutomationSystemReadiness,
    AutomationGapItem,
    AutomationProductionGate,
    AutomationCompletionCheck
)

class AutomationSystemCompletionTest(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.engine = AutomationSystemCompletionEngine()

    def test_missing_observability_integration(self):
        # Scenario: Ensure failed check creates a gap and reduces score
        # In the mock engine, the DLQ check fails by default
        readiness = self.engine.run_completion_assessment(self.tenant_id)
        
        gaps = AutomationGapItem.objects.filter(tenant_id=self.tenant_id, title__contains='Dead Letter Queue Bound')
        self.assertTrue(gaps.exists())
        self.assertEqual(gaps.first().impact_level, 'high')
        
        # A high failure should reduce score from 80 down to 60 (which is 'partial')
        self.assertEqual(readiness.readiness_status, 'partial')

    def test_production_gate_blocked(self):
        # Scenario: If reliability check fails, the recovery gate should be blocked/failed
        self.engine.run_completion_assessment(self.tenant_id)
        
        gate = AutomationProductionGate.objects.filter(tenant_id=self.tenant_id, gate_type='reliability_gate').first()
        self.assertEqual(gate.current_status, 'failed')

    def test_end_to_end_flow_passes(self):
        # Scenario: Check E2E flows exist and pass
        self.engine.run_completion_assessment(self.tenant_id)
        
        check = AutomationCompletionCheck.objects.filter(tenant_id=self.tenant_id, check_name='Candidate Flow E2E').first()
        self.assertEqual(check.check_status, 'passed')

    def test_all_checks_pass(self):
        # Scenario: Modify failed check to pass, expect 'ready_with_warnings' or 'production_ready' depending on warnings
        self.engine.run_completion_assessment(self.tenant_id)
        
        # Manually fix the failed check
        failed_check = AutomationCompletionCheck.objects.filter(tenant_id=self.tenant_id, check_status='failed').first()
        failed_check.check_status = 'passed'
        failed_check.severity = 'medium'
        failed_check.save()
        
        # Re-run assessment to calculate score again
        readiness = self.engine.calculate_readiness_score(self.tenant_id)
        self.engine.evaluate_production_gates(self.tenant_id)
        
        # Score should be 80, which is 'ready_with_warnings' (since no critical/high failures remain)
        self.assertEqual(readiness.readiness_status, 'ready_with_warnings')
        
        # The reliability gate should now pass
        gate = AutomationProductionGate.objects.filter(tenant_id=self.tenant_id, gate_type='reliability_gate').first()
        self.assertEqual(gate.current_status, 'passed')
