from django.urls import path
from apps.automation_maturity import views

urlpatterns = [
    # Core assessment endpoints
    path('overview/',         views.MaturityOverviewView.as_view(),      name='am-overview'),
    path('modules/',          views.MaturityModulesView.as_view(),        name='am-modules'),
    path('teams/',            views.MaturityTeamsView.as_view(),          name='am-teams'),
    path('recommendations/',  views.MaturityRecommendationsView.as_view(),name='am-recommendations'),
    path('recommendations/<uuid:pk>/action/',
                              views.MaturityRecommendationActionView.as_view(),
                                                                          name='am-rec-action'),
    path('roadmap/',          views.MaturityRoadmapView.as_view(),        name='am-roadmap'),
    path('roadmap/generate/', views.MaturityRoadmapGenerateView.as_view(),name='am-roadmap-generate'),
    path('transformation/',   views.MaturityTransformationView.as_view(), name='am-transformation'),
    path('trends/',           views.MaturityTrendsView.as_view(),         name='am-trends'),
    path('recalculate/',      views.MaturityRecalculateView.as_view(),    name='am-recalculate'),

    # Command Center widget
    path('summary/',          views.MaturitySummaryView.as_view(),        name='am-summary'),
]
