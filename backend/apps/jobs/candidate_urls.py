from django.urls import path
from apps.jobs import views
from apps.candidates.views import CandidateSelfProfileView

urlpatterns = [
    path('profile/', CandidateSelfProfileView.as_view(), name='candidate-self-profile'),
    path('applications/', views.CandidateApplicationListView.as_view(), name='candidate-application-list'),
    path('applications/<uuid:pk>/', views.CandidateApplicationDetailView.as_view(), name='candidate-application-detail'),
    path('recommended-jobs/', views.RecommendedJobsView.as_view(), name='recommended-jobs'),
]