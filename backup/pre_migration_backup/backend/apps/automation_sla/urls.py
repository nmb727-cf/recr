from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.automation_sla import views
from apps.workflow_execution.api.views import WorkflowSLAListView, WorkflowSLAResolveView

router = DefaultRouter()
router.register(r'policies', views.SLAPolicyViewSet, basename='workflow-sla-policy')
router.register(r'executions', views.SLAExecutionViewSet, basename='workflow-sla-execution')
router.register(r'escalation-rules', views.SLAEscalationRuleViewSet, basename='workflow-sla-escalation')

urlpatterns = [
    path('', WorkflowSLAListView.as_view(), name='workflow-sla-list'),
    path('<uuid:pk>/resolve/', WorkflowSLAResolveView.as_view(), name='workflow-sla-resolve'),
    path('', include(router.urls)),
    path('reminders/', views.SLAReminderListView.as_view(), name='workflow-sla-reminders'),
    path('analytics/', views.SLAAnalyticsView.as_view(), name='workflow-sla-analytics'),
    path('breach-insights/', views.SLABreachInsightListView.as_view(), name='workflow-sla-breach-insights'),
]
