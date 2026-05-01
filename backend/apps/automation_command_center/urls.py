from django.urls import path

from . import views

urlpatterns = [
    path('overview/', views.OverviewView.as_view(), name='acc-overview'),
    path('workflows/', views.WorkflowListView.as_view(), name='acc-workflows'),
    path('activity/', views.ActivityFeedView.as_view(), name='acc-activity'),
    path('ai-suggestions/', views.AISuggestionsView.as_view(), name='acc-ai-suggestions'),
    path('health/', views.HealthView.as_view(), name='acc-health'),
    path('executions/', views.ExecutionMonitorView.as_view(), name='acc-executions'),
    path('learning-summary/', views.LearningSummaryView.as_view(), name='acc-learning-summary'),
    path('ai-brain-summary/', views.AIBrainSummaryView.as_view(), name='acc-ai-brain-summary'),
    path('completion-summary/', views.CompletionSummaryView.as_view(), name='acc-completion-summary'),
    path('pause-all/', views.PauseAllView.as_view(), name='acc-pause-all'),
    path('resume-all/', views.ResumeAllView.as_view(), name='acc-resume-all'),
    path('emergency-stop/', views.EmergencyStopView.as_view(), name='acc-emergency-stop'),
]
