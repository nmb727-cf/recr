from django.urls import path
from apps.interviews import views

urlpatterns = [
    # ── Interview Types (catalog) ──────────────────────────────────────────────
    path('types/', views.InterviewTypeListView.as_view(), name='interview-type-list'),
    path('types/<uuid:pk>/', views.InterviewTypeDetailView.as_view(), name='interview-type-detail'),
    path('types/<uuid:pk>/config/', views.InterviewTypeConfigView.as_view(), name='interview-type-config'),

    # ── Templates ─────────────────────────────────────────────────────────────
    path('templates/', views.InterviewTemplateListView.as_view(), name='interview-template-list'),
    path('templates/<uuid:pk>/', views.InterviewTemplateDetailView.as_view(), name='interview-template-detail'),
    path('scorecards/templates/', views.InterviewScorecardTemplateListView.as_view(), name='interview-scorecard-template-list'),
    path('scorecards/templates/<uuid:pk>/', views.InterviewScorecardTemplateDetailView.as_view(), name='interview-scorecard-template-detail'),

    # ── Interviews (recruiter / HR side) ──────────────────────────────────────
    path('', views.InterviewListView.as_view(), name='interview-list'),
    path('<uuid:pk>/', views.InterviewDetailView.as_view(), name='interview-detail'),
    path('<uuid:pk>/start/', views.InterviewStartView.as_view(), name='interview-start'),
    path('<uuid:pk>/complete/', views.InterviewCompleteView.as_view(), name='interview-complete'),
    path('<uuid:pk>/cancel/', views.InterviewCancelView.as_view(), name='interview-cancel'),
    path('<uuid:pk>/reschedule/', views.InterviewRescheduleView.as_view(), name='interview-reschedule'),
    path('<uuid:pk>/kit/', views.InterviewKitView.as_view(), name='interview-kit'),
    path('<uuid:pk>/schedule-flex/', views.InterviewScheduleActionView.as_view(), name='interview-schedule-flex'),
    path('<uuid:pk>/cancel-flex/', views.InterviewCancelActionView.as_view(), name='interview-cancel-flex'),

    # ── Feedback (panelist inline — quick path) ────────────────────────────────
    path('<uuid:pk>/feedback/', views.InterviewFeedbackView.as_view(), name='interview-feedback'),

    # ── Structured Feedback (formal per-panelist records) ─────────────────────
    path('<uuid:pk>/structured-feedback/', views.InterviewStructuredFeedbackView.as_view(), name='interview-structured-feedback'),

    # ── Decision ──────────────────────────────────────────────────────────────
    path('<uuid:pk>/decision/', views.InterviewDecisionView.as_view(), name='interview-decision'),
    path('<uuid:pk>/decision/history/', views.InterviewDecisionHistoryView.as_view(), name='interview-decision-history'),
    path('<uuid:pk>/decision/evaluate/', views.InterviewDecisionEvaluateView.as_view(), name='interview-decision-evaluate'),
    path('<uuid:pk>/panel-decision/', views.InterviewPanelDecisionView.as_view(), name='interview-panel-decision'),
    path('<uuid:pk>/scheduling-link/', views.InterviewSchedulingLinkView.as_view(), name='interview-scheduling-link'),
    path('scheduling-link/<str:token>/', views.InterviewSchedulingLinkPublicView.as_view(), name='interview-scheduling-link-public'),

    # ── Flows ─────────────────────────────────────────────────────────────────
    path('flows/', views.InterviewFlowListView.as_view(), name='interview-flow-list'),
    path('flows/<uuid:pk>/', views.InterviewFlowDetailView.as_view(), name='interview-flow-detail'),

    # ── Scheduling Engine ─────────────────────────────────────────────────────
    path('availability/profile/', views.InterviewAvailabilityProfileView.as_view(), name='interview-availability-profile'),
    path('availability/blocks/', views.InterviewAvailabilityBlockListView.as_view(), name='interview-availability-blocks'),
    path('availability/panel-slots/', views.InterviewPanelSlotsView.as_view(), name='interview-panel-slots'),
    path('scheduling/manual/', views.InterviewManualSchedulingView.as_view(), name='interview-manual-scheduling'),
    path('calendar/connections/', views.InterviewCalendarConnectionView.as_view(), name='interview-calendar-connections'),
    path('integrations/providers/', views.InterviewIntegrationProviderListView.as_view(), name='interview-integration-provider-list'),
    path('integrations/providers/<uuid:pk>/', views.InterviewIntegrationProviderDetailView.as_view(), name='interview-integration-provider-detail'),
    path('integrations/connections/', views.InterviewTenantProviderConnectionListView.as_view(), name='interview-tenant-provider-connection-list'),
    path('integrations/connections/<uuid:pk>/', views.InterviewTenantProviderConnectionDetailView.as_view(), name='interview-tenant-provider-connection-detail'),
    path('integrations/mappings/', views.InterviewExecutionMappingListView.as_view(), name='interview-execution-mapping-list'),
    path('integrations/mappings/<uuid:pk>/', views.InterviewExecutionMappingDetailView.as_view(), name='interview-execution-mapping-detail'),

    # ── Interview Question Engine ──────────────────────────────────────
    path('questions/bank/', views.InterviewQuestionBankListView.as_view(), name='interview-question-bank-list'),
    path('questions/bank/<uuid:pk>/', views.InterviewQuestionBankDetailView.as_view(), name='interview-question-bank-detail'),
    path('questions/attachments/', views.InterviewQuestionAttachmentListView.as_view(), name='interview-question-attachment-list'),
    path('questions/attachments/<uuid:pk>/', views.InterviewQuestionAttachmentDetailView.as_view(), name='interview-question-attachment-detail'),
    path('questions/groups/', views.InterviewQuestionGroupListView.as_view(), name='interview-question-group-list'),
    path('questions/groups/<uuid:pk>/', views.InterviewQuestionGroupDetailView.as_view(), name='interview-question-group-detail'),

    # ── Interview Packages ────────────────────────────────────────────────────
    path('packages/', views.InterviewPackageListView.as_view(), name='interview-package-list'),
    path('packages/<uuid:pk>/', views.InterviewPackageDetailView.as_view(), name='interview-package-detail'),
    ]

