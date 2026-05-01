from django.urls import path

from apps.automation_tasks import views

urlpatterns = [
    # Rules CRUD
    path('rules/',           views.TaskRuleListView.as_view(),   name='wf-task-rule-list'),
    path('rules/<uuid:pk>/', views.TaskRuleDetailView.as_view(), name='wf-task-rule-detail'),

    # Executions
    path('executions/',                         views.TaskExecutionListView.as_view(), name='wf-task-execution-list'),
    path('executions/<uuid:pk>/complete/',      views.TaskCompleteView.as_view(),      name='wf-task-complete'),

    # Escalations
    path('escalations/', views.EscalationListView.as_view(), name='wf-task-escalations'),

    # Analytics
    path('analytics/', views.TaskAnalyticsView.as_view(), name='wf-task-analytics'),

    # SLA tracking (admin trigger)
    path('track-sla/', views.TaskSLATrackView.as_view(), name='wf-task-track-sla'),

    # Test task creation
    path('test/', views.TaskTestView.as_view(), name='wf-task-test'),
]
