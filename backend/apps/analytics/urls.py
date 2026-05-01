from django.urls import path
from apps.analytics import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='analytics-dashboard'),
    path('hiring-intelligence/', views.HiringIntelligenceDashboardView.as_view(), name='analytics-hiring-intelligence'),
    path('hiring-ai-brain/', views.HiringAIBrainView.as_view(), name='analytics-hiring-ai-brain'),
    path('intelligence/jobs/<uuid:job_id>/', views.IntelligenceJobView.as_view(), name='analytics-intelligence-job'),
    path('intelligence/candidates/<uuid:candidate_id>/', views.IntelligenceCandidateView.as_view(), name='analytics-intelligence-candidate'),
    path('intelligence/pipeline/', views.IntelligencePipelineView.as_view(), name='analytics-intelligence-pipeline'),
    path('intelligence/recruiters/', views.IntelligenceRecruiterView.as_view(), name='analytics-intelligence-recruiter'),
    path('unified-operations/', views.UnifiedOperationsView.as_view(), name='analytics-unified-operations'),
    path('executive-decision/', views.ExecutiveDecisionView.as_view(), name='analytics-executive-decision'),
    path('control-tower/', views.GlobalControlTowerView.as_view(), name='analytics-control-tower'),
    path('recruitment/', views.RecruitmentAnalyticsView.as_view(), name='analytics-recruitment'),
    path('pipeline/', views.PipelineAnalyticsView.as_view(), name='analytics-pipeline'),
    path('agencies/', views.AgencyAnalyticsView.as_view(), name='analytics-agencies'),
    path('candidates/', views.CandidateAnalyticsView.as_view(), name='analytics-candidates'),
    path('interviews/', views.InterviewAnalyticsView.as_view(), name='analytics-interviews'),
    path('interviews/intelligence/', views.InterviewIntelligenceAnalyticsView.as_view(), name='analytics-interviews-intelligence'),
    path('recruiter-intelligence/', views.RecruiterIntelligenceView.as_view(), name='analytics-recruiter-intelligence'),
    path('intelligence-memory/', views.SystemIntelligenceMemoryView.as_view(), name='analytics-system-intelligence-memory'),
]
