from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.core.responses import success_response, error_response
from apps.automation_command_center.permissions import CanView, CanManage, CanAdmin

from .models import (
    AutomationSystemReadiness,
    AutomationCompletionCheck,
    AutomationGapItem,
    AutomationProductionGate,
    AutomationCompletionReport
)
from .serializers import (
    AutomationSystemReadinessSerializer,
    AutomationCompletionCheckSerializer,
    AutomationGapItemSerializer,
    AutomationProductionGateSerializer,
    AutomationCompletionReportSerializer
)
from .automation_system_completion_engine import AutomationSystemCompletionEngine

class ReadinessOverviewView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        readiness = AutomationSystemReadiness.objects.filter(tenant_id=request.user.tenant_id).first()
        if not readiness:
            # If not assessed yet, run initial setup
            engine = AutomationSystemCompletionEngine()
            readiness = engine.run_completion_assessment(request.user.tenant_id)
            
        return success_response(data={
            'readiness': AutomationSystemReadinessSerializer(readiness).data
        }, message="Readiness retrieved.")

class CompletionChecksView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        checks = AutomationCompletionCheck.objects.filter(tenant_id=request.user.tenant_id)
        return success_response(data={
            'checks': AutomationCompletionCheckSerializer(checks, many=True).data
        }, message="Completion checks retrieved.")

class GapItemsView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        gaps = AutomationGapItem.objects.filter(tenant_id=request.user.tenant_id)
        return success_response(data={
            'gaps': AutomationGapItemSerializer(gaps, many=True).data
        }, message="Gap items retrieved.")

class ProductionGatesView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        gates = AutomationProductionGate.objects.filter(tenant_id=request.user.tenant_id)
        return success_response(data={
            'gates': AutomationProductionGateSerializer(gates, many=True).data
        }, message="Production gates retrieved.")

class CompletionReportsView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        reports = AutomationCompletionReport.objects.filter(tenant_id=request.user.tenant_id).order_by('-created_at')
        return success_response(data={
            'reports': AutomationCompletionReportSerializer(reports, many=True).data
        }, message="Completion reports retrieved.")

class EndToEndFlowsView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        # Specific view filtering for 'api' or E2E flow related checks
        checks = AutomationCompletionCheck.objects.filter(
            tenant_id=request.user.tenant_id, 
            check_category='api'
        )
        return success_response(data={
            'end_to_end_flows': AutomationCompletionCheckSerializer(checks, many=True).data
        }, message="End-to-End flow checks retrieved.")

class RunAssessmentView(APIView):
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request):
        engine = AutomationSystemCompletionEngine()
        readiness = engine.run_completion_assessment(request.user.tenant_id)
        return success_response(data={
            'readiness': AutomationSystemReadinessSerializer(readiness).data
        }, message="System Completion Assessment triggered successfully.")

class GenerateReportView(APIView):
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request):
        report_type = request.data.get('report_type', 'qa_report')
        engine = AutomationSystemCompletionEngine()
        report = engine.generate_completion_reports(request.user.tenant_id, report_type)
        return success_response(data={
            'report': AutomationCompletionReportSerializer(report).data
        }, message=f"{report_type} generated successfully.")

class AcknowledgeGapView(APIView):
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request, pk):
        gap = get_object_or_404(AutomationGapItem, id=pk, tenant_id=request.user.tenant_id)
        gap.status = 'acknowledged'
        gap.save()
        return success_response(data={
            'gap': AutomationGapItemSerializer(gap).data
        }, message="Gap marked as acknowledged.")

class RecheckGateView(APIView):
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request, pk):
        gate = get_object_or_404(AutomationProductionGate, id=pk, tenant_id=request.user.tenant_id)
        
        # Trigger assessment just for gates updating
        engine = AutomationSystemCompletionEngine()
        engine.evaluate_production_gates(request.user.tenant_id)
        
        # Refetch
        gate.refresh_from_db()
        return success_response(data={
            'gate': AutomationProductionGateSerializer(gate).data
        }, message="Production gate rechecked.")
