from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.core.responses import error_response, success_response
from apps.automation_os.models import (
    AutomationRuntimeState,
    AutomationEngineRegistry,
    AutomationExecutionPolicy,
    AutomationWorkloadBucket,
    AutomationBusinessCoverage,
    AutomationOperatingEvent,
    AutomationOperatingInsight,
    OrchestrationMode,
    EngineStatus
)
from apps.automation_os.serializers import (
    AutomationRuntimeStateSerializer,
    AutomationEngineRegistrySerializer,
    AutomationExecutionPolicySerializer,
    AutomationWorkloadBucketSerializer,
    AutomationBusinessCoverageSerializer,
    AutomationOperatingEventSerializer,
    AutomationOperatingInsightSerializer
)
from apps.automation_os.services.automation_operating_system import AutomationOperatingSystem


class RuntimeStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        state = AutomationOperatingSystem.initialize_runtime(request.user.tenant_id)
        # Ensure latest health evaluation
        state = AutomationOperatingSystem.evaluate_runtime_health(request.user.tenant_id)
        return success_response(data=AutomationRuntimeStateSerializer(state).data)

    @action(detail=False, methods=['post'])
    def recalculate(self, request):
        state = AutomationOperatingSystem.evaluate_runtime_health(request.user.tenant_id)
        return success_response(data=AutomationRuntimeStateSerializer(state).data, message="Runtime state recalculated.")

class RuntimeModeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, mode_type):
        # mode_type: safe-mode, maintenance-mode, emergency-override, normal
        mode_map = {
            'safe-mode': OrchestrationMode.SAFE_MODE,
            'maintenance-mode': OrchestrationMode.MAINTENANCE_MODE,
            'emergency-override': OrchestrationMode.EMERGENCY_OVERRIDE,
            'normal': OrchestrationMode.NORMAL
        }
        
        mode = mode_map.get(mode_type)
        if not mode:
            return error_response("Invalid mode type.")
            
        state = AutomationOperatingSystem.switch_orchestration_mode(
            request.user.tenant_id, 
            mode, 
            performed_by=request.user.id
        )
        return success_response(data=AutomationRuntimeStateSerializer(state).data)

class GlobalControlView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, action_type):
        tenant_id = request.user.tenant_id
        if action_type == 'pause-all':
            AutomationEngineRegistry.objects.filter(tenant_id=tenant_id).update(status=EngineStatus.PAUSED)
            AutomationOperatingSystem.log_operating_event(tenant_id, 'global_pause', "Global pause triggered by admin.", source='OS', performed_by=request.user.id)
        elif action_type == 'resume-all':
            AutomationEngineRegistry.objects.filter(tenant_id=tenant_id).update(status=EngineStatus.ACTIVE)
            AutomationOperatingSystem.log_operating_event(tenant_id, 'global_resume', "Global resume triggered by admin.", source='OS', performed_by=request.user.id)
        
        AutomationOperatingSystem.evaluate_runtime_health(tenant_id)
        return success_response(message=f"Global {action_type} executed.")

class EngineRegistryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AutomationEngineRegistrySerializer

    def get_queryset(self):
        return AutomationEngineRegistry.objects.filter(tenant_id=self.request.user.tenant_id)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        engine = self.get_object()
        engine.status = EngineStatus.PAUSED
        engine.save()
        AutomationOperatingSystem.evaluate_runtime_health(request.user.tenant_id)
        return success_response(message=f"Engine {engine.engine_name} paused.")

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        engine = self.get_object()
        engine.status = EngineStatus.ACTIVE
        engine.save()
        AutomationOperatingSystem.evaluate_runtime_health(request.user.tenant_id)
        return success_response(message=f"Engine {engine.engine_name} resumed.")

    @action(detail=True, methods=['post'])
    def maintenance(self, request, pk=None):
        engine = self.get_object()
        engine.status = EngineStatus.MAINTENANCE
        engine.save()
        AutomationOperatingSystem.evaluate_runtime_health(request.user.tenant_id)
        return success_response(message=f"Engine {engine.engine_name} set to maintenance.")

class ExecutionPolicyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AutomationExecutionPolicySerializer

    def get_queryset(self):
        return AutomationExecutionPolicy.objects.filter(tenant_id=self.request.user.tenant_id)

class WorkloadBucketViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AutomationWorkloadBucketSerializer

    def get_queryset(self):
        return AutomationWorkloadBucket.objects.filter(tenant_id=self.request.user.tenant_id)

class BusinessCoverageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        AutomationOperatingSystem.recalculate_business_coverage(request.user.tenant_id)
        coverage = AutomationBusinessCoverage.objects.filter(tenant_id=request.user.tenant_id)
        return success_response(data=AutomationBusinessCoverageSerializer(coverage, many=True).data)

class OperatingEventListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = AutomationOperatingEvent.objects.filter(tenant_id=request.user.tenant_id)[:50]
        return success_response(data=AutomationOperatingEventSerializer(events, many=True).data)

class OperatingInsightListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        AutomationOperatingSystem.generate_operating_insights(request.user.tenant_id)
        insights = AutomationOperatingInsight.objects.filter(tenant_id=request.user.tenant_id)
        return success_response(data=AutomationOperatingInsightSerializer(insights, many=True).data)
