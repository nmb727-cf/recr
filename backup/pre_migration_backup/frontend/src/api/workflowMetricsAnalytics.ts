import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const workflowMetricsAnalyticsApi = {
  listWorkflows: () =>
    http.get<ApiResponse<any[]>>('/workflow-analytics/workflows/'),

  getWorkflowSummary: (workflowId: string) =>
    http.get<ApiResponse<any>>(`/workflow-analytics/workflows/${workflowId}/summary/`),

  getWorkflowTimeline: (workflowId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-analytics/workflows/${workflowId}/timeline/`),

  getWorkflowBottlenecks: (workflowId: string) =>
    http.get<ApiResponse<any>>(`/workflow-analytics/workflows/${workflowId}/bottlenecks/`),

  getWorkflowFailures: (workflowId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-analytics/workflows/${workflowId}/failures/`),

  getWorkflowStages: (workflowId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-analytics/workflows/${workflowId}/stages/`),

  getWorkflowActions: (workflowId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-analytics/workflows/${workflowId}/actions/`),

  getWorkflowImpact: (workflowId: string) =>
    http.get<ApiResponse<any>>(`/workflow-analytics/workflows/${workflowId}/impact/`),

  getWorkflowTrends: (workflowId: string, params?: { days?: number }) =>
    http.get<ApiResponse<any>>(`/workflow-analytics/workflows/${workflowId}/trends/`, { params }),
}
