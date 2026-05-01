from django.urls import path

from apps.workflow_execution.api.views import WorkflowOrchestratorInstanceViewSet


orchestrator_context = WorkflowOrchestratorInstanceViewSet.as_view({'get': 'context'})
orchestrator_decisions = WorkflowOrchestratorInstanceViewSet.as_view({'get': 'decisions'})
orchestrator_logs = WorkflowOrchestratorInstanceViewSet.as_view({'get': 'logs'})
orchestrator_run = WorkflowOrchestratorInstanceViewSet.as_view({'post': 'run'})
orchestrator_resume = WorkflowOrchestratorInstanceViewSet.as_view({'post': 'resume'})
orchestrator_retry = WorkflowOrchestratorInstanceViewSet.as_view({'post': 'retry'})
orchestrator_fail = WorkflowOrchestratorInstanceViewSet.as_view({'post': 'fail'})

urlpatterns = [
    path('workflow-orchestrator/instances/<uuid:pk>/context/', orchestrator_context, name='workflow-orchestrator-context'),
    path('workflow-orchestrator/instances/<uuid:pk>/decisions/', orchestrator_decisions, name='workflow-orchestrator-decisions'),
    path('workflow-orchestrator/instances/<uuid:pk>/logs/', orchestrator_logs, name='workflow-orchestrator-logs'),
    path('workflow-orchestrator/instances/<uuid:pk>/run/', orchestrator_run, name='workflow-orchestrator-run'),
    path('workflow-orchestrator/instances/<uuid:pk>/resume/', orchestrator_resume, name='workflow-orchestrator-resume'),
    path('workflow-orchestrator/instances/<uuid:pk>/retry/', orchestrator_retry, name='workflow-orchestrator-retry'),
    path('workflow-orchestrator/instances/<uuid:pk>/fail/', orchestrator_fail, name='workflow-orchestrator-fail'),
]
