from django.urls import path

from apps.automation import views

urlpatterns = [
    path('autonomous-engine/', views.AutonomousHiringView.as_view(), name='automation-autonomous-engine'),
    path('autonomous-engine/actions/<uuid:pk>/', views.AutonomousActionUpdateView.as_view(), name='automation-autonomous-action-update'),
    path('orchestrator/', views.GlobalOrchestratorDashboardView.as_view(), name='automation-orchestrator-dashboard'),
    path('rules/', views.AutomationRuleListView.as_view(), name='automation-rule-list'),
    path('rules/<uuid:pk>/', views.AutomationRuleDetailView.as_view(), name='automation-rule-detail'),
    path('trigger/', views.AutomationTriggerView.as_view(), name='automation-trigger'),
    path('logs/', views.AutomationLogListView.as_view(), name='automation-log-list'),
]

