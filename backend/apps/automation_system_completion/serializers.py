from rest_framework import serializers
from .models import (
    AutomationSystemReadiness,
    AutomationCompletionCheck,
    AutomationGapItem,
    AutomationProductionGate,
    AutomationCompletionReport
)

class AutomationSystemReadinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationSystemReadiness
        fields = '__all__'

class AutomationCompletionCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationCompletionCheck
        fields = '__all__'

class AutomationGapItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationGapItem
        fields = '__all__'

class AutomationProductionGateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationProductionGate
        fields = '__all__'

class AutomationCompletionReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationCompletionReport
        fields = '__all__'
