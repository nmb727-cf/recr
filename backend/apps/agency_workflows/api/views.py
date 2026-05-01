from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from ..models import AgencyWorkflowDefinition, AgencyWorkflowNode, AgencyWorkflowEdge
from .serializers import (
    AgencyWorkflowDefinitionSerializer, 
    AgencyWorkflowNodeSerializer, 
    AgencyWorkflowEdgeSerializer
)

class AgencyWorkflowViewSet(viewsets.ModelViewSet):
    queryset = AgencyWorkflowDefinition.objects.all()
    serializer_class = AgencyWorkflowDefinitionSerializer

    def create(self, request, *args, **kwargs):
        # Basic create implementation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def save_canvas(self, request, pk=None):
        """Saves current state of nodes and edges from visual builder."""
        workflow = self.get_object()
        nodes_data = request.data.get('nodes', [])
        edges_data = request.data.get('edges', [])
        
        # Simple implementation: Re-sync nodes and edges
        workflow.nodes.all().delete()
        workflow.edges.all().delete()
        
        node_map = {}
        for n_data in nodes_data:
            node = AgencyWorkflowNode.objects.create(
                workflow=workflow,
                node_type=n_data.get('type'),
                config=n_data.get('config', {}),
                position_x=n_data.get('position', {}).get('x', 0),
                position_y=n_data.get('position', {}).get('y', 0)
            )
            node_map[n_data.get('id')] = node
            
        for e_data in edges_data:
            AgencyWorkflowEdge.objects.create(
                workflow=workflow,
                source_node=node_map.get(e_data.get('source')),
                target_node=node_map.get(e_data.get('target')),
                condition=e_data.get('condition', {})
            )
            
        return Response({"status": "saved"})
