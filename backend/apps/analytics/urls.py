from django.urls import path
from apps.analytics import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='analytics-dashboard'),
    path('hiring-intelligence/', views.HiringIntelligenceDashboardView.as_view(), name='analytics-hiring-intelligence'),
    path('recruitment/', views.RecruitmentAnalyticsView.as_view(), name='analytics-recruitment'),
    path('pipeline/', views.PipelineAnalyticsView.as_view(), name='analytics-pipeline'),
    path('agencies/', views.AgencyAnalyticsView.as_view(), name='analytics-agencies'),
    path('candidates/', views.CandidateAnalyticsView.as_view(), name='analytics-candidates'),
    path('interviews/', views.InterviewAnalyticsView.as_view(), name='analytics-interviews'),
    path('interviews/intelligence/', views.InterviewIntelligenceAnalyticsView.as_view(), name='analytics-interviews-intelligence'),
    path('recruiter-intelligence/', views.RecruiterIntelligenceView.as_view(), name='analytics-recruiter-intelligence'),
]
