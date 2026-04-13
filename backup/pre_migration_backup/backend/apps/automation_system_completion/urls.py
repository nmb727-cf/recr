from django.urls import path
from .views import (
    ReadinessOverviewView,
    CompletionChecksView,
    GapItemsView,
    ProductionGatesView,
    CompletionReportsView,
    EndToEndFlowsView,
    RunAssessmentView,
    GenerateReportView,
    AcknowledgeGapView,
    RecheckGateView
)

urlpatterns = [
    path('readiness/', ReadinessOverviewView.as_view(), name='completion-readiness'),
    path('checks/', CompletionChecksView.as_view(), name='completion-checks'),
    path('gaps/', GapItemsView.as_view(), name='completion-gaps'),
    path('production-gates/', ProductionGatesView.as_view(), name='completion-production-gates'),
    path('reports/', CompletionReportsView.as_view(), name='completion-reports'),
    path('end-to-end/', EndToEndFlowsView.as_view(), name='completion-end-to-end'),
    
    path('run-assessment/', RunAssessmentView.as_view(), name='completion-run-assessment'),
    path('reports/generate/', GenerateReportView.as_view(), name='completion-generate-report'),
    path('gaps/<uuid:pk>/acknowledge/', AcknowledgeGapView.as_view(), name='completion-acknowledge-gap'),
    path('gates/<uuid:pk>/recheck/', RecheckGateView.as_view(), name='completion-recheck-gate'),
]
