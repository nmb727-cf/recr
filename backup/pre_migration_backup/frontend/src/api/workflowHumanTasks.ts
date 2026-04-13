import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const workflowHumanTasksApi = {
  listHumanTasks: (params?: { tenant_id?: string; workflow_instance_id?: string; status?: string; assigned_to_id?: string }) =>
    http.get<ApiResponse<any[]>>('/workflow-human-tasks/', { params }),

  getHumanTask: (id: string) =>
    http.get<ApiResponse<any>>(`/workflow-human-tasks/${id}/`),

  getInstanceHumanTasks: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${instanceId}/human-tasks/`),

  completeHumanTask: (
    id: string,
    payload?: { actor_type?: string; actor_id?: string; comments?: string; context?: Record<string, unknown> }
  ) => http.post<ApiResponse<any>>(`/workflow-human-tasks/${id}/complete/`, payload || {}),

  rejectHumanTask: (
    id: string,
    payload?: { actor_type?: string; actor_id?: string; comments?: string; context?: Record<string, unknown> }
  ) => http.post<ApiResponse<any>>(`/workflow-human-tasks/${id}/reject/`, payload || {}),

  escalateHumanTask: (id: string, payload?: { reason?: string }) =>
    http.post<ApiResponse<any>>(`/workflow-human-tasks/${id}/escalate/`, payload || {}),
}
