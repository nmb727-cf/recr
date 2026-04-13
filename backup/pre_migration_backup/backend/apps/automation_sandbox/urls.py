from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.automation_sandbox import views

router = DefaultRouter()
router.register(r'runs', views.SandboxRunViewSet, basename='workflow-sandbox-run')
router.register(r'scenarios', views.SandboxScenarioViewSet, basename='workflow-sandbox-scenario')
router.register(r'approvals', views.SandboxApprovalViewSet, basename='workflow-sandbox-approval')

urlpatterns = [
    path('', include(router.urls)),
    path('simulate/', views.SandboxSimulationView.as_view(), name='workflow-sandbox-simulate'),
]
