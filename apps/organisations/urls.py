from django.urls import path
from .views import (
    OrganisationProfileView,
    UserListView, UserDetailView,
    DepartmentListView, DepartmentDetailView,
    LocationListView, LocationDetailView,
    TeamListView, TeamDetailView,
)

urlpatterns = [
    path('api/v1/organisation/profile/', OrganisationProfileView.as_view(), name='organisation-profile'),
    path('api/v1/organisation/users/', UserListView.as_view(), name='user-list'),
    path('api/v1/organisation/users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('api/v1/organisation/departments/', DepartmentListView.as_view(), name='department-list'),
    path('api/v1/organisation/departments/<int:pk>/', DepartmentDetailView.as_view(), name='department-detail'),
    path('api/v1/organisation/locations/', LocationListView.as_view(), name='location-list'),
    path('api/v1/organisation/locations/<int:pk>/', LocationDetailView.as_view(), name='location-detail'),
    path('api/v1/organisation/teams/', TeamListView.as_view(), name='team-list'),
    path('api/v1/organisation/teams/<int:pk>/', TeamDetailView.as_view(), name='team-detail'),
]
