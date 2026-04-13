from rest_framework import serializers
from ..models import (
    AgencyWorkflowEventDefinition,
    AgencyWorkflowEventSubscription,
    AgencyWorkflowEventLog,
    AgencyWorkflowEventDebugTrace
)

class AgencyWorkflowEventDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyWorkflowEventDefinition
        fields = '__all__'

class AgencyWorkflowEventSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyWorkflowEventSubscription
        fields = '__all__'

class AgencyWorkflowEventLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyWorkflowEventLog
        fields = '__all__'

class AgencyWorkflowEventDebugTraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyWorkflowEventDebugTrace
        fields = '__all__'
