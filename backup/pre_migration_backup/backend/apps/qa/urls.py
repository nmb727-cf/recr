from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import views

router = DefaultRouter()
router.register(r'modules', views.ModuleReadinessResultViewSet, basename='qa-modules')
router.register(r'blockers', views.ReadinessBlockerViewSet, basename='qa-blockers')
router.register(r'scenarios', views.EndToEndScenarioResultViewSet, basename='qa-scenarios')

urlpatterns = [
    path('readiness/', include(router.urls)),
]
