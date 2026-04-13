import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const workflowSchedulerApi = {
  listTasks: (params?: {
    tenant_id?: string
    workflow_instance_id?: string
    status?: string
    task_type?: string
  }) => http.get<ApiResponse<any[]>>('/workflow-scheduler/tasks/', { params }),

  getTask: (id: string) =>
    http.get<ApiResponse<any>>(`/workflow-scheduler/tasks/${id}/`),

  getInstanceScheduledTasks: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${instanceId}/scheduled-tasks/`),

  retryTask: (id: string) =>
    http.post<ApiResponse<any>>(`/workflow-scheduler/tasks/${id}/retry/`, {}),

  cancelTask: (id: string) =>
    http.post<ApiResponse<any>>(`/workflow-scheduler/tasks/${id}/cancel/`, {}),
}
