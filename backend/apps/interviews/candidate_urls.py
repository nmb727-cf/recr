from django.urls import path
from apps.interviews import views

urlpatterns = [
    path('', views.CandidateInterviewListView.as_view(), name='candidate-interview-list'),
    path('<uuid:pk>/start/', views.CandidateInterviewStartView.as_view(), name='candidate-interview-start'),
    path('<uuid:pk>/submit-answer/', views.CandidateSubmitAnswerView.as_view(), name='candidate-submit-answer'),
    path('<uuid:pk>/complete/', views.CandidateCompleteInterviewView.as_view(), name='candidate-interview-complete'),
]