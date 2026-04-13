from rest_framework import serializers
from ..models import AgencyWorkflowDefinition, AgencyWorkflowNode, AgencyWorkflowEdge

class AgencyWorkflowNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyWorkflowNode
        fields = '__all__'

class AgencyWorkflowEdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyWorkflowEdge
        fields = '__all__'

class AgencyWorkflowDefinitionSerializer(serializers.ModelSerializer):
    nodes = AgencyWorkflowNodeSerializer(many=True, read_only=True)
    edges = AgencyWorkflowEdgeSerializer(many=True, read_only=True)

    class Meta:
        model = AgencyWorkflowDefinition
        fields = '__all__'
