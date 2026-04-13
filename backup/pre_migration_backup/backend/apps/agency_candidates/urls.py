from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.agency_candidates.views import (
    AgencyCandidatePipelineRegistryViewSet,
    AgencyCandidateViewSet,
    AgencyCandidateNoteViewSet,
    AgencyCandidateHotlistViewSet,
    AgencyCandidateHotlistMemberViewSet,
    AgencyCandidateResumeVersionViewSet,
    AgencyCandidateSubmissionViewSet
)

router = DefaultRouter()
router.register(r'registry', AgencyCandidatePipelineRegistryViewSet)
router.register(r'candidates', AgencyCandidateViewSet)
router.register(r'notes', AgencyCandidateNoteViewSet)
router.register(r'hotlists', AgencyCandidateHotlistViewSet)
router.register(r'hotlist-members', AgencyCandidateHotlistMemberViewSet)
router.register(r'resumes', AgencyCandidateResumeVersionViewSet)
router.register(r'submissions', AgencyCandidateSubmissionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
