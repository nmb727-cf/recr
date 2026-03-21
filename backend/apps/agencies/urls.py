from django.urls import path
from apps.agencies import views

urlpatterns = [
    # Company side
    path('relationships/', views.AgencyRelationshipListView.as_view(), name='agency-relationship-list'),
    path('relationships/<uuid:pk>/', views.AgencyRelationshipDetailView.as_view(), name='agency-relationship-detail'),
    path('relationships/<uuid:pk>/invite/', views.AgencyRelationshipInviteView.as_view(), name='agency-relationship-invite'),
    path('relationships/<uuid:pk>/accept/', views.AgencyRelationshipAcceptView.as_view(), name='agency-relationship-accept'),
    path('relationships/<uuid:pk>/suspend/', views.AgencyRelationshipSuspendView.as_view(), name='agency-relationship-suspend'),
    path('assignments/', views.AgencyJobAssignmentListView.as_view(), name='agency-assignment-list'),
    path('assignments/<uuid:pk>/', views.AgencyJobAssignmentDetailView.as_view(), name='agency-assignment-detail'),
    path('performance/', views.AgencyPerformanceListView.as_view(), name='agency-performance'),

    # Agency side
    path('my-jobs/', views.AgencyMyJobsView.as_view(), name='agency-my-jobs'),
    path('submit-candidate/', views.AgencySubmitCandidateView.as_view(), name='agency-submit-candidate'),
    path('my-submissions/', views.AgencyMySubmissionsView.as_view(), name='agency-my-submissions'),
    path('my-clients/', views.AgencyMyClientsView.as_view(), name='agency-my-clients'),
]