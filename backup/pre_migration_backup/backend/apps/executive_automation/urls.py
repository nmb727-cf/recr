from django.urls import path
from . import views

urlpatterns = [
    # Summary & snapshot
    path('summary/',                  views.ExecutiveSummaryView.as_view(),            name='exec-summary'),
    path('snapshot/trigger/',         views.ExecutiveSnapshotTriggerView.as_view(),    name='exec-snapshot-trigger'),

    # ROI
    path('roi/',                      views.ExecutiveROIListView.as_view(),            name='exec-roi-list'),

    # Risks
    path('risks/',                    views.ExecutiveRiskListView.as_view(),           name='exec-risk-list'),
    path('risks/<uuid:risk_id>/',     views.ExecutiveRiskDetailView.as_view(),         name='exec-risk-detail'),
    path('risks/<uuid:risk_id>/status/', views.ExecutiveRiskUpdateStatusView.as_view(), name='exec-risk-status'),

    # Departments
    path('departments/',              views.ExecutiveDepartmentListView.as_view(),     name='exec-department-list'),

    # Opportunities
    path('opportunities/',            views.ExecutiveOpportunityListView.as_view(),    name='exec-opportunity-list'),
    path('opportunities/<uuid:opp_id>/', views.ExecutiveOpportunityDetailView.as_view(), name='exec-opportunity-detail'),
    path('opportunities/<uuid:opp_id>/status/', views.ExecutiveOpportunityUpdateStatusView.as_view(), name='exec-opportunity-status'),

    # Analytics & insights
    path('business-impact/',          views.ExecutiveBusinessImpactView.as_view(),     name='exec-business-impact'),
    path('insights/',                 views.ExecutiveInsightsView.as_view(),           name='exec-insights'),

    # Command Center widget
    path('widget/',                   views.ExecutiveControlTowerWidgetView.as_view(), name='exec-widget'),
]
