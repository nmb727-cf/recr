from rest_framework import serializers
from .models import (
    AutomationAIDecision,
    AutomationAIContext,
    AutomationAIReasoning,
    AutomationAIRecommendation
)

class AutomationAIDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationAIDecision
        fields = '__all__'

class AutomationAIContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationAIContext
        fields = '__all__'

class AutomationAIReasoningSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationAIReasoning
        fields = '__all__'

class AutomationAIRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationAIRecommendation
        fields = '__all__'
