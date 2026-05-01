from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.core.responses import error_response, success_response
from apps.automation_sandbox.models import (
    WorkflowSandboxRun,
    WorkflowSandboxStepLog,
    WorkflowSandboxScenario,
    WorkflowSandboxArtifact,
    WorkflowSandboxApproval,
    SandboxRunStatus,
    SandboxApprovalStatus,
)
from apps.automation_sandbox.serializers import (
    WorkflowSandboxRunSerializer,
    WorkflowSandboxStepLogSerializer,
    WorkflowSandboxArtifactSerializer,
    WorkflowSandboxScenarioSerializer,
    WorkflowSandboxApprovalSerializer,
)
from apps.automation_sandbox.services.workflow_sandbox_engine import WorkflowSandboxEngine


class SandboxRunViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkflowSandboxRunSerializer

    def get_queryset(self):
        return WorkflowSandboxRun.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, started_by=self.request.user.id)

    @action(detail=True, methods=['get'])
    def steps(self, request, pk=None):
        run = self.get_object()
        serializer = WorkflowSandboxStepLogSerializer(run.steps.all(), many=True)
        return success_response(data=serializer.data)

    @action(detail=True, methods=['get'])
    def artifacts(self, request, pk=None):
        run = self.get_object()
        serializer = WorkflowSandboxArtifactSerializer(run.artifacts.all(), many=True)
        return success_response(data=serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        run = self.get_object()
        if run.status == SandboxRunStatus.RUNNING:
            run.status = SandboxRunStatus.CANCELLED
            run.save()
            return success_response(message="Run cancelled.")
        return error_response("Can only cancel running simulations.")


class SandboxScenarioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkflowSandboxScenarioSerializer

    def get_queryset(self):
        from django.db.models import Q
        return WorkflowSandboxScenario.objects.filter(
            Q(tenant_id=self.request.user.tenant_id) | Q(is_system_scenario=True)
        )

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, created_by=self.request.user.id)


class SandboxSimulationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        workflow_id = request.data.get('workflow_id')
        input_context = request.data.get('input_context', {})
        run_name = request.data.get('run_name')
        
        try:
            run = WorkflowSandboxEngine.create_sandbox_run(
                tenant_id=request.user.tenant_id,
                workflow_id=workflow_id,
                started_by=request.user.id,
                input_context=input_context,
                run_name=run_name
            )
            
            # For now, execute synchronously for immediate feedback
            # In production this might be a Celery task
            WorkflowSandboxEngine.simulate_workflow(run.id)
            
            return success_response(
                data=WorkflowSandboxRunSerializer(run).data,
                message="Simulation completed."
            )
        except Exception as e:
            return error_response(str(e))


class SandboxApprovalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkflowSandboxApprovalSerializer

    def get_queryset(self):
        return WorkflowSandboxApproval.objects.filter(tenant_id=self.request.user.tenant_id)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        approval = self.get_object()
        approval.approval_status = SandboxApprovalStatus.APPROVED
        approval.reviewed_by = request.user.id
        approval.approved_at = timezone.now()
        approval.review_notes = request.data.get('notes', '')
        approval.save()
        return success_response(message="Sandbox run approved.")

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        approval = self.get_object()
        approval.approval_status = SandboxApprovalStatus.REJECTED
        approval.reviewed_by = request.user.id
        approval.review_notes = request.data.get('notes', '')
        approval.save()
        return success_response(message="Sandbox run rejected.")
