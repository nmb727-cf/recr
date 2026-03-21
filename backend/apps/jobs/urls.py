from django.urls import path
from apps.jobs import views

urlpatterns = [
    # Requisitions
    path('requisitions/', views.JobRequisitionListView.as_view(), name='requisition-list'),
    path('requisitions/<uuid:pk>/', views.JobRequisitionDetailView.as_view(), name='requisition-detail'),
    path('requisitions/<uuid:pk>/submit-for-approval/', views.JobRequisitionSubmitView.as_view(), name='requisition-submit'),
    path('requisitions/<uuid:pk>/approve/', views.JobRequisitionApproveView.as_view(), name='requisition-approve'),
    path('requisitions/<uuid:pk>/reject/', views.JobRequisitionRejectView.as_view(), name='requisition-reject'),
    path('requisitions/<uuid:pk>/publish/', views.JobRequisitionPublishView.as_view(), name='requisition-publish'),
    path('requisitions/<uuid:pk>/clone/', views.JobRequisitionCloneView.as_view(), name='requisition-clone'),

    # Stages
    path('requisitions/<uuid:requisition_id>/stages/', views.JobStageListView.as_view(), name='stage-list'),
    path('requisitions/<uuid:requisition_id>/stages/<uuid:stage_id>/', views.JobStageDetailView.as_view(), name='stage-detail'),
    path('requisitions/<uuid:requisition_id>/stages/reorder/', views.JobStageReorderView.as_view(), name='stage-reorder'),

    # Postings
    path('postings/', views.JobPostingListView.as_view(), name='posting-list'),
    path('postings/<uuid:pk>/', views.JobPostingDetailView.as_view(), name='posting-detail'),
    path('postings/<uuid:pk>/pause/', views.JobPostingPauseView.as_view(), name='posting-pause'),
    path('postings/<uuid:pk>/close/', views.JobPostingCloseView.as_view(), name='posting-close'),

    # Public / Candidate-facing
    path('search/', views.JobSearchView.as_view(), name='job-search'),
    path('<uuid:pk>/', views.JobPublicDetailView.as_view(), name='job-public-detail'),
    path('<uuid:pk>/apply/', views.JobApplyView.as_view(), name='job-apply'),
    path('<uuid:pk>/save/', views.JobSaveView.as_view(), name='job-save'),
]
