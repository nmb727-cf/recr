"""
Automation Maturity Center — API Views
"""
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import error_response, success_response

from .models import (
    AutomationMaturityAssessment,
    AutomationMaturityRecommendation,
    AutomationMaturityRoadmap,
    AutomationBusinessTransformationMetric,
    AutomationModuleMaturity,
    AutomationTeamAdoption,
    MaturityLevel,
    RecommendationStatus,
)
from .permissions import CanAdmin, CanManage, CanView
from .serializers import (
    AutomationMaturityAssessmentListSerializer,
    AutomationMaturityAssessmentSerializer,
    AutomationMaturityRecommendationSerializer,
    AutomationMaturityRoadmapSerializer,
    AutomationBusinessTransformationMetricSerializer,
    AutomationModuleMaturitySerializer,
    AutomationTeamAdoptionSerializer,
)
from .services.automation_maturity_engine import (
    generate_maturity_roadmap,
    run_full_assessment,
)


def _tid(request):
    return request.user.tenant_id


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

class MaturityOverviewView(APIView):
    """GET /api/v1/automation-maturity/overview/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tid(request)
        latest = (
            AutomationMaturityAssessment.objects
            .filter(tenant_id=tid, is_deleted=False)
            .order_by('-assessment_date')
            .prefetch_related('module_scores')
            .first()
        )
        if not latest:
            return success_response(
                data={'message': 'No assessment found. POST /recalculate/ to run one.'},
                message='No maturity data yet.',
            )

        modules = list(latest.module_scores.all().order_by('-maturity_score'))
        strongest = modules[0] if modules else None
        weakest   = modules[-1] if modules else None

        open_recs = AutomationMaturityRecommendation.objects.filter(
            tenant_id=tid,
            status__in=[RecommendationStatus.NEW, RecommendationStatus.ACKNOWLEDGED],
            is_deleted=False,
        ).order_by('-priority').first()

        data = {
            'overall_maturity_score': float(latest.overall_maturity_score),
            'maturity_level':         latest.maturity_level,
            'coverage_score':         float(latest.coverage_score),
            'adoption_score':         float(latest.adoption_score),
            'governance_score':       float(latest.governance_score),
            'reliability_score':      float(latest.reliability_score),
            'intelligence_score':     float(latest.intelligence_score),
            'operating_score':        float(latest.operating_score),
            'business_impact_score':  float(latest.business_impact_score),
            'assessment_date':        latest.assessment_date.isoformat(),
            'strongest_module':       strongest.module_scope if strongest else None,
            'weakest_module':         weakest.module_scope if weakest else None,
            'open_recommendation_count': AutomationMaturityRecommendation.objects.filter(
                tenant_id=tid,
                status__in=[RecommendationStatus.NEW, RecommendationStatus.ACKNOWLEDGED],
                is_deleted=False,
            ).count(),
            'top_recommendation': {
                'title':    open_recs.title,
                'priority': open_recs.priority,
            } if open_recs else None,
        }
        return success_response(data=data, message='Maturity overview retrieved.')


# ---------------------------------------------------------------------------
# Module Maturity Matrix
# ---------------------------------------------------------------------------

class MaturityModulesView(APIView):
    """GET /api/v1/automation-maturity/modules/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid    = _tid(request)
        latest = (
            AutomationMaturityAssessment.objects
            .filter(tenant_id=tid, is_deleted=False)
            .order_by('-assessment_date')
            .first()
        )
        if not latest:
            return success_response(data=[], message='No assessment data.')

        modules = AutomationModuleMaturity.objects.filter(
            tenant_id=tid, assessment=latest, is_deleted=False
        ).order_by('-maturity_score')
        serializer = AutomationModuleMaturitySerializer(modules, many=True)
        return success_response(data=serializer.data, message='Module maturity retrieved.')


# ---------------------------------------------------------------------------
# Team Adoption
# ---------------------------------------------------------------------------

class MaturityTeamsView(APIView):
    """GET /api/v1/automation-maturity/teams/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid    = _tid(request)
        latest = (
            AutomationMaturityAssessment.objects
            .filter(tenant_id=tid, is_deleted=False)
            .order_by('-assessment_date')
            .first()
        )
        if not latest:
            return success_response(data=[], message='No adoption data.')

        teams = AutomationTeamAdoption.objects.filter(
            tenant_id=tid, assessment=latest, is_deleted=False
        ).order_by('-adoption_score')
        serializer = AutomationTeamAdoptionSerializer(teams, many=True)

        # Summary signals
        all_scores = [float(t.adoption_score) for t in teams]
        top_teams  = [t for t in teams if float(t.adoption_score) >= 70]
        low_teams  = [t for t in teams if float(t.adoption_score) < 30]

        return success_response(
            data={
                'teams': serializer.data,
                'summary': {
                    'total_teams':     len(all_scores),
                    'avg_adoption':    round(sum(all_scores) / len(all_scores), 2) if all_scores else 0,
                    'top_team_count':  len(top_teams),
                    'low_team_count':  len(low_teams),
                },
            },
            message='Team adoption retrieved.',
        )


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

class MaturityRecommendationsView(APIView):
    """GET /api/v1/automation-maturity/recommendations/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tid(request)
        qs  = AutomationMaturityRecommendation.objects.filter(
            tenant_id=tid, is_deleted=False
        )
        status_filter   = request.query_params.get('status')
        priority_filter = request.query_params.get('priority')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if priority_filter:
            qs = qs.filter(priority=priority_filter)

        serializer = AutomationMaturityRecommendationSerializer(
            qs.order_by('-priority', '-created_at'), many=True
        )
        return success_response(data=serializer.data, message='Recommendations retrieved.')


class MaturityRecommendationActionView(APIView):
    """POST /api/v1/automation-maturity/recommendations/{id}/action/"""
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request, pk):
        action = request.data.get('action')
        if action not in ('acknowledge', 'start', 'complete', 'ignore'):
            return error_response(
                message='action must be acknowledge | start | complete | ignore',
                status_code=400,
            )
        status_map = {
            'acknowledge': RecommendationStatus.ACKNOWLEDGED,
            'start':       RecommendationStatus.IN_PROGRESS,
            'complete':    RecommendationStatus.COMPLETED,
            'ignore':      RecommendationStatus.IGNORED,
        }
        updated = AutomationMaturityRecommendation.objects.filter(
            id=pk, tenant_id=_tid(request), is_deleted=False
        ).update(status=status_map[action])
        if not updated:
            return error_response(message='Recommendation not found.', status_code=404)
        return success_response(message=f'Recommendation {action}d.')


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------

class MaturityRoadmapView(APIView):
    """GET /api/v1/automation-maturity/roadmap/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tid(request)
        roadmap = (
            AutomationMaturityRoadmap.objects
            .filter(tenant_id=tid, is_active=True, is_deleted=False)
            .order_by('-created_at')
            .first()
        )
        if not roadmap:
            return success_response(
                data={'message': 'No roadmap yet. POST /roadmap/generate/ to create one.'},
                message='No roadmap found.',
            )
        return success_response(
            data=AutomationMaturityRoadmapSerializer(roadmap).data,
            message='Roadmap retrieved.',
        )


class MaturityRoadmapGenerateView(APIView):
    """POST /api/v1/automation-maturity/roadmap/generate/"""
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request):
        tid = _tid(request)

        # Determine current level from latest assessment
        latest = (
            AutomationMaturityAssessment.objects
            .filter(tenant_id=tid, is_deleted=False)
            .order_by('-assessment_date')
            .first()
        )
        current_level = latest.maturity_level if latest else 'manual'
        target_level  = request.data.get('target_level') or _next_level(current_level)

        if current_level == target_level:
            return error_response(
                message='Already at target level or higher. Choose a higher target.',
                status_code=400,
            )

        plan = generate_maturity_roadmap(tid, current_level, target_level)

        # Deactivate previous roadmaps
        AutomationMaturityRoadmap.objects.filter(
            tenant_id=tid, is_active=True, is_deleted=False
        ).update(is_active=False)

        roadmap = AutomationMaturityRoadmap.objects.create(
            tenant_id             = tid,
            roadmap_name          = plan['roadmap_name'],
            current_level         = plan['current_level'],
            target_level          = plan['target_level'],
            roadmap_steps         = plan['roadmap_steps'],
            expected_timeline_days= plan['expected_timeline_days'],
            created_by            = request.user.id if hasattr(request.user, 'id') else None,
            is_active             = True,
        )
        return success_response(
            data=AutomationMaturityRoadmapSerializer(roadmap).data,
            message='Maturity roadmap generated.',
            status_code=201,
        )


def _next_level(current: str) -> str:
    order = ['manual', 'assisted', 'structured', 'optimized', 'autonomous']
    idx   = order.index(current) if current in order else 0
    return order[min(idx + 1, len(order) - 1)]


# ---------------------------------------------------------------------------
# Transformation Metrics
# ---------------------------------------------------------------------------

class MaturityTransformationView(APIView):
    """GET /api/v1/automation-maturity/transformation/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid = _tid(request)
        qs  = AutomationBusinessTransformationMetric.objects.filter(
            tenant_id=tid, is_deleted=False
        ).order_by('-metric_date')[:50]
        serializer = AutomationBusinessTransformationMetricSerializer(qs, many=True)

        # Aggregate across all processes
        metrics = list(qs)
        if metrics:
            avg_effort   = round(sum(float(m.manual_effort_reduction_percent) for m in metrics) / len(metrics), 2)
            avg_response = round(sum(float(m.response_time_improvement_percent) for m in metrics) / len(metrics), 2)
            avg_sla      = round(sum(float(m.sla_improvement_percent) for m in metrics) / len(metrics), 2)
            avg_usage    = round(sum(float(m.automation_usage_percent) for m in metrics) / len(metrics), 2)
        else:
            avg_effort = avg_response = avg_sla = avg_usage = 0.0

        return success_response(
            data={
                'metrics': serializer.data,
                'summary': {
                    'avg_manual_effort_reduction_percent':   avg_effort,
                    'avg_response_time_improvement_percent': avg_response,
                    'avg_sla_improvement_percent':           avg_sla,
                    'avg_automation_usage_percent':          avg_usage,
                },
            },
            message='Transformation metrics retrieved.',
        )


# ---------------------------------------------------------------------------
# Trends
# ---------------------------------------------------------------------------

class MaturityTrendsView(APIView):
    """GET /api/v1/automation-maturity/trends/"""
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid   = _tid(request)
        limit = min(int(request.query_params.get('limit', 30)), 90)

        assessments = (
            AutomationMaturityAssessment.objects
            .filter(tenant_id=tid, is_deleted=False)
            .order_by('-assessment_date')[:limit]
        )

        trend_data = AutomationMaturityAssessmentListSerializer(
            list(reversed(list(assessments))), many=True
        ).data

        # Compute direction (improving / declining / stable)
        scores = [float(a.overall_maturity_score) for a in list(reversed(list(assessments)))]
        if len(scores) >= 2:
            delta = scores[-1] - scores[0]
            if delta > 2:    direction = 'improving'
            elif delta < -2: direction = 'declining'
            else:            direction = 'stable'
        else:
            direction = 'insufficient_data'

        return success_response(
            data={
                'trend': trend_data,
                'direction': direction,
                'data_points': len(trend_data),
            },
            message='Maturity trends retrieved.',
        )


# ---------------------------------------------------------------------------
# Recalculate (trigger full assessment)
# ---------------------------------------------------------------------------

class MaturityRecalculateView(APIView):
    """POST /api/v1/automation-maturity/recalculate/"""
    permission_classes = [IsAuthenticated, CanManage]

    def post(self, request):
        tid = _tid(request)
        try:
            assessment = run_full_assessment(tenant_id=tid)
        except Exception as exc:
            return error_response(
                message=f'Assessment failed: {str(exc)}',
                status_code=500,
            )
        return success_response(
            data={
                'assessment_id':          str(assessment.id),
                'overall_maturity_score': float(assessment.overall_maturity_score),
                'maturity_level':         assessment.maturity_level,
                'assessment_date':        assessment.assessment_date.isoformat(),
            },
            message='Maturity assessment completed.',
        )


# ---------------------------------------------------------------------------
# Command Center — Maturity Summary Widget
# ---------------------------------------------------------------------------

class MaturitySummaryView(APIView):
    """
    GET /api/v1/automation-maturity/summary/
    Used by the Automation Command Center maturity widget.
    """
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request):
        tid    = _tid(request)
        latest = (
            AutomationMaturityAssessment.objects
            .filter(tenant_id=tid, is_deleted=False)
            .order_by('-assessment_date')
            .first()
        )
        if not latest:
            return success_response(
                data={
                    'maturity_level': 'manual',
                    'overall_score':  0,
                    'weakest_area':   None,
                    'top_recommendation': None,
                    'roadmap_active': False,
                },
                message='No maturity data yet.',
            )

        # Weakest dimension
        dims = {
            'Coverage':     float(latest.coverage_score),
            'Adoption':     float(latest.adoption_score),
            'Governance':   float(latest.governance_score),
            'Reliability':  float(latest.reliability_score),
            'Intelligence': float(latest.intelligence_score),
            'Operating':    float(latest.operating_score),
        }
        weakest = min(dims, key=dims.get)

        top_rec = AutomationMaturityRecommendation.objects.filter(
            tenant_id=tid,
            status__in=[RecommendationStatus.NEW, RecommendationStatus.ACKNOWLEDGED],
            is_deleted=False,
        ).order_by('-priority', '-created_at').first()

        roadmap_active = AutomationMaturityRoadmap.objects.filter(
            tenant_id=tid, is_active=True, is_deleted=False
        ).exists()

        return success_response(
            data={
                'maturity_level':    latest.maturity_level,
                'overall_score':     float(latest.overall_maturity_score),
                'weakest_area':      weakest,
                'weakest_score':     dims[weakest],
                'top_recommendation':{'title': top_rec.title, 'priority': top_rec.priority} if top_rec else None,
                'roadmap_active':    roadmap_active,
                'assessment_date':   latest.assessment_date.isoformat(),
            },
            message='Maturity summary retrieved.',
        )
