from django.urls import path
from apps.integrations import views

urlpatterns = [
    path('', views.IntegrationListView.as_view(), name='integration-list'),
    path('<uuid:pk>/', views.IntegrationDetailView.as_view(), name='integration-detail'),
]
