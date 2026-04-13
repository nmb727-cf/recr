import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const workflowActionsApi = {
  listActions: (params?: { workflow_id?: string; stage_id?: string; active?: boolean }) =>
    http.get<ApiResponse<any[]>>('/workflow-actions/', { params }),

  getAction: (id: string) =>
    http.get<ApiResponse<any>>(`/workflow-actions/${id}/`),

  createAction: (payload: Record<string, unknown>) =>
    http.post<ApiResponse<any>>('/workflow-actions/', payload),

  updateAction: (id: string, payload: Record<string, unknown>) =>
    http.put<ApiResponse<any>>(`/workflow-actions/${id}/`, payload),

  testRunAction: (
    id: string,
    payload: {
      workflow_instance_id: string
      stage_execution_id?: string | null
      context?: Record<string, unknown>
    }
  ) => http.post<ApiResponse<any>>(`/workflow-actions/${id}/test-run/`, payload),

  getInstanceActionLogs: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${instanceId}/action-logs/`),
}
