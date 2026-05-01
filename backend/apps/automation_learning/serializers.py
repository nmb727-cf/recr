from rest_framework import serializers
from .models import (
    AutomationLearningEvent,
    AutomationLearningPattern,
    AutomationOptimizationSuggestion,
    AutomationLearningModel
)

class AutomationLearningEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationLearningEvent
        fields = '__all__'

class AutomationLearningPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationLearningPattern
        fields = '__all__'

class AutomationOptimizationSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationOptimizationSuggestion
        fields = '__all__'

class AutomationLearningModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationLearningModel
        fields = '__all__'
