from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.automation_change_impact import views

router = DefaultRouter()
router.register(r'dependencies', views.WorkflowDependencyMapViewSet, basename='workflow-change-dependency')

urlpatterns = [
    path('analysis/', views.WorkflowChangeAnalysisView.as_view(), name='workflow-change-analysis'), # GET
    path('analyze/', views.WorkflowChangeAnalysisView.as_view(), name='workflow-change-analyze'), # POST
    path('deployment-plan/', views.WorkflowDeploymentPlanView.as_view(), name='workflow-change-deployment-plan'), # GET
    path('deploy/', views.WorkflowDeploymentPlanView.as_view(), name='workflow-change-deploy'), # POST
    path('rollback-preview/', views.WorkflowRollbackPreviewView.as_view(), name='workflow-change-rollback-preview'), # GET
    path('', include(router.urls)),
]
