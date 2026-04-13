from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.orchestration_center.api import views
from apps.orchestration_center.api import orchestration_views
from apps.analytics import views as analytics_views

router = DefaultRouter()
router.register(r'workflow-orchestration/processes', orchestration_views.WorkflowOrchestrationViewSet, basename='workflow-orchestration-processes')
router.register(r'workflow-orchestration/approvals', orchestration_views.WorkflowApprovalViewSet, basename='workflow-orchestration-approvals')
router.register(r'workflow-orchestration/scheduling', orchestration_views.WorkflowSchedulingViewSet, basename='workflow-orchestration-scheduling')
router.register(r'workflow-orchestration/negotiations', orchestration_views.WorkflowNegotiationViewSet, basename='workflow-orchestration-negotiations')
router.register(r'workflow-orchestration/handoffs', orchestration_views.WorkflowHandoffViewSet, basename='workflow-orchestration-handoffs')

urlpatterns = [
    path('', include(router.urls)),
    path('jobs/<uuid:job_id>/', analytics_views.IntelligenceJobView.as_view(), name='intelligence-substrate-job'),
    path('candidate/<uuid:candidate_id>/', analytics_views.IntelligenceCandidateView.as_view(), name='intelligence-substrate-candidate'),
    path('pipeline/', analytics_views.IntelligencePipelineView.as_view(), name='intelligence-substrate-pipeline'),
    path('recruiters/', analytics_views.IntelligenceRecruiterView.as_view(), name='intelligence-substrate-recruiters'),
    path('overview/', views.OverviewView.as_view(), name='intelligence-overview'),
    path('providers/', views.ProviderListView.as_view(), name='intelligence-provider-list'),
    path('providers/<uuid:pk>/', views.ProviderDetailView.as_view(), name='intelligence-provider-detail'),
    path('models/', views.ModelListView.as_view(), name='intelligence-model-list'),
    path('models/<uuid:pk>/', views.ModelDetailView.as_view(), name='intelligence-model-detail'),
    path('prompts/', views.PromptListCreateView.as_view(), name='intelligence-prompt-list-create'),
    path('prompts/<uuid:pk>/', views.PromptDetailView.as_view(), name='intelligence-prompt-detail'),
    path('prompts/<uuid:pk>/versions/', views.PromptVersionCreateView.as_view(), name='intelligence-prompt-version-create'),
    path('prompts/<uuid:pk>/approve/', views.PromptApproveView.as_view(), name='intelligence-prompt-approve'),
    path('prompts/<uuid:pk>/archive/', views.PromptArchiveView.as_view(), name='intelligence-prompt-archive'),
    path('prompts/<uuid:pk>/test/', views.PromptTestView.as_view(), name='intelligence-prompt-test'),
    path('automations/', views.AutomationListCreateView.as_view(), name='intelligence-automation-list-create'),
    path('automations/<uuid:pk>/', views.AutomationDetailView.as_view(), name='intelligence-automation-detail'),
    path(
        'automation-intelligence/policies/',
        views.AutomationIntelligencePolicyListCreateView.as_view(),
        name='intelligence-automation-intelligence-policy-list-create',
    ),
    path(
        'automation-intelligence/policies/<uuid:pk>/',
        views.AutomationIntelligencePolicyDetailView.as_view(),
        name='intelligence-automation-intelligence-policy-detail',
    ),
    # Automation Intelligence Library (templates).
    path(
        'automation-templates/',
        views.AutomationTemplateListCreateView.as_view(),
        name='intelligence-automation-template-list-create',
    ),
    path(
        'automation-templates/<uuid:pk>/',
        views.AutomationTemplateDetailView.as_view(),
        name='intelligence-automation-template-detail',
    ),
    path(
        'automation-templates/<uuid:pk>/apply/',
        views.AutomationTemplateApplyView.as_view(),
        name='intelligence-automation-template-apply',
    ),
    # Short-form aliases for automation-intelligence policy CRUD.
    path(
        'automation-policies/',
        views.AutomationIntelligencePolicyListCreateView.as_view(),
        name='intelligence-automation-policy-list-create',
    ),
    path(
        'automation-policies/<uuid:pk>/',
        views.AutomationIntelligencePolicyDetailView.as_view(),
        name='intelligence-automation-policy-detail',
    ),
    path('automations/<uuid:pk>/toggle/', views.AutomationToggleView.as_view(), name='intelligence-automation-toggle'),
    path('automations/<uuid:pk>/simulate/', views.AutomationSimulateView.as_view(), name='intelligence-automation-simulate'),
    path('automations/<uuid:pk>/runs/', views.AutomationRunsView.as_view(), name='intelligence-automation-runs'),
    path('executions/ai/', views.AIExecutionListView.as_view(), name='intelligence-ai-executions'),
    path('suggestions/', views.SuggestionListCreateView.as_view(), name='intelligence-suggestion-list-create'),
    path('suggestions/<uuid:pk>/', views.SuggestionDetailView.as_view(), name='intelligence-suggestion-detail'),
    path('suggestions/<uuid:pk>/review/', views.SuggestionReviewView.as_view(), name='intelligence-suggestion-review'),
    path('suggestions/<uuid:pk>/approve/', views.SuggestionApproveView.as_view(), name='intelligence-suggestion-approve'),
    path('suggestions/<uuid:pk>/reject/', views.SuggestionRejectView.as_view(), name='intelligence-suggestion-reject'),
    path('suggestions/<uuid:pk>/dismiss/', views.SuggestionDismissView.as_view(), name='intelligence-suggestion-dismiss'),
    path('suggestions/<uuid:pk>/apply/', views.SuggestionApplyView.as_view(), name='intelligence-suggestion-apply'),
    path('suggestions/<uuid:pk>/convert/', views.SuggestionConvertView.as_view(), name='intelligence-suggestion-convert'),
    path('executions/automation/', views.AutomationExecutionListView.as_view(), name='intelligence-automation-executions'),
    path('executions/<uuid:execution_id>/', views.UnifiedExecutionDetailView.as_view(), name='intelligence-execution-detail'),
    path('executions/<uuid:execution_id>/retry/', views.ExecutionRetryView.as_view(), name='intelligence-execution-retry'),
    path('executions/<uuid:execution_id>/cancel/', views.ExecutionCancelView.as_view(), name='intelligence-execution-cancel'),
    path('executions/<uuid:execution_id>/approve/', views.ExecutionApproveView.as_view(), name='intelligence-execution-approve'),
    path('executions/<uuid:execution_id>/reject/', views.ExecutionRejectView.as_view(), name='intelligence-execution-reject'),
    path('failures/', views.FailureListView.as_view(), name='intelligence-failure-list'),
    path('failures/<uuid:pk>/retry/', views.FailureRetryView.as_view(), name='intelligence-failure-retry'),
    path('failures/<uuid:pk>/resolve/', views.FailureResolveView.as_view(), name='intelligence-failure-resolve'),
    path('dead-letter/', views.DeadLetterListView.as_view(), name='intelligence-dead-letter-list'),
    path('dead-letter/<uuid:pk>/requeue/', views.DeadLetterRequeueView.as_view(), name='intelligence-dead-letter-requeue'),
    path('connectors/', views.ConnectorListView.as_view(), name='intelligence-connector-list'),
    path('settings/', views.SettingsView.as_view(), name='intelligence-settings'),
    path('approvals/', views.ApprovalListView.as_view(), name='intelligence-approval-list'),
    path('approvals/<uuid:pk>/', views.ApprovalDetailView.as_view(), name='intelligence-approval-detail'),
    path('approvals/<uuid:pk>/approve/', views.ApprovalApproveView.as_view(), name='intelligence-approval-approve'),
    path('approvals/<uuid:pk>/reject/', views.ApprovalRejectView.as_view(), name='intelligence-approval-reject'),
    path('governance/audit-logs/', views.AuditLogListView.as_view(), name='intelligence-audit-logs'),
    path('governance/decisions/', views.DecisionTrackingView.as_view(), name='intelligence-decisions'),
    path('governance/automation/', views.AutomationGovernanceView.as_view(), name='intelligence-automation-governance'),
    path('governance/ai-transparency/', views.AITransparencyView.as_view(), name='intelligence-ai-transparency'),
    path('automation-analytics/', views.AutomationAnalyticsView.as_view(), name='intelligence-automation-analytics'),
    path('policy-analytics/', views.PolicyAnalyticsView.as_view(), name='intelligence-policy-analytics'),
    path('analytics/overview/', views.AnalyticsOverviewView.as_view(), name='intelligence-analytics-overview'),
    path('analytics/suggestions/', views.AnalyticsSuggestionsView.as_view(), name='intelligence-analytics-suggestions'),
    path('analytics/policies/', views.AnalyticsPoliciesView.as_view(), name='intelligence-analytics-policies'),
    path('analytics/executions/', views.AnalyticsExecutionsView.as_view(), name='intelligence-analytics-executions'),
    path('self-learning/', include('apps.automation_learning.urls')),
    
    # Learning Engine
    path('learning/overview/', views.LearningOverviewView.as_view(), name='intelligence-learning-overview'),
    path('learning/recommendations/', views.LearningRecommendationsView.as_view(), name='intelligence-learning-recommendations'),
    path('learning/signals/', views.LearningSignalsView.as_view(), name='intelligence-learning-signals'),
    path('learning/policy-table/', views.PolicyLearningTableView.as_view(), name='intelligence-learning-policy-table'),
    
    # Governance Engine (Phase 59)
    path('governance/summary/', views.GovernanceSummaryView.as_view(), name='intelligence-governance-summary'),
    path('governance/audit/', views.GovernanceAuditListView.as_view(), name='intelligence-governance-audit-list'),
    
    # Automation Library (Phase 60)
    path('templates/', views.TemplateListView.as_view(), name='intelligence-template-list'),
    path('templates/<uuid:pk>/clone/', views.TemplateCloneView.as_view(), name='intelligence-template-clone'),
    path('templates/<uuid:pk>/activate/', views.TemplateActivateView.as_view(), name='intelligence-template-activate'),
    path('templates/tenant/', views.TenantTemplateListView.as_view(), name='intelligence-tenant-template-list'),
    
    # Optimization Engine (Phase 61)
    path('optimization/overview/', views.OptimizationOverviewView.as_view(), name='intelligence-optimization-overview'),
    path('optimization/recommendations/', views.OptimizationRecommendationListView.as_view(), name='intelligence-optimization-recommendations'),
    path('optimization/<uuid:pk>/apply/', views.OptimizationApplyView.as_view(), name='intelligence-optimization-apply'),
    
    path('health/', views.IntelligenceHealthView.as_view(), name='intelligence-health'),
    
    path('learning/policies/', views.LearningPoliciesView.as_view(), name='intelligence-learning-policies'),
    path('governance/rules/', views.GovernanceRulesView.as_view(), name='intelligence-governance-rules'),
    path('governance/approvals/', views.GovernanceApprovalsView.as_view(), name='intelligence-governance-approvals'),
    path('governance/approve/', views.GovernanceApproveView.as_view(), name='intelligence-governance-approve'),
    path('governance/reject/', views.GovernanceRejectView.as_view(), name='intelligence-governance-reject'),
    
    # Workflow Analytics
    path('workflows/analytics/overview/', views.WorkflowAnalyticsOverviewView.as_view(), name='workflow-analytics-overview'),
    path('workflows/analytics/workflows/', views.WorkflowAnalyticsListView.as_view(), name='workflow-analytics-list'),
    path('workflows/analytics/triggers/', views.WorkflowAnalyticsTriggersView.as_view(), name='workflow-analytics-triggers'),
    path('workflows/analytics/actions/', views.WorkflowAnalyticsActionsView.as_view(), name='workflow-analytics-actions'),
    path('workflows/analytics/failures/', views.WorkflowAnalyticsFailuresView.as_view(), name='workflow-analytics-failures'),
    path('workflows/analytics/impact/', views.WorkflowAnalyticsImpactView.as_view(), name='workflow-analytics-impact'),
    path('workflows/analytics/adoption/', views.WorkflowAnalyticsAdoptionView.as_view(), name='workflow-analytics-adoption'),
    path('workflows/<uuid:pk>/analytics/', views.WorkflowAnalyticsDetailView.as_view(), name='workflow-detail-analytics'),

    path('library/templates/', views.LibraryTemplateListView.as_view(), name='intelligence-library-template-list'),
    path('library/templates/<uuid:pk>/clone/', views.LibraryTemplateCloneView.as_view(), name='intelligence-library-template-clone'),
    path('library/templates/<uuid:pk>/activate/', views.LibraryTemplateActivateView.as_view(), name='intelligence-library-template-activate'),
    path('library/tenant-templates/', views.LibraryTenantTemplatesView.as_view(), name='intelligence-library-tenant-templates'),
    path('workflows/', views.WorkflowListView.as_view(), name='intelligence-workflow-list'),
    path('workflows/<uuid:pk>/', views.WorkflowDetailView.as_view(), name='intelligence-workflow-detail'),
    path('workflows/<uuid:pk>/builder/', views.WorkflowBuilderView.as_view(), name='intelligence-workflow-builder'),
    path('workflows/<uuid:pk>/builder/save/', views.WorkflowBuilderSaveView.as_view(), name='intelligence-workflow-builder-save'),
    path('workflows/<uuid:pk>/validate/', views.WorkflowValidateView.as_view(), name='intelligence-workflow-validate'),
    path('workflows/<uuid:pk>/duplicate/', views.WorkflowDuplicateView.as_view(), name='intelligence-workflow-duplicate'),
    path('workflows/<uuid:pk>/<str:action>/', views.WorkflowStatusActionView.as_view(), name='intelligence-workflow-status-action'),
    path('workflows/executions/', views.WorkflowExecutionListView.as_view(), name='intelligence-workflow-executions'),
    path('workflows/templates/', views.WorkflowTemplateListView.as_view(), name='intelligence-workflow-template-list'),
    path('workflows/templates/<uuid:pk>/enable/', views.WorkflowTemplateEnableView.as_view(), name='intelligence-workflow-template-enable'),
    # New Workflow Governance endpoints
    path('workflows/<uuid:workflow_id>/versions/', views.WorkflowVersionListView.as_view(), name='workflow-version-list'),
    path('workflows/approvals/', views.WorkflowApprovalListView.as_view(), name='workflow-approval-list'),
    path('workflows/approvals/<uuid:pk>/decide/', views.WorkflowApprovalDecideView.as_view(), name='workflow-approval-decide'),
    path('workflows/<uuid:workflow_id>/safety-rule/', views.WorkflowSafetyRuleView.as_view(), name='workflow-safety-rule'),
    path('workflows/executions/<uuid:execution_id>/rollback/', views.WorkflowRollbackView.as_view(), name='workflow-rollback'),
    path('workflows/audit-logs/', views.WorkflowAuditLogListView.as_view(), name='workflow-audit-log-list'),
    path('workflows/governance/health/', views.WorkflowGovernanceHealthView.as_view(), name='workflow-governance-health'),

    # AI Automation Intelligence
    path('automation-intelligence/insights/', views.AutomationInsightListView.as_view(), name='automation-insight-list'),
    path('automation-intelligence/insights/<uuid:pk>/accept/', views.AutomationInsightAcceptView.as_view(), name='automation-insight-accept'),
    path('automation-intelligence/insights/<uuid:pk>/dismiss/', views.AutomationInsightDismissView.as_view(), name='automation-insight-dismiss'),
    path('automation-intelligence/recommendations/', views.AutomationRecommendationListView.as_view(), name='automation-recommendation-list'),

    # Workflow Event Trigger System
    path('workflow-events/registry/', views.WorkflowEventRegistryView.as_view(), name='workflow-event-registry'),
    path('workflow-events/logs/', views.WorkflowEventLogListView.as_view(), name='workflow-event-log-list'),
    path('workflow-events/logs/<uuid:pk>/', views.WorkflowEventLogDetailView.as_view(), name='workflow-event-log-detail'),
    path('workflow-events/debug/<uuid:log_pk>/', views.WorkflowEventDebugTraceView.as_view(), name='workflow-event-debug-trace'),
    path('workflow-events/test-emit/', views.WorkflowEventTestEmitView.as_view(), name='workflow-event-test-emit'),
    path('workflow-events/subscriptions/', views.WorkflowEventSubscriptionViewSet.as_view({'get': 'list', 'post': 'create'}), name='workflow-event-subscription-list'),
    path('workflow-events/subscriptions/<uuid:pk>/', views.WorkflowEventSubscriptionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='workflow-event-subscription-detail'),
]
