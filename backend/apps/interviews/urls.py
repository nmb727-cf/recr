from django.urls import path
from apps.interviews import views

urlpatterns = [
    # Templates
    path('templates/', views.InterviewTemplateListView.as_view(), name='interview-template-list'),
    path('templates/<uuid:pk>/', views.InterviewTemplateDetailView.as_view(), name='interview-template-detail'),

    # Interviews (company/recruiter side)
    path('', views.InterviewListView.as_view(), name='interview-list'),
    path('<uuid:pk>/', views.InterviewDetailView.as_view(), name='interview-detail'),
    path('<uuid:pk>/start/', views.InterviewStartView.as_view(), name='interview-start'),
    path('<uuid:pk>/complete/', views.InterviewCompleteView.as_view(), name='interview-complete'),
    path('<uuid:pk>/cancel/', views.InterviewCancelView.as_view(), name='interview-cancel'),
    path('<uuid:pk>/reschedule/', views.InterviewRescheduleView.as_view(), name='interview-reschedule'),
    path('<uuid:pk>/feedback/', views.InterviewFeedbackView.as_view(), name='interview-feedback'),
]
