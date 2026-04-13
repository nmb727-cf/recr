from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.automation_os import views

router = DefaultRouter()
router.register(r'engines', views.EngineRegistryViewSet, basename='automation-engine')
router.register(r'policies', views.ExecutionPolicyViewSet, basename='automation-policy')
router.register(r'workloads', views.WorkloadBucketViewSet, basename='automation-workload')

urlpatterns = [
    path('', include(router.urls)),
    path('runtime/', views.RuntimeStateView.as_view(), name='automation-runtime-state'),
    path('runtime/mode/<str:mode_type>/', views.RuntimeModeView.as_view(), name='automation-runtime-mode'),
    path('runtime/control/<str:action_type>/', views.GlobalControlView.as_view(), name='automation-global-control'),
    path('coverage/', views.BusinessCoverageView.as_view(), name='automation-business-coverage'),
    path('events/', views.OperatingEventListView.as_view(), name='automation-operating-events'),
    path('insights/', views.OperatingInsightListView.as_view(), name='automation-operating-insights'),
]
