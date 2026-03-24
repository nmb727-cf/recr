from django.urls import path
from apps.candidates import views
from apps.candidates.invite_views import (
    InviteLinkListView, InviteLinkDeactivateView
)
from apps.candidates.crm_views import (
    CRMPipelineView, CRMAddToPipelineView, CRMMovePipelineView,
    CRMInteractionListView, CRMRemindersView, CRMSuggestionsView
)

urlpatterns = [
    # Candidates
    path('', views.CandidateListView.as_view(), name='candidate-list'),
    path('<uuid:pk>/', views.CandidateDetailView.as_view(), name='candidate-detail'),
    path('<uuid:pk>/timeline/', views.CandidateTimelineView.as_view(), name='candidate-timeline'),

    # Duplicates
    path('duplicates/', views.CandidateDuplicatesView.as_view(), name='candidate-duplicates'),
    path('merge/', views.CandidateMergeView.as_view(), name='candidate-merge'),

    # Notes
    path('<uuid:pk>/notes/', views.CandidateNoteListView.as_view(), name='candidate-note-list'),
    path('<uuid:pk>/notes/<uuid:note_id>/', views.CandidateNoteDetailView.as_view(), name='candidate-note-detail'),

    # Invite links
    path('invite-links/', InviteLinkListView.as_view(), name='invite-link-list'),
    path('invite-links/<uuid:pk>/deactivate/', InviteLinkDeactivateView.as_view(), name='invite-link-deactivate'),

    # CRM
    path('crm/pipeline/', CRMPipelineView.as_view(), name='crm-pipeline'),
    path('crm/pipeline/add/', CRMAddToPipelineView.as_view(), name='crm-add'),
    path('crm/pipeline/<uuid:pk>/move/', CRMMovePipelineView.as_view(), name='crm-move'),
    path('crm/candidates/<uuid:candidate_id>/interactions/', CRMInteractionListView.as_view(), name='crm-interactions'),
    path('crm/reminders/', CRMRemindersView.as_view(), name='crm-reminders'),
    path('crm/suggestions/<uuid:job_id>/', CRMSuggestionsView.as_view(), name='crm-suggestions'),

    path('skills/search/', views.SkillSearchView.as_view(),
         name='skill-search'),
    path('locations/search/', views.LocationSearchView.as_view(),
         name='location-search'),

    # Engagement domain
    path('<uuid:candidate_id>/workspace/',
         views.CandidateWorkspaceView.as_view(), name='candidate-workspace'),

    path('<uuid:candidate_id>/engagements/',
         views.CandidateEngagementListView.as_view(), name='candidate-engagements'),

    path('<uuid:candidate_id>/engagements/<uuid:engagement_id>/',
         views.CandidateEngagementDetailView.as_view(), name='candidate-engagement-detail'),

    path('<uuid:candidate_id>/engagements/<uuid:engagement_id>/close/',
         views.CandidateEngagementCloseView.as_view(), name='candidate-engagement-close'),

    path('<uuid:candidate_id>/engagements/<uuid:engagement_id>/revive/',
         views.CandidateEngagementReviveView.as_view(), name='candidate-engagement-revive'),

    path('<uuid:candidate_id>/timeline-events/',
         views.CandidateEngagementTimelineView.as_view(), name='candidate-timeline-events'),

    path('active/',
         views.ActiveCandidatesView.as_view(), name='candidates-active'),
]

