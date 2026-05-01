from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.core.responses import success_response, error_response
from apps.automation_command_center.permissions import CanView, CanAdmin
from .models import (
    AutomationLearningEvent,
    AutomationLearningPattern,
    AutomationOptimizationSuggestion,
    AutomationLearningModel
)
from .serializers import (
    AutomationLearningEventSerializer,
    AutomationLearningPatternSerializer,
    AutomationOptimizationSuggestionSerializer,
    AutomationLearningModelSerializer
)
from .automation_self_learning_engine import AutomationSelfLearningEngine

class AutomationLearningOverviewView(APIView):
    permission_classes = [IsAuthenticated, CanView]
...
class AutomationLearningPatternsView(APIView):
    permission_classes = [IsAuthenticated, CanView]
...
class AutomationLearningSuggestionsView(APIView):
    permission_classes = [IsAuthenticated, CanView]
...
class AutomationLearningPredictionsView(APIView):
    permission_classes = [IsAuthenticated, CanView]
...
class AutomationLearningModelsView(APIView):
    permission_classes = [IsAuthenticated, CanView]
...
class AutomationLearningRetrainView(APIView):
    permission_classes = [IsAuthenticated, CanAdmin]
...
class AutomationCenterLearningSummaryView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tenant_id = request.user.tenant_id
        engine = AutomationSelfLearningEngine()
        
        # Trigger pattern detection and suggestion generation on the fly for summary if needed
        engine.detect_patterns(tenant_id)
        engine.generate_optimization_suggestions(tenant_id)
        
        suggestions = AutomationOptimizationSuggestion.objects.filter(tenant_id=tenant_id, status='pending')[:5]
        patterns = AutomationLearningPattern.objects.filter(tenant_id=tenant_id).order_by('-confidence_score')[:5]
        
        return success_response(data={
            'learning_summary': {
                'suggestions': AutomationOptimizationSuggestionSerializer(suggestions, many=True).data,
                'patterns': AutomationLearningPatternSerializer(patterns, many=True).data,
                'predictions': {
                    'system_reliability': 0.98,
                    'potential_failures_next_24h': 2
                }
            }
        }, message="Automation Center learning summary retrieved.")
