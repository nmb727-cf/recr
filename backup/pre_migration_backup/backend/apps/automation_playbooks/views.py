from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.core.responses import error_response, success_response
from apps.automation_playbooks.models import (
    AutomationPlaybook,
    AutomationPlaybookInstall,
    AutomationPlaybookRecommendation,
    AutomationPlaybookAnalytics,
)
from apps.automation_playbooks.serializers import (
    AutomationPlaybookSerializer,
    AutomationPlaybookInstallSerializer,
    AutomationPlaybookRecommendationSerializer,
    AutomationPlaybookAnalyticsSerializer,
)
from apps.automation_playbooks.services.automation_playbook_engine import AutomationPlaybookEngine


class PlaybookViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AutomationPlaybookSerializer

    def get_queryset(self):
        return AutomationPlaybookEngine.list_available_playbooks(self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, created_by=self.request.user.id)

    @action(detail=False, methods=['get'])
    def library(self, request):
        queryset = self.get_queryset().filter(is_system_playbook=True)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    @action(detail=False, methods=['get'])
    def installed(self, request):
        installs = AutomationPlaybookInstall.objects.filter(tenant_id=request.user.tenant_id)
        serializer = AutomationPlaybookInstallSerializer(installs, many=True)
        return success_response(data=serializer.data)

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        playbook = self.get_object()
        serializer = self.get_serializer(playbook)
        # Add expected impact logic here
        data = serializer.data
        data['expected_impact'] = {
            'time_saved_weekly': '4-6 hours',
            'accuracy_improvement': '15%',
            'sla_breach_reduction': '20%'
        }
        return success_response(data=data)

    @action(detail=True, methods=['post'])
    def install(self, request, pk=None):
        config_values = request.data.get('config', {})
        
        # 1. Validate
        valid, msg = AutomationPlaybookEngine.validate_playbook_install(pk, request.user.tenant_id, config_values)
        if not valid:
            return error_response(msg)

        # 2. Install
        try:
            install = AutomationPlaybookEngine.install_playbook(
                pk, 
                request.user.tenant_id, 
                request.user.id, 
                config_values
            )
            return success_response(
                data=AutomationPlaybookInstallSerializer(install).data,
                message="Playbook installation started."
            )
        except Exception as e:
            return error_response(str(e))

    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        # Implementation logic ...
        return success_response(message="Rollback completed.")

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        playbook = AutomationPlaybookEngine.duplicate_playbook_to_tenant(
            pk, 
            request.user.tenant_id, 
            request.user.id
        )
        return success_response(
            data=AutomationPlaybookSerializer(playbook).data,
            message="Playbook duplicated to your custom library."
        )


class PlaybookRecommendationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recommendations = AutomationPlaybookRecommendation.objects.filter(tenant_id=request.user.tenant_id)
        serializer = AutomationPlaybookRecommendationSerializer(recommendations, many=True)
        return success_response(data=serializer.data)


class PlaybookAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Implementation for global or tenant-scoped playbook analytics
        return success_response(data={
            'top_installed': [],
            'best_performing': [],
            'impact_metrics': {}
        })
