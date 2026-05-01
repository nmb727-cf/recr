from django.urls import path
from apps.automation_recovery import views

urlpatterns = [
    # Recovery Cases
    path('cases/', views.RecoveryCaseListView.as_view(), name='wf-recovery-case-list'),
    path('cases/<uuid:pk>/', views.RecoveryCaseDetailView.as_view(), name='wf-recovery-case-detail'),
    path('cases/<uuid:pk>/retry/', views.RecoveryCaseRetryView.as_view(), name='wf-recovery-case-retry'),
    path('cases/<uuid:pk>/resume/', views.RecoveryCaseResumeView.as_view(), name='wf-recovery-case-resume'),
    path('cases/<uuid:pk>/fallback/', views.RecoveryCaseFallbackView.as_view(), name='wf-recovery-case-fallback'),
    path('cases/<uuid:pk>/rollback/', views.RecoveryCaseRollbackView.as_view(), name='wf-recovery-case-rollback'),
    path('cases/<uuid:pk>/resolve/', views.RecoveryCaseResolveView.as_view(), name='wf-recovery-case-resolve'),

    # Dead Letter Queue
    path('dead-letter/', views.DeadLetterListView.as_view(), name='wf-recovery-dl-list'),
    path('dead-letter/<uuid:pk>/', views.DeadLetterDetailView.as_view(), name='wf-recovery-dl-detail'),
    path('dead-letter/<uuid:pk>/retry/', views.DeadLetterRetryView.as_view(), name='wf-recovery-dl-retry'),
    path('dead-letter/<uuid:pk>/assign/', views.DeadLetterAssignView.as_view(), name='wf-recovery-dl-assign'),
    path('dead-letter/<uuid:pk>/resolve/', views.DeadLetterResolveView.as_view(), name='wf-recovery-dl-resolve'),

    # Fallback Rules
    path('fallback-rules/', views.FallbackRuleListView.as_view(), name='wf-recovery-fallback-list'),
    path('fallback-rules/<uuid:pk>/', views.FallbackRuleDetailView.as_view(), name='wf-recovery-fallback-detail'),

    # Insights & Analytics
    path('insights/', views.RecoveryInsightListView.as_view(), name='wf-recovery-insights'),
    path('analytics/', views.RecoveryAnalyticsView.as_view(), name='wf-recovery-analytics'),

    # Command Center Summary
    path('summary/', views.RecoverySummaryView.as_view(), name='wf-recovery-summary'),
]
