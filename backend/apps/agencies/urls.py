from django.urls import path
from apps.agencies import views

urlpatterns = [
    # Company side
    path('lookup/', views.TenantLookupView.as_view(), name='tenant-lookup'),
    path('available/', views.AvailableAgencyListView.as_view(), name='agency-available-list'),
    path('relationships/', views.AgencyRelationshipListView.as_view(), name='agency-relationship-list'),
    path('relationships/<uuid:pk>/', views.AgencyRelationshipDetailView.as_view(), name='agency-relationship-detail'),
    path('relationships/<uuid:pk>/invite/', views.AgencyRelationshipInviteView.as_view(), name='agency-relationship-invite'),
    path('relationships/<uuid:pk>/accept/', views.AgencyRelationshipAcceptView.as_view(), name='agency-relationship-accept'),
    path('relationships/<uuid:pk>/suspend/', views.AgencyRelationshipSuspendView.as_view(), name='agency-relationship-suspend'),
    path('relationships/<uuid:pk>/reactivate/', views.AgencyRelationshipReactivateView.as_view(), name='agency-relationship-reactivate'),
    path('company-agency/<uuid:pk>/reactivate/', views.AgencyRelationshipReactivateView.as_view(), name='company-agency-reactivate'),
    path('assignments/', views.AgencyJobAssignmentListView.as_view(), name='agency-assignment-list'),
    path('assignments/<uuid:pk>/', views.AgencyJobAssignmentDetailView.as_view(), name='agency-assignment-detail'),
    path('assignments/<uuid:pk>/assign-recruiter/', views.AgencyJobAssignRecruiterView.as_view(), name='agency-assignment-assign-recruiter'),
    path('agency-jobs/<uuid:pk>/assign-recruiter/', views.AgencyJobAssignRecruiterView.as_view(), name='agency-jobs-assign-recruiter'),
    path('agency-jobs/<uuid:pk>/submission-governance/', views.AgencyJobSubmissionGovernanceView.as_view(), name='agency-jobs-submission-governance'),
    path('intelligence/dashboard/', views.AgencyIntelligenceDashboardView.as_view(), name='agency-intelligence-dashboard'),
    path('jobs/<uuid:requisition_id>/intelligence/', views.JobAgencyIntelligenceView.as_view(), name='job-agency-intelligence'),
    path('performance/', views.AgencyPerformanceListView.as_view(), name='agency-performance'),

    # New connection system
    path('guest-portals/', views.GuestPortalCreateView.as_view(), name='guest-portal-create'),
    path('guest-portals/<uuid:pk>/resend/', views.GuestPortalResendInviteView.as_view(), name='guest-portal-resend'),
    path('email-tracking/', views.EmailTrackingCreateView.as_view(), name='email-tracking-create'),
    path('offline-clients/', views.OfflineClientCreateView.as_view(), name='offline-client-create'),

    # Agency side
    path('my-jobs/', views.AgencyMyJobsView.as_view(), name='agency-my-jobs'),
    path('submit-candidate/', views.AgencySubmitCandidateView.as_view(), name='agency-submit-candidate'),
    path('my-submissions/', views.AgencyMySubmissionsView.as_view(), name='agency-my-submissions'),
    path('my-clients/', views.AgencyMyClientsView.as_view(), name='agency-my-clients'),

    # Public portal endpoints
    path('portal/accept/<str:token>/', views.AgencyPortalAcceptView.as_view(), name='portal-accept'),
]
