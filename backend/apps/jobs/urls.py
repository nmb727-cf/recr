from django.urls import path
from apps.jobs import views
from apps.interviews import views as interview_views

urlpatterns = [
    # Requisitions
    path('requisitions/', views.JobRequisitionListView.as_view(), name='requisition-list'),
    path('requisitions/global-intelligence/', views.GlobalHiringCommandCenterView.as_view(), name='requisition-global-intelligence'),
    path('requisitions/<uuid:pk>/', views.JobRequisitionDetailView.as_view(), name='requisition-detail'),
    path('requisitions/<uuid:pk>/submit-for-approval/', views.JobRequisitionSubmitView.as_view(), name='requisition-submit'),
    path('requisitions/<uuid:pk>/approve/', views.JobRequisitionApproveView.as_view(), name='requisition-approve'),
    path('requisitions/<uuid:pk>/reject/', views.JobRequisitionRejectView.as_view(), name='requisition-reject'),
    path('requisitions/<uuid:pk>/publish/', views.JobRequisitionPublishView.as_view(), name='requisition-publish'),
    path('requisitions/<uuid:pk>/review/', views.JobRequisitionReviewView.as_view(), name='requisition-review'),
    path('requisitions/<uuid:pk>/clone/', views.JobRequisitionCloneView.as_view(), name='requisition-clone'),
    path('requisitions/<uuid:pk>/candidates/', views.JobRequisitionCandidatesView.as_view(), name='requisition-candidates'),
    path('requisitions/<uuid:pk>/hiring-brain/', views.HiringAIBrainView.as_view(), name='requisition-hiring-brain'),
    path('requisitions/<uuid:pk>/pipeline-snapshot/', views.JobPipelineSnapshotView.as_view(), name='requisition-pipeline-snapshot'),
    path('requisitions/<uuid:requisition_id>/interview-binding/', interview_views.JobInterviewBindingView.as_view(), name='requisition-interview-binding'),
    path('requisitions/<uuid:requisition_id>/interview-snapshot/', interview_views.JobInterviewSnapshotView.as_view(), name='requisition-interview-snapshot'),

    # Stages
    path('requisitions/<uuid:requisition_id>/stages/', views.JobStageListView.as_view(), name='stage-list'),
    path('requisitions/<uuid:requisition_id>/stages/<uuid:stage_id>/', views.JobStageDetailView.as_view(), name='stage-detail'),
    path('requisitions/<uuid:requisition_id>/stages/reorder/', views.JobStageReorderView.as_view(), name='stage-reorder'),

    # Postings
    path('postings/', views.JobPostingListView.as_view(), name='posting-list'),
    path('postings/<uuid:pk>/', views.JobPostingDetailView.as_view(), name='posting-detail'),
    path('postings/<uuid:pk>/pause/', views.JobPostingPauseView.as_view(), name='posting-pause'),
    path('postings/<uuid:pk>/close/', views.JobPostingCloseView.as_view(), name='posting-close'),

    # JD Templates
    path('templates/', views.JDTemplateListView.as_view(), name='jd-template-list'),
    path('templates/<uuid:pk>/', views.JDTemplateDetailView.as_view(), name='jd-template-detail'),
    path('templates/<uuid:pk>/duplicate/', views.JDTemplateDuplicateView.as_view(), name='jd-template-duplicate'),
    path('templates/<uuid:pk>/apply/', views.JDTemplateApplyView.as_view(), name='jd-template-apply'),

    # Multiple Locations per Job
    path('requisitions/<uuid:pk>/locations/', views.JobLocationListView.as_view(), name='job-location-list'),
    path('requisitions/<uuid:pk>/locations/<uuid:location_id>/', views.JobLocationDeleteView.as_view(), name='job-location-delete'),

    # Prequalification Binding
    path('requisitions/<uuid:pk>/prequal-snapshot/', views.JobPrequalSnapshotView.as_view(), name='job-prequal-snapshot'),
    path('requisitions/<uuid:pk>/prequal-evaluate/', views.JobPrequalEvaluateView.as_view(), name='job-prequal-evaluate'),

    # Public / Candidate-facing
    path('search/', views.JobSearchView.as_view(), name='job-search'),
    path('<uuid:pk>/', views.JobPublicDetailView.as_view(), name='job-public-detail'),
    path('<uuid:pk>/apply/', views.JobApplyView.as_view(), name='job-apply'),
    path('<uuid:pk>/save/', views.JobSaveView.as_view(), name='job-save'),
]
