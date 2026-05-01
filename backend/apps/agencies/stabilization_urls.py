from django.urls import path
from apps.agencies import views

urlpatterns = [
    path('company-agency/<uuid:pk>/reactivate/', views.AgencyRelationshipReactivateView.as_view(), name='api-company-agency-reactivate'),
    path('agency-jobs/<uuid:pk>/assign-recruiter/', views.AgencyJobAssignRecruiterView.as_view(), name='api-agency-jobs-assign-recruiter'),
    path('agency-jobs/<uuid:pk>/submission-governance/', views.AgencyJobSubmissionGovernanceView.as_view(), name='api-agency-jobs-submission-governance'),
]
