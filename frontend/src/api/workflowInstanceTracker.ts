import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export type WorkflowInstanceTrackerStatus =
  | 'pending'
  | 'running'
  | 'waiting'
  | 'completed'
  | 'failed'
  | 'cancelled'

export const workflowInstanceTrackerApi = {
  listInstances: (params?: {
    tenant_id?: string
    workflow_id?: string
    status?: WorkflowInstanceTrackerStatus
    entity_type?: string
    entity_id?: string
  }) =>
    http.get<ApiResponse<any[]>>('/workflow-instances/', { params }),

  getInstance: (id: string) =>
    http.get<ApiResponse<any>>(`/workflow-instances/${id}/`),

  getTimeline: (id: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${id}/timeline/`),

  getStages: (id: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${id}/stages/`),

  getWaitStates: (id: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${id}/wait-states/`),

  getFailures: (id: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${id}/failures/`),

  getActorOwnership: (id: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${id}/actor-ownership/`),

  getConditionLogs: (id: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${id}/condition-logs/`),

  getActionLogs: (id: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${id}/action-logs/`),

  getHumanTasks: (id: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${id}/human-tasks/`),

  retryInstance: (id: string, payload?: { actor_id?: string; context?: Record<string, unknown> }) =>
    http.post<ApiResponse<any>>(`/workflow-instances/${id}/retry/`, payload || {}),

  resumeWaitState: (waitStateId: string, payload?: { actor_id?: string; context?: Record<string, unknown> }) =>
    http.post<ApiResponse<any>>(`/workflow-wait/${waitStateId}/resume/`, payload || {}),
}
