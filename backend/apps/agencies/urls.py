from django.urls import path
from apps.agencies import views

urlpatterns = [
    # Relationships
    path('relationships/', views.AgencyRelationshipListView.as_view(), name='agency-relationship-list'),
    path('relationships/<uuid:pk>/', views.AgencyRelationshipDetailView.as_view(), name='agency-relationship-detail'),
    path('relationships/<uuid:pk>/invite/', views.AgencyRelationshipInviteView.as_view(), name='agency-relationship-invite'),
    path('relationships/<uuid:pk>/accept/', views.AgencyRelationshipAcceptView.as_view(), name='agency-relationship-accept'),
    path('relationships/<uuid:pk>/suspend/', views.AgencyRelationshipSuspendView.as_view(), name='agency-relationship-suspend'),

    # Job assignments
    path('assignments/', views.AgencyJobAssignmentListView.as_view(), name='agency-assignment-list'),
    path('assignments/<uuid:pk>/', views.AgencyJobAssignmentDetailView.as_view(), name='agency-assignment-detail'),

    # Performance
    path('performance/', views.AgencyPerformanceListView.as_view(), name='agency-performance'),
]