from django.urls import path
from apps.prequalification import candidate_views

urlpatterns = [
    path('forms/<uuid:pk>/', candidate_views.CandidatePrequalFormDetailView.as_view(), name='candidate-prequal-form-detail'),
    path('forms/<uuid:pk>/submit/', candidate_views.CandidatePrequalSubmitView.as_view(), name='candidate-prequal-submit'),
]
