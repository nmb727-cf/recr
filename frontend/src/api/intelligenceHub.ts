import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export type SuggestionListParams = {
  category?: string
  status?: string
  source_module?: string
  confidence_band?: string
}

export type AutomationListParams = {
  status?: string
  module_scope?: string
  trigger_event?: string
  tenant_scope?: 'tenant' | 'platform'
  built_in_kind?: 'builtin' | 'custom'
}

export const intelligenceHubApi = {
  listPrompts: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/prompts/'),

  getPrompt: (id: string) =>
    http.get<ApiResponse<Record<string, unknown>>>(`/intelligence/prompts/${id}/`),

  approvePrompt: (id: string) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/prompts/${id}/approve/`),

  archivePrompt: (id: string) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/prompts/${id}/archive/`),

  listProviders: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/providers/'),

  listAutomations: (_params?: AutomationListParams) =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/automations/'),

  getAutomation: (id: string) =>
    http.get<ApiResponse<Record<string, unknown>>>(`/intelligence/automations/${id}/`),

  toggleAutomation: (id: string) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/automations/${id}/toggle/`),

  listAutomationRuns: (id: string) =>
    http.get<ApiResponse<Record<string, unknown>[]>>(`/intelligence/automations/${id}/runs/`),

  listExecutionsAI: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/executions/ai/'),

  listExecutionsAutomation: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/executions/automation/'),

  getExecutionDetail: (id: string) =>
    http.get<ApiResponse<Record<string, unknown>>>(`/intelligence/executions/${id}/`),

  retryExecution: (id: string) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/executions/${id}/retry/`),

  cancelExecution: (id: string) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/executions/${id}/cancel/`),

  listSuggestions: (params?: SuggestionListParams) =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/suggestions/', { params }),

  getSuggestion: (id: string) =>
    http.get<ApiResponse<Record<string, unknown>>>(`/intelligence/suggestions/${id}/`),

  approveSuggestion: (id: string, payload?: Record<string, unknown>) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/suggestions/${id}/approve/`, payload || {}),

  rejectSuggestion: (id: string, payload?: Record<string, unknown>) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/suggestions/${id}/reject/`, payload || {}),

  dismissSuggestion: (id: string, payload?: Record<string, unknown>) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/suggestions/${id}/dismiss/`, payload || {}),

  applySuggestion: (id: string, payload?: Record<string, unknown>) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/suggestions/${id}/apply/`, payload || {}),

  listFailures: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/failures/'),

  retryFailure: (id: string) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/failures/${id}/retry/`),

  listDeadLetter: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/dead-letter/'),

  listApprovals: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/approvals/'),

  approveApproval: (id: string, payload?: Record<string, unknown>) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/approvals/${id}/approve/`, payload || {}),

  rejectApproval: (id: string, payload?: Record<string, unknown>) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/approvals/${id}/reject/`, payload || {}),

  listConnectors: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/connectors/'),

  getSettings: () =>
    http.get<ApiResponse<Record<string, unknown>>>('/intelligence/settings/'),

  updateSettings: (payload: Record<string, unknown>) =>
    http.put<ApiResponse<Record<string, unknown>>>('/intelligence/settings/', payload),

  listAutomationIntelligencePolicies: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/automation-intelligence/policies/'),

  createAutomationIntelligencePolicy: (payload: Record<string, unknown>) =>
    http.post<ApiResponse<Record<string, unknown>>>('/intelligence/automation-intelligence/policies/', payload),

  updateAutomationIntelligencePolicy: (id: string, payload: Record<string, unknown>) =>
    http.put<ApiResponse<Record<string, unknown>>>(`/intelligence/automation-intelligence/policies/${id}/`, payload),

  deleteAutomationIntelligencePolicy: (id: string) =>
    http.delete<ApiResponse<Record<string, unknown>>>(`/intelligence/automation-intelligence/policies/${id}/`),

  // Automation Intelligence Library (templates).
  listAutomationTemplates: (params?: { suggestion_type?: string; automation_level?: string }) =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/automation-templates/', { params }),

  createAutomationTemplate: (payload: Record<string, unknown>) =>
    http.post<ApiResponse<Record<string, unknown>>>('/intelligence/automation-templates/', payload),

  updateAutomationTemplate: (id: string, payload: Record<string, unknown>) =>
    http.put<ApiResponse<Record<string, unknown>>>(`/intelligence/automation-templates/${id}/`, payload),

  deleteAutomationTemplate: (id: string) =>
    http.delete<ApiResponse<Record<string, unknown>>>(`/intelligence/automation-templates/${id}/`),

  applyAutomationTemplate: (id: string) =>
    http.post<ApiResponse<Record<string, unknown>>>(`/intelligence/automation-templates/${id}/apply/`),

  // Short-form aliases at /automation-policies/ — same views, shorter URL.
  listAutomationPolicies: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/automation-policies/'),

  createAutomationPolicy: (payload: Record<string, unknown>) =>
    http.post<ApiResponse<Record<string, unknown>>>('/intelligence/automation-policies/', payload),

  updateAutomationPolicy: (id: string, payload: Record<string, unknown>) =>
    http.put<ApiResponse<Record<string, unknown>>>(`/intelligence/automation-policies/${id}/`, payload),

  deleteAutomationPolicy: (id: string) =>
    http.delete<ApiResponse<Record<string, unknown>>>(`/intelligence/automation-policies/${id}/`),

  listAuditLogs: (params?: Record<string, unknown>) =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/governance/audit-logs/', { params }),

  getDecisionsHistory: () =>
    http.get<ApiResponse<Record<string, unknown>>>('/intelligence/governance/decisions/'),

  getAutomationGovernance: () =>
    http.get<ApiResponse<Record<string, unknown>>>('/intelligence/governance/automation/'),

  getAITransparency: () =>
    http.get<ApiResponse<Record<string, unknown>>>('/intelligence/governance/ai-transparency/'),

  getAutomationAnalytics: (params?: { days: number }) =>
    http.get<ApiResponse<any>>('/intelligence/automation-analytics/', { params }),

  getPolicyAnalytics: () =>
    http.get<ApiResponse<any>>('/intelligence/policy-analytics/'),

  getAnalyticsOverview: (params?: { days?: number }) =>
    http.get<ApiResponse<any>>('/intelligence/analytics/overview/', { params }),

  getAnalyticsSuggestions: (params?: { days?: number }) =>
    http.get<ApiResponse<any>>('/intelligence/analytics/suggestions/', { params }),

  getAnalyticsPolicies: () =>
    http.get<ApiResponse<any>>('/intelligence/analytics/policies/'),

  getAnalyticsExecutions: (params?: { days?: number }) =>
    http.get<ApiResponse<any>>('/intelligence/analytics/executions/', { params }),

  listLearningSignals: () =>
    http.get<ApiResponse<any[]>>('/intelligence/learning/signals/'),

  listLearningPolicies: () =>
    http.get<ApiResponse<any[]>>('/intelligence/learning/policies/'),

  getLearningRecommendations: () =>
    http.get<ApiResponse<any[]>>('/intelligence/learning/recommendations/'),

  getLearningOverview: () =>
    http.get<ApiResponse<any>>('/intelligence/learning/overview/'),

  getPolicyLearningTable: () =>
    http.get<ApiResponse<any[]>>('/intelligence/learning/policy-table/'),

  // AI Governance
  getGovernanceSummary: () =>
    http.get<ApiResponse<any>>('/intelligence/governance/summary/'),

  updateGovernanceSummary: (payload: any) =>
    http.post<ApiResponse<any>>('/intelligence/governance/summary/', payload),

  getGovernanceAudit: () =>
    http.get<ApiResponse<any[]>>('/intelligence/governance/audit/'),

  // Optimization Engine (Phase 61)
  getOptimizationOverview: () =>
    http.get<ApiResponse<any>>('/intelligence/optimization/overview/'),

  listOptimizationRecommendations: () =>
    http.get<ApiResponse<any[]>>('/intelligence/optimization/recommendations/'),

  applyOptimizationRecommendation: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/optimization/${id}/apply/`, {}),

  listGovernanceRules: () =>
    http.get<ApiResponse<any[]>>('/intelligence/governance/rules/'),

  createGovernanceRule: (payload: Record<string, unknown>) =>
    http.post<ApiResponse<any>>('/intelligence/governance/rules/', payload),

  listGovernanceApprovals: (params?: { status?: string }) =>
    http.get<ApiResponse<any[]>>('/intelligence/governance/approvals/', { params }),

  approveGovernanceRequest: (approvalId: string, reason?: string) =>
    http.post<ApiResponse<any>>('/intelligence/governance/approve/', { approval_id: approvalId, reason }),

  rejectGovernanceRequest: (approvalId: string, reason?: string) =>
    http.post<ApiResponse<any>>('/intelligence/governance/reject/', { approval_id: approvalId, reason }),

  // Automation Library
  listLibraryTemplates: (params?: { category?: string }) =>
    http.get<ApiResponse<any[]>>('/intelligence/library/templates/', { params }),

  cloneLibraryTemplate: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/library/templates/${id}/clone/`, {}),

  activateLibraryTemplate: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/library/templates/${id}/activate/`, {}),

  listTenantLibraryTemplates: () =>
    http.get<ApiResponse<any[]>>('/intelligence/library/tenant-templates/'),

  // Legacy compatibility for existing callers.
  listTenantTemplates: () =>
    http.get<ApiResponse<any[]>>('/intelligence/library/tenant-templates/'),

  // Workflows
  listWorkflows: () =>
    http.get<ApiResponse<any[]>>('/intelligence/workflows/'),

  createWorkflow: (payload: any) =>
    http.post<ApiResponse<any>>('/intelligence/workflows/', payload),

  getWorkflow: (id: string) =>
    http.get<ApiResponse<any>>(`/intelligence/workflows/${id}/`),

  updateWorkflow: (id: string, payload: any) =>
    http.put<ApiResponse<any>>(`/intelligence/workflows/${id}/`, payload),

  getWorkflowBuilder: (id: string) =>
    http.get<ApiResponse<any>>(`/intelligence/workflows/${id}/builder/`),

  saveWorkflowBuilder: (id: string, payload: { nodes: any[]; edges: any[]; metadata: any }) =>
    http.post<ApiResponse<any>>(`/intelligence/workflows/${id}/builder/save/`, payload),

  validateWorkflow: (id: string) =>
    http.post<ApiResponse<{ valid: boolean; errors: string[] }>>(`/intelligence/workflows/${id}/validate/`, {}),

  duplicateWorkflow: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/workflows/${id}/duplicate/`, {}),

  activateWorkflow: (id: string) =>
    http.post<ApiResponse<null>>(`/intelligence/workflows/${id}/activate/`, {}),

  pauseWorkflow: (id: string) =>
    http.post<ApiResponse<null>>(`/intelligence/workflows/${id}/pause/`, {}),

  archiveWorkflow: (id: string) =>
    http.post<ApiResponse<null>>(`/intelligence/workflows/${id}/archive/`, {}),

  listWorkflowExecutions: (params?: { workflow_id?: string }) =>
    http.get<ApiResponse<any[]>>('/intelligence/workflows/executions/', { params }),

  listWorkflowTemplates: () =>
    http.get<ApiResponse<any[]>>('/intelligence/workflows/templates/'),

  enableWorkflowTemplate: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/workflows/templates/${id}/enable/`, {}),

  // Workflow Governance
  listWorkflowVersions: (workflowId: string) =>
    http.get<ApiResponse<any[]>>(`/intelligence/workflows/${workflowId}/versions/`),

  createWorkflowVersion: (workflowId: string, payload: any) =>
    http.post<ApiResponse<any>>(`/intelligence/workflows/${workflowId}/versions/`, payload),

  listWorkflowApprovals: (params?: { status?: string }) =>
    http.get<ApiResponse<any[]>>('/intelligence/workflows/approvals/', { params }),

  decideWorkflowApproval: (id: string, payload: { status: string; comment?: string }) =>
    http.post<ApiResponse<any>>(`/intelligence/workflows/approvals/${id}/decide/`, payload),

  getWorkflowSafetyRule: (workflowId: string) =>
    http.get<ApiResponse<any>>(`/intelligence/workflows/${workflowId}/safety-rule/`),

  updateWorkflowSafetyRule: (workflowId: string, payload: any) =>
    http.put<ApiResponse<any>>(`/intelligence/workflows/${workflowId}/safety-rule/`, payload),

  rollbackWorkflowExecution: (executionId: string) =>
    http.post<ApiResponse<any>>(`/intelligence/workflows/executions/${executionId}/rollback/`, {}),

  listWorkflowAuditLogs: (params?: { workflow_id?: string }) =>
    http.get<ApiResponse<any[]>>('/intelligence/workflows/audit-logs/', { params }),

  getWorkflowHealth: () =>
    http.get<ApiResponse<any>>('/intelligence/workflows/governance/health/'),

  // Workflow Analytics (Phase 14)
  getWorkflowAnalyticsOverview: (params?: { days?: number; date_from?: string; date_to?: string }) =>
    http.get<ApiResponse<any>>('/intelligence/workflows/analytics/overview/', { params }),

  listWorkflowAnalytics: () =>
    http.get<ApiResponse<any[]>>('/intelligence/workflows/analytics/workflows/'),

  getWorkflowAnalyticsTriggers: () =>
    http.get<ApiResponse<any[]>>('/intelligence/workflows/analytics/triggers/'),

  getWorkflowAnalyticsActions: () =>
    http.get<ApiResponse<any[]>>('/intelligence/workflows/analytics/actions/'),

  getWorkflowAnalyticsFailures: () =>
    http.get<ApiResponse<any[]>>('/intelligence/workflows/analytics/failures/'),

  getWorkflowAnalyticsImpact: () =>
    http.get<ApiResponse<any[]>>('/intelligence/workflows/analytics/impact/'),

  getWorkflowAnalyticsAdoption: () =>
    http.get<ApiResponse<any[]>>('/intelligence/workflows/analytics/adoption/'),

  getWorkflowDetailAnalytics: (id: string) =>
    http.get<ApiResponse<any>>(`/intelligence/workflows/${id}/analytics/`),

  // AI Automation Intelligence
  listAutomationInsights: (params?: { status?: string }) =>
    http.get<ApiResponse<any[]>>('/intelligence/automation-intelligence/insights/', { params }),

  acceptAutomationInsight: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/automation-intelligence/insights/${id}/accept/`, {}),

  dismissAutomationInsight: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/automation-intelligence/insights/${id}/dismiss/`, {}),

  listAutomationRecommendations: () =>
    http.get<ApiResponse<any[]>>('/intelligence/automation-intelligence/recommendations/'),

  // Workflow Event Trigger System
  listWorkflowEventRegistry: () =>
    http.get<ApiResponse<any[]>>('/intelligence/workflow-events/registry/'),
  
  listWorkflowEventSubscriptions: () =>
    http.get<ApiResponse<any[]>>('/intelligence/workflow-events/subscriptions/'),
  
  listWorkflowEventLogs: () =>
    http.get<ApiResponse<any[]>>('/intelligence/workflow-events/logs/'),
  
  getWorkflowEventLogDetail: (id: string) =>
    http.get<ApiResponse<any>>(`/intelligence/workflow-events/logs/${id}/`),
  
  getWorkflowEventDebugTraces: (logId: string) =>
    http.get<ApiResponse<any[]>>(`/intelligence/workflow-events/debug/${logId}/`),
  
  testEmitWorkflowEvent: (payload: any) =>
    http.post<ApiResponse<any>>('/intelligence/workflow-events/test-emit/', payload),

  // Workflow Orchestration Engine
  listOrchestrationProcesses: (params?: { tenant_id?: string }) =>
    http.get<ApiResponse<any[]>>('/intelligence/workflow-orchestration/processes/', { params }),

  getOrchestrationProcess: (id: string) =>
    http.get<ApiResponse<any>>(`/intelligence/workflow-orchestration/processes/${id}/`),

  getOrchestrationTimeline: (id: string) =>
    http.get<ApiResponse<any>>(`/intelligence/workflow-orchestration/processes/${id}/timeline/`),

  startOrchestrationProcess: (payload: { tenant_id: string; workflow_id: string; entity_type: string; entity_id: string }) =>
    http.post<ApiResponse<any>>('/intelligence/workflow-orchestration/processes/start/', payload),

  advanceOrchestrationProcess: (id: string, payload: { next_stage_key: string; next_stage_type: string; metadata?: any }) =>
    http.post<ApiResponse<any>>(`/intelligence/workflow-orchestration/processes/${id}/advance/`, payload),

  cancelOrchestrationProcess: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/workflow-orchestration/processes/${id}/cancel/`, {}),

  listOrchestrationApprovals: (params?: { tenant_id?: string }) =>
    http.get<ApiResponse<any[]>>('/intelligence/workflow-orchestration/approvals/', { params }),

  approveOrchestrationRequest: (id: string, payload?: { notes?: string }) =>
    http.post<ApiResponse<any>>(`/intelligence/workflow-orchestration/approvals/${id}/approve/`, payload || {}),

  rejectOrchestrationRequest: (id: string, payload?: { notes?: string }) =>
    http.post<ApiResponse<any>>(`/intelligence/workflow-orchestration/approvals/${id}/reject/`, payload || {}),

  listOrchestrationScheduling: (params?: { tenant_id?: string }) =>
    http.get<ApiResponse<any[]>>('/intelligence/workflow-orchestration/scheduling/', { params }),

  checkOrchestrationAvailability: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/workflow-orchestration/scheduling/${id}/check-availability/`, {}),

  bookOrchestrationSlot: (id: string, payload: { slot_data: any }) =>
    http.post<ApiResponse<any>>(`/intelligence/workflow-orchestration/scheduling/${id}/book/`, payload),

  rescheduleOrchestration: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/workflow-orchestration/scheduling/${id}/reschedule/`, {}),

  listOrchestrationNegotiations: (params?: { tenant_id?: string }) =>
    http.get<ApiResponse<any[]>>('/intelligence/workflow-orchestration/negotiations/', { params }),

  counterOrchestrationNegotiation: (id: string, payload: { amount: number }) =>
    http.post<ApiResponse<any>>(`/intelligence/workflow-orchestration/negotiations/${id}/counter/`, payload),

  acceptOrchestrationNegotiation: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/workflow-orchestration/negotiations/${id}/accept/`, {}),

  rejectOrchestrationNegotiation: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/workflow-orchestration/negotiations/${id}/reject/`, {}),

  listOrchestrationHandoffs: (params?: { tenant_id?: string }) =>
    http.get<ApiResponse<any[]>>('/intelligence/workflow-orchestration/handoffs/', { params }),

  sendOrchestrationHandoff: (id: string) =>
    http.post<ApiResponse<any>>(`/intelligence/workflow-orchestration/handoffs/${id}/send/`, {}),
}
