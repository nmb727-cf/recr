import uuid
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.core.responses import success_response, error_response
from apps.automation_command_center.permissions import CanManage

from .models import (
    AutomationAIDecision,
    AutomationAIContext,
    AutomationAIReasoning,
    AutomationAIRecommendation
)
from .serializers import (
    AutomationAIDecisionSerializer,
    AutomationAIContextSerializer,
    AutomationAIReasoningSerializer,
    AutomationAIRecommendationSerializer
)
from .automation_ai_brain import AutomationAIBrainEngine

class AutomationAIDecisionsView(APIView):
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        tenant_id = request.user.tenant_id
        decisions = AutomationAIDecision.objects.filter(tenant_id=tenant_id).order_by('-created_at')[:50]
        return success_response(data={
            'decisions': AutomationAIDecisionSerializer(decisions, many=True).data
        }, message="AI decisions retrieved.")

class AutomationAIRecommendationsView(APIView):
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        tenant_id = request.user.tenant_id
        recommendations = AutomationAIRecommendation.objects.filter(tenant_id=tenant_id).order_by('-confidence_score')
        return success_response(data={
            'recommendations': AutomationAIRecommendationSerializer(recommendations, many=True).data
        }, message="AI recommendations retrieved.")

class AutomationAIPredictionsView(APIView):
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        tenant_id = request.user.tenant_id
        predictions = AutomationAIReasoning.objects.filter(
            tenant_id=tenant_id, 
            reasoning_type='predictive'
        ).order_by('-created_at')[:50]
        return success_response(data={
            'predictions': AutomationAIReasoningSerializer(predictions, many=True).data
        }, message="AI predictions retrieved.")

class AutomationAIContextView(APIView):
    permission_classes = [IsAuthenticated, CanManage]

    def get(self, request):
        tenant_id = request.user.tenant_id
        contexts = AutomationAIContext.objects.filter(tenant_id=tenant_id).order_by('-created_at')[:50]
        return success_response(data={
            'context': AutomationAIContextSerializer(contexts, many=True).data
        }, message="AI context retrieved.")

class AutomationAIRecalculateView(APIView):
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request):
        tenant_id = request.user.tenant_id
        entity_type = request.data.get('entity_type', 'candidate_state')
        entity_id = request.data.get('entity_id', str(uuid.uuid4()))
        
        # Simulate recalculation using the brain engine
        engine = AutomationAIBrainEngine()
        
        # In a real scenario, available_workflows would be queried from the database based on the trigger
        mock_workflows = [
            {'id': uuid.uuid4(), 'name': 'Workflow A', 'historical_success_rate': 0.7},
            {'id': uuid.uuid4(), 'name': 'Workflow B', 'historical_success_rate': 0.95}
        ]
        
        decision = engine.generate_decision(tenant_id, entity_type, entity_id, available_workflows=mock_workflows)
        recommendations = engine.generate_recommendations(tenant_id)
        
        return success_response(data={
            'decision': AutomationAIDecisionSerializer(decision).data,
            'recommendations_generated': len(recommendations)
        }, message="AI Brain recalculated and generated new decisions.")
