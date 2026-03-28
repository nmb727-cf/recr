from django.urls import path
from apps.interviews import views

urlpatterns = [
    path('', views.CandidateInterviewListView.as_view(), name='candidate-interview-list'),
    path('<uuid:pk>/instructions/', views.CandidateInterviewInstructionsView.as_view(), name='candidate-interview-instructions'),
    path('<uuid:pk>/runtime/', views.CandidateInterviewRuntimeView.as_view(), name='candidate-interview-runtime'),
    path('<uuid:pk>/status/', views.CandidateInterviewStatusView.as_view(), name='candidate-interview-status'),
    path('<uuid:pk>/security-event/', views.CandidateInterviewSecurityEventView.as_view(), name='candidate-interview-security-event'),
    path('<uuid:pk>/start/', views.CandidateInterviewStartView.as_view(), name='candidate-interview-start'),
    path('<uuid:pk>/submit-answer/', views.CandidateSubmitAnswerView.as_view(), name='candidate-submit-answer'),
    path('<uuid:pk>/complete/', views.CandidateCompleteInterviewView.as_view(), name='candidate-interview-complete'),
]
