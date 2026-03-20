from django.urls import path
from apps.organisations import views

urlpatterns = [
    path('profile/', views.OrganisationProfileView.as_view(), name='org-profile'),
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),
    path('departments/<uuid:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
    path('locations/', views.LocationListView.as_view(), name='location-list'),
    path('locations/<uuid:pk>/', views.LocationDetailView.as_view(), name='location-detail'),
    path('teams/', views.TeamListView.as_view(), name='team-list'),
    path('teams/<uuid:pk>/', views.TeamDetailView.as_view(), name='team-detail'),
]
