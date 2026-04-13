from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Avg

from apps.core.responses import success_response, error_response
from apps.automation_observability.models import (
    WorkflowExecutionTrace,
    WorkflowObservabilityEvent,
    WorkflowDependencyHealth,
    WorkflowAnomaly,
    TraceStatus
)
from apps.automation_observability.serializers import (
    WorkflowExecutionTraceSerializer,
    WorkflowObservabilityEventSerializer,
    WorkflowDependencyHealthSerializer,
    WorkflowAnomalySerializer
)
from apps.automation_observability.services.workflow_observability_engine import WorkflowObservabilityEngine

class LiveWorkflowMonitorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        traces = WorkflowExecutionTrace.objects.filter(
            tenant_id=request.user.tenant_id,
            status__in=[TraceStatus.STARTED, TraceStatus.RUNNING]
        ).order_by('-created_at')
        serializer = WorkflowExecutionTraceSerializer(traces, many=True)
        return success_response(data=serializer.data)

class FailureMonitorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        failures = WorkflowExecutionTrace.objects.filter(
            tenant_id=request.user.tenant_id,
            status=TraceStatus.FAILED
        ).order_by('-created_at')
        serializer = WorkflowExecutionTraceSerializer(failures, many=True)
        return success_response(data=serializer.data)

class LatencyMonitorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Return average latency per workflow
        stats = WorkflowExecutionTrace.objects.filter(
            tenant_id=request.user.tenant_id
        ).values('workflow_id').annotate(avg_latency=Avg('execution_time_ms')).order_by('-avg_latency')
        return success_response(data=list(stats))

class DependencyHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Trigger mock check
        WorkflowObservabilityEngine.monitor_dependencies(request.user.tenant_id)
        
        health = WorkflowDependencyHealth.objects.filter(tenant_id=request.user.tenant_id)
        serializer = WorkflowDependencyHealthSerializer(health, many=True)
        return success_response(data=serializer.data)

class AnomalyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Trigger detection
        WorkflowObservabilityEngine.detect_anomalies(request.user.tenant_id)
        
        anomalies = WorkflowAnomaly.objects.filter(tenant_id=request.user.tenant_id).order_by('-detected_at')
        serializer = WorkflowAnomalySerializer(anomalies, many=True)
        return success_response(data=serializer.data)

class AlertListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = WorkflowObservabilityEvent.objects.filter(
            tenant_id=request.user.tenant_id,
            severity__in=['error', 'critical']
        ).order_by('-created_at')
        serializer = WorkflowObservabilityEventSerializer(events, many=True)
        return success_response(data=serializer.data)
