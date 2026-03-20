from django.urls import path
from apps.candidates import views

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
]