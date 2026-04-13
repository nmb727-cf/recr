import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const workflowObservabilityApi = {
  getInstanceTimeline: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-observability/instances/${instanceId}/timeline/`),

  getInstanceTrace: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-observability/instances/${instanceId}/trace/`),

  getInstanceSnapshot: (instanceId: string) =>
    http.get<ApiResponse<any>>(`/workflow-observability/instances/${instanceId}/snapshot/`),

  getInstanceMetrics: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-observability/instances/${instanceId}/metrics/`),

  getInstanceHealth: (instanceId: string) =>
    http.get<ApiResponse<any>>(`/workflow-observability/instances/${instanceId}/health/`),

  getWorkflowSummary: (workflowId: string) =>
    http.get<ApiResponse<any>>(`/workflow-observability/workflows/${workflowId}/summary/`),

  getWorkflowFailures: (workflowId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-observability/workflows/${workflowId}/failures/`),

  getWorkflowSlaRisks: (workflowId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-observability/workflows/${workflowId}/sla-risks/`),
}
