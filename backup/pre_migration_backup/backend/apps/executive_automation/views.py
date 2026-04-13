from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.core.responses import success_response, error_response
from .models import (
    ExecutiveAutomationSummary,
    ExecutiveAutomationROI,
    ExecutiveAutomationRisk,
    ExecutiveAutomationDepartment,
    ExecutiveAutomationOpportunity,
    ROIPeriod,
    RiskStatus,
    RiskSeverity,
)
from .serializers import (
    ExecutiveAutomationSummarySerializer,
    ExecutiveAutomationROISerializer,
    ExecutiveAutomationRiskSerializer,
    RiskStatusUpdateSerializer,
    ExecutiveAutomationDepartmentSerializer,
    ExecutiveAutomationOpportunitySerializer,
    OpportunityStatusUpdateSerializer,
)
from .permissions import ExecutiveReadPermission, ExecutiveWritePermission, ExecutiveAdminPermission
from .services import automation_executive_engine as exec_engine


def _tid(request):
    return getattr(request.user, 'tenant_id', None)


# ---------------------------------------------------------------------------
# Executive Summary
# ---------------------------------------------------------------------------

class ExecutiveSummaryView(APIView):
    permission_classes = [IsAuthenticated, ExecutiveReadPermission]

    def get(self, request):
        qs = ExecutiveAutomationSummary.objects.filter(
            tenant_id=_tid(request), is_deleted=False
        ).order_by('-snapshot_date')
        latest = qs.first()
        if not latest:
            return success_response({'summary': None, 'message': 'No snapshot available yet.'})
        data = ExecutiveAutomationSummarySerializer(latest).data
        # also include 30-day trend (last 30 snapshots)
        trend = ExecutiveAutomationSummarySerializer(qs[:30], many=True).data
        return success_response({'summary': data, 'trend': trend})


# ---------------------------------------------------------------------------
# Executive Snapshot Trigger
# ---------------------------------------------------------------------------

class ExecutiveSnapshotTriggerView(APIView):
    permission_classes = [IsAuthenticated, ExecutiveAdminPermission]

    def post(self, request):
        tenant_id = _tid(request)
        try:
            result = exec_engine.run_executive_snapshot(tenant_id)
            return success_response(result)
        except Exception as exc:
            return error_response(str(exc), status=500)


# ---------------------------------------------------------------------------
# ROI
# ---------------------------------------------------------------------------

class ExecutiveROIListView(APIView):
    permission_classes = [IsAuthenticated, ExecutiveReadPermission]

    def get(self, request):
        period = request.query_params.get('period', ROIPeriod.MONTHLY)
        if period not in ROIPeriod.values:
            return error_response('Invalid period. Choices: daily, weekly, monthly, yearly.', status=400)

        qs = ExecutiveAutomationROI.objects.filter(
            tenant_id=_tid(request), period=period, is_deleted=False
        ).order_by('-period_start')[:24]  # up to 24 data points
        return success_response({'roi': ExecutiveAutomationROISerializer(qs, many=True).data, 'period': period})


# ---------------------------------------------------------------------------
# Risks
# ---------------------------------------------------------------------------

class ExecutiveRiskListView(APIView):
    permission_classes = [IsAuthenticated, ExecutiveReadPermission]

    def get(self, request):
        qs = ExecutiveAutomationRisk.objects.filter(tenant_id=_tid(request), is_deleted=False)

        severity = request.query_params.get('severity')
        if severity:
            qs = qs.filter(severity=severity)

        status = request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        else:
            # default: exclude resolved/ignored
            qs = qs.exclude(status__in=[RiskStatus.RESOLVED, RiskStatus.IGNORED])

        risk_type = request.query_params.get('risk_type')
        if risk_type:
            qs = qs.filter(risk_type=risk_type)

        return success_response({
            'risks': ExecutiveAutomationRiskSerializer(qs.order_by('-severity', '-created_at'), many=True).data,
            'total': qs.count(),
        })


class ExecutiveRiskDetailView(APIView):
    permission_classes = [IsAuthenticated, ExecutiveReadPermission]

    def get(self, request, risk_id):
        try:
            risk = ExecutiveAutomationRisk.objects.get(
                id=risk_id, tenant_id=_tid(request), is_deleted=False
            )
        except ExecutiveAutomationRisk.DoesNotExist:
            return error_response('Risk not found.', status=404)
        return success_response({'risk': ExecutiveAutomationRiskSerializer(risk).data})


class ExecutiveRiskUpdateStatusView(APIView):
    permission_classes = [IsAuthenticated, ExecutiveWritePermission]

    def post(self, request, risk_id):
        try:
            risk = ExecutiveAutomationRisk.objects.get(
                id=risk_id, tenant_id=_tid(request), is_deleted=False
            )
        except ExecutiveAutomationRisk.DoesNotExist:
            return error_response('Risk not found.', status=404)

        ser = RiskStatusUpdateSerializer(data=request.data)
        if not ser.is_valid():
            return error_response(ser.errors, status=400)

        risk.status = ser.validated_data['status']
        risk.save(update_fields=['status', 'updated_at'])
        return success_response({'risk': ExecutiveAutomationRiskSerializer(risk).data})


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

class ExecutiveDepartmentListView(APIView):
    permission_classes = [IsAuthenticated, ExecutiveReadPermission]

    def get(self, request):
        # latest snapshot date
        latest_snap = ExecutiveAutomationDepartment.objects.filter(
            tenant_id=_tid(request), is_deleted=False
        ).order_by('-snapshot_date').values_list('snapshot_date', flat=True).first()

        if not latest_snap:
            return success_response({'departments': [], 'snapshot_date': None})

        qs = ExecutiveAutomationDepartment.objects.filter(
            tenant_id=_tid(request), snapshot_date=latest_snap, is_deleted=False
        ).order_by('-automation_coverage')

        return success_response({
            'departments': ExecutiveAutomationDepartmentSerializer(qs, many=True).data,
            'snapshot_date': str(latest_snap),
        })


# ---------------------------------------------------------------------------
# Opportunities
# ---------------------------------------------------------------------------

class ExecutiveOpportunityListView(APIView):
    permission_classes = [IsAuthenticated, ExecutiveReadPermission]

    def get(self, request):
        qs = ExecutiveAutomationOpportunity.objects.filter(
            tenant_id=_tid(request), is_deleted=False
        )

        priority = request.query_params.get('priority')
        if priority:
            qs = qs.filter(priority=priority)

        status = request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        else:
            qs = qs.exclude(status__in=['completed', 'dismissed'])

        opp_type = request.query_params.get('opportunity_type')
        if opp_type:
            qs = qs.filter(opportunity_type=opp_type)

        return success_response({
            'opportunities': ExecutiveAutomationOpportunitySerializer(
                qs.order_by('-priority', '-created_at'), many=True
            ).data,
            'total': qs.count(),
        })


class ExecutiveOpportunityDetailView(APIView):
    permission_classes = [IsAuthenticated, ExecutiveReadPermission]

    def get(self, request, opp_id):
        try:
            opp = ExecutiveAutomationOpportunity.objects.get(
                id=opp_id, tenant_id=_tid(request), is_deleted=False
            )
        except ExecutiveAutomationOpportunity.DoesNotExist:
            return error_response('Opportunity not found.', status=404)
        return success_response({'opportunity': ExecutiveAutomationOpportunitySerializer(opp).data})


class ExecutiveOpportunityUpdateStatusView(APIView):
    permission_classes = [IsAuthenticated, ExecutiveWritePermission]

    def post(self, request, opp_id):
        try:
            opp = ExecutiveAutomationOpportunity.objects.get(
                id=opp_id, tenant_id=_tid(request), is_deleted=False
            )
        except ExecutiveAutomationOpportunity.DoesNotExist:
            return error_response('Opportunity not found.', status=404)

        ser = OpportunityStatusUpdateSerializer(data=request.data)
        if not ser.is_valid():
            return error_response(ser.errors, status=400)

        opp.status = ser.validated_data['status']
        if 'assigned_to' in ser.validated_data:
            opp.assigned_to = ser.validated_data['assigned_to']
        opp.save(update_fields=['status', 'assigned_to', 'updated_at'])
        return success_response({'opportunity': ExecutiveAutomationOpportunitySerializer(opp).data})


# ---------------------------------------------------------------------------
# Business Impact / Analytics
# ---------------------------------------------------------------------------

class ExecutiveBusinessImpactView(APIView):
    """Aggregated business impact metrics across all ROI periods."""
    permission_classes = [IsAuthenticated, ExecutiveReadPermission]

    def get(self, request):
        from django.db.models import Sum, Avg

        tid = _tid(request)

        monthly = ExecutiveAutomationROI.objects.filter(
            tenant_id=tid, period=ROIPeriod.MONTHLY, is_deleted=False
        ).aggregate(
            total_hours=Sum('hours_saved'),
            total_cost=Sum('operational_cost_reduction'),
            total_tasks=Sum('manual_tasks_reduced'),
            avg_success=Avg('success_rate'),
        )

        latest_summary = ExecutiveAutomationSummary.objects.filter(
            tenant_id=tid, is_deleted=False
        ).order_by('-snapshot_date').first()

        open_risks = ExecutiveAutomationRisk.objects.filter(
            tenant_id=tid, is_deleted=False,
            status__in=[RiskStatus.OPEN, RiskStatus.ACKNOWLEDGED]
        ).count()

        critical_risks = ExecutiveAutomationRisk.objects.filter(
            tenant_id=tid, is_deleted=False,
            severity=RiskSeverity.CRITICAL,
            status__in=[RiskStatus.OPEN, RiskStatus.ACKNOWLEDGED]
        ).count()

        return success_response({
            'monthly_roi': {
                'total_hours_saved':      float(monthly['total_hours'] or 0),
                'total_cost_reduction':   float(monthly['total_cost'] or 0),
                'total_tasks_reduced':    monthly['total_tasks'] or 0,
                'avg_success_rate':       float(monthly['avg_success'] or 0),
            },
            'current_state': {
                'coverage_percent':    float(latest_summary.automation_coverage_percent) if latest_summary else 0,
                'maturity_level':      latest_summary.automation_maturity_level if latest_summary else 'unknown',
                'business_impact_score': float(latest_summary.business_impact_score) if latest_summary else 0,
            },
            'risk_exposure': {
                'open_risks':     open_risks,
                'critical_risks': critical_risks,
            },
        })


# ---------------------------------------------------------------------------
# Insights (narrative)
# ---------------------------------------------------------------------------

class ExecutiveInsightsView(APIView):
    permission_classes = [IsAuthenticated, ExecutiveReadPermission]

    def get(self, request):
        tenant_id = _tid(request)
        try:
            insights = exec_engine.generate_executive_insights(tenant_id)
            return success_response({'insights': insights})
        except Exception as exc:
            return error_response(str(exc), status=500)


# ---------------------------------------------------------------------------
# Command Center Widget Summary
# ---------------------------------------------------------------------------

class ExecutiveControlTowerWidgetView(APIView):
    """Compact payload for Command Center / Dashboard widget."""
    permission_classes = [IsAuthenticated, ExecutiveReadPermission]

    def get(self, request):
        tid = _tid(request)

        latest = ExecutiveAutomationSummary.objects.filter(
            tenant_id=tid, is_deleted=False
        ).order_by('-snapshot_date').first()

        open_critical = ExecutiveAutomationRisk.objects.filter(
            tenant_id=tid, is_deleted=False,
            severity__in=[RiskSeverity.CRITICAL, RiskSeverity.HIGH],
            status__in=[RiskStatus.OPEN, RiskStatus.ACKNOWLEDGED],
        ).count()

        top_opportunities = ExecutiveAutomationOpportunity.objects.filter(
            tenant_id=tid, is_deleted=False,
            status__in=['new', 'assigned', 'in_progress'],
        ).order_by('-priority', '-created_at')[:3]

        return success_response({
            'kpis': {
                'coverage_percent':     float(latest.automation_coverage_percent) if latest else 0,
                'maturity_level':       latest.automation_maturity_level if latest else 'unknown',
                'time_saved_hours':     float(latest.time_saved_hours) if latest else 0,
                'business_impact_score': float(latest.business_impact_score) if latest else 0,
            },
            'open_critical_risks': open_critical,
            'top_opportunities': ExecutiveAutomationOpportunitySerializer(
                top_opportunities, many=True
            ).data,
            'snapshot_date': str(latest.snapshot_date) if latest else None,
        })
