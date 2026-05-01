from django.urls import path
from .api.views import (
    WorkspaceSummaryView,
    WorkspaceTasksView,
    WorkspaceActivityView,
    WorkspaceAlertsView,
    WorkspaceAIView
)
from .api.task_views import WorkspaceTaskActionView

urlpatterns = [
    path('summary/', WorkspaceSummaryView.as_view(), name='workspace-summary'),
    path('tasks/', WorkspaceTasksView.as_view(), name='workspace-tasks'),
    path('tasks/<str:task_id>/action/', WorkspaceTaskActionView.as_view(), name='workspace-task-action'),
    path('activity/', WorkspaceActivityView.as_view(), name='workspace-activity'),
    path('alerts/', WorkspaceAlertsView.as_view(), name='workspace-alerts'),
    path('ai/', WorkspaceAIView.as_view(), name='workspace-ai'),
]
