from rest_framework import serializers
from apps.automation_observability.models import (
    WorkflowExecutionTrace,
    WorkflowObservabilityEvent,
    WorkflowDependencyHealth,
    WorkflowAnomaly
)

class WorkflowExecutionTraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowExecutionTrace
        fields = '__all__'

class WorkflowObservabilityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowObservabilityEvent
        fields = '__all__'

class WorkflowDependencyHealthSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDependencyHealth
        fields = '__all__'

class WorkflowAnomalySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAnomaly
        fields = '__all__'
