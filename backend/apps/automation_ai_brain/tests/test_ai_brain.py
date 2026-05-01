import uuid
from django.test import TestCase
from apps.automation_ai_brain.automation_ai_brain import AutomationAIBrainEngine
from apps.automation_ai_brain.models import (
    AutomationAIDecision,
    AutomationAIRecommendation
)

class AutomationAIBrainTest(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.entity_id = uuid.uuid4()
        self.engine = AutomationAIBrainEngine()

    def test_select_best_workflow(self):
        # Scenario 1: Multiple workflows available, should pick highest success rate
        workflows = [
            {'id': uuid.uuid4(), 'name': 'Workflow Low', 'historical_success_rate': 0.5},
            {'id': uuid.uuid4(), 'name': 'Workflow High', 'historical_success_rate': 0.95},
        ]
        decision = self.engine.generate_decision(
            tenant_id=self.tenant_id,
            entity_type='candidate_state',
            entity_id=self.entity_id,
            available_workflows=workflows
        )
        
        self.assertEqual(decision.decision_type, 'execute_workflow')
        self.assertEqual(
            decision.decision_output.get('selected_workflow_id'), 
            str(workflows[1]['id'])
        )

    def test_sla_risk_escalation(self):
        # By default in our mock engine, 'critical' priority creates high SLA risk
        # We need to simulate the context to have critical priority.
        # We override analyze_context to simulate this for testing purposes
        original_analyze = self.engine.analyze_context
        
        def mock_analyze(tenant_id, entity_type, entity_id):
            return {
                'priority': 'critical',
                'workload_status': 'normal',
                'historical_success': 0.88
            }
        self.engine.analyze_context = mock_analyze
        
        decision = self.engine.generate_decision(
            tenant_id=self.tenant_id,
            entity_type='candidate_state',
            entity_id=self.entity_id
        )
        
        self.assertEqual(decision.decision_type, 'escalate')
        self.assertIn('High SLA risk', decision.decision_reason)
        
        # Restore original method
        self.engine.analyze_context = original_analyze

    def test_recommendation_generation(self):
        # Scenario 3: Manual repeated action -> recommendation generated
        recs = self.engine.generate_recommendations(self.tenant_id)
        
        self.assertTrue(len(recs) > 0)
        self.assertEqual(recs[0].recommendation_type, 'create_workflow')
        self.assertEqual(recs[0].tenant_id, self.tenant_id)
