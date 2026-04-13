from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.core.responses import success_response, error_response
from apps.automation_change_impact.models import (
    WorkflowChangeSet,
    WorkflowDependencyMap,
    WorkflowDeploymentPlan,
    WorkflowRollbackPreview,
    WorkflowImpactAnalysis,
)
from apps.automation_change_impact.serializers import (
    WorkflowChangeSetSerializer,
    WorkflowDependencyMapSerializer,
    WorkflowDeploymentPlanSerializer,
    WorkflowRollbackPreviewSerializer,
)
from apps.automation_change_impact.services.workflow_change_impact_engine import WorkflowChangeImpactEngine

class WorkflowChangeAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        change_sets = WorkflowChangeSet.objects.filter(tenant_id=request.user.tenant_id)
        serializer = WorkflowChangeSetSerializer(change_sets, many=True)
        return success_response(data=serializer.data)

    def post(self, request):
        # /analyze/
        workflow_id = request.data.get('workflow_id')
        from_version = request.data.get('from_version', 1)
        to_version = request.data.get('to_version', 2)
        change_summary = request.data.get('change_summary', {})

        if not workflow_id:
            return error_response('workflow_id is required.')

        try:
            change_set = WorkflowChangeImpactEngine.analyze_workflow_change(
                tenant_id=request.user.tenant_id,
                workflow_id=workflow_id,
                from_version=from_version,
                to_version=to_version,
                change_summary=change_summary,
                created_by=request.user.id
            )
            serializer = WorkflowChangeSetSerializer(change_set)
            return success_response(data=serializer.data, message='Analysis complete.')
        except Exception as e:
            return error_response(str(e))

class WorkflowDependencyMapViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkflowDependencyMapSerializer

    def get_queryset(self):
        return WorkflowDependencyMap.objects.filter(tenant_id=self.request.user.tenant_id)

class WorkflowDeploymentPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = WorkflowDeploymentPlan.objects.filter(tenant_id=request.user.tenant_id)
        serializer = WorkflowDeploymentPlanSerializer(plans, many=True)
        return success_response(data=serializer.data)

    def post(self, request):
        # /deploy/
        change_set_id = request.data.get('change_set_id')
        if not change_set_id:
            return error_response('change_set_id is required.')
            
        plan = get_object_or_404(WorkflowDeploymentPlan, change_set_id=change_set_id, tenant_id=request.user.tenant_id)
        plan.status = 'in_progress'
        plan.save()
        
        return success_response(message='Deployment started.')

class WorkflowRollbackPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        change_set_id = request.query_params.get('change_set_id')
        if change_set_id:
            previews = WorkflowRollbackPreview.objects.filter(change_set_id=change_set_id, tenant_id=request.user.tenant_id)
        else:
            previews = WorkflowRollbackPreview.objects.filter(tenant_id=request.user.tenant_id)
            
        serializer = WorkflowRollbackPreviewSerializer(previews, many=True)
        return success_response(data=serializer.data)
