from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.automation_playbooks import views

router = DefaultRouter()
router.register(r'playbooks', views.PlaybookViewSet, basename='automation-playbook')

urlpatterns = [
    path('', include(router.urls)),
    path('recommendations/', views.PlaybookRecommendationListView.as_view(), name='automation-playbook-recommendations'),
    path('analytics/', views.PlaybookAnalyticsView.as_view(), name='automation-playbook-analytics'),
]
