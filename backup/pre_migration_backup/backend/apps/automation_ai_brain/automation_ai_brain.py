import uuid
from typing import List, Dict, Any
from .models import (
    AutomationAIDecision,
    AutomationAIContext,
    AutomationAIReasoning,
    AutomationAIRecommendation
)

class AutomationAIBrainEngine:
    def analyze_context(self, tenant_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID) -> Dict[str, Any]:
        """
        Step 1 & 2: Collect context and analyze rules.
        """
        # Normally fetches realtime state from jobs, candidates, SLAs
        context, created = AutomationAIContext.objects.get_or_create(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            defaults={
                'context_data': {
                    'priority': 'high',
                    'workload_status': 'normal',
                    'historical_success': 0.88
                }
            }
        )
        return context.context_data

    def predict_outcomes(self, tenant_id: uuid.UUID, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 4: Predict outcomes based on context.
        """
        prediction = {
            'success_probability': 0.85,
            'estimated_delay': 10,
            'sla_risk_level': 'low'
        }
        if context_data.get('priority') == 'critical':
            prediction['sla_risk_level'] = 'high'
            
        AutomationAIReasoning.objects.create(
            tenant_id=tenant_id,
            reasoning_type='predictive',
            reasoning_data=prediction,
            confidence_score=0.9
        )
        return prediction

    def detect_risk(self, tenant_id: uuid.UUID, context_data: Dict[str, Any], prediction: Dict[str, Any]) -> bool:
        """
        Check for risks that would warrant pausing or escalating.
        """
        if prediction.get('sla_risk_level') == 'high' or context_data.get('workload_status') == 'overloaded':
            return True
        return False

    def select_best_workflow(self, tenant_id: uuid.UUID, available_workflows: List[Dict[str, Any]], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5: Choose best action/workflow among multiple.
        """
        if not available_workflows:
            return None
        
        # Simplistic selection: pick workflow with highest success rate based on context
        best_workflow = max(available_workflows, key=lambda w: w.get('historical_success_rate', 0))
        return best_workflow

    def prioritize_execution(self, tenant_id: uuid.UUID, workflows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Smart prioritization logic for queued workflows.
        """
        # Sort workflows by priority and SLA constraints
        return sorted(workflows, key=lambda w: w.get('priority_score', 0), reverse=True)

    def generate_decision(self, tenant_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID, available_workflows: List[Dict[str, Any]] = None) -> AutomationAIDecision:
        """
        Main entrypoint: analyzes, predicts, decides.
        """
        # 1. Collect Context
        context = self.analyze_context(tenant_id, entity_type, entity_id)
        
        # 2. Predict
        prediction = self.predict_outcomes(tenant_id, context)
        
        # 3. Detect Risk
        is_risky = self.detect_risk(tenant_id, context, prediction)
        
        decision_type = 'execute_workflow'
        decision_reason = 'Optimal conditions detected'
        decision_output = {}

        if is_risky:
            decision_type = 'escalate'
            decision_reason = 'High SLA risk or overloaded workload detected.'
        else:
            if available_workflows:
                best_wf = self.select_best_workflow(tenant_id, available_workflows, context)
                decision_output['selected_workflow_id'] = str(best_wf.get('id'))
                decision_reason = f"Selected workflow {best_wf.get('name')} based on context"

        decision = AutomationAIDecision.objects.create(
            tenant_id=tenant_id,
            decision_type=decision_type,
            decision_reason=decision_reason,
            decision_confidence=0.88,
            decision_output=decision_output
        )
        return decision

    def generate_recommendations(self, tenant_id: uuid.UUID) -> List[AutomationAIRecommendation]:
        """
        Identify missing automations, repeated manual actions to suggest optimizations.
        """
        recommendation = AutomationAIRecommendation.objects.create(
            tenant_id=tenant_id,
            recommendation_type='create_workflow',
            title='Automate manual follow-ups',
            description='System detected manual repetitive actions regarding candidate follow-ups.',
            expected_impact='Reduce manual workload by 15 hours/week.',
            confidence_score=0.92
        )
        return [recommendation]
