from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from ..models import (
    AgencyWorkflowEventDefinition,
    AgencyWorkflowEventSubscription,
    AgencyWorkflowEventLog,
    AgencyWorkflowEventDebugTrace
)
from .event_serializers import (
    AgencyWorkflowEventDefinitionSerializer,
    AgencyWorkflowEventSubscriptionSerializer,
    AgencyWorkflowEventLogSerializer,
    AgencyWorkflowEventDebugTraceSerializer
)
from ..services.agency_workflow_event_engine import AgencyWorkflowEventEngine

class AgencyWorkflowEventRegistryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgencyWorkflowEventDefinition.objects.all()
    serializer_class = AgencyWorkflowEventDefinitionSerializer

class AgencyWorkflowEventSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = AgencyWorkflowEventSubscription.objects.all()
    serializer_class = AgencyWorkflowEventSubscriptionSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

class AgencyWorkflowEventLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgencyWorkflowEventLog.objects.all()
    serializer_class = AgencyWorkflowEventLogSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=['get'])
    def debug(self, request, pk=None):
        log = self.get_object()
        traces = log.traces.all()
        serializer = AgencyWorkflowEventDebugTraceSerializer(traces, many=True)
        return Response(serializer.data)

class AgencyWorkflowEventTestViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='test-emit')
    def test_emit(self, request):
        tenant_id = request.data.get('tenant_id')
        event_key = request.data.get('event_key')
        entity_type = request.data.get('entity_type', 'test')
        entity_id = request.data.get('entity_id')
        payload = request.data.get('payload', {})
        source_module = request.data.get('source_module', 'test_mode')
        
        event_log = AgencyWorkflowEventEngine.emit_agency_event(
            tenant_id=tenant_id,
            event_key=event_key,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            source_module=source_module
        )
        
        return Response({
            "status": "emitted",
            "log_id": event_log.id,
            "event_status": event_log.status
        })
