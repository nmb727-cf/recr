import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const workflowNotificationsApi = {
  listNotifications: (params?: {
    tenant_id?: string
    workflow_instance_id?: string
    status?: string
    channel?: string
  }) => http.get<ApiResponse<any[]>>('/workflow-notifications/', { params }),

  getNotification: (id: string) =>
    http.get<ApiResponse<any>>(`/workflow-notifications/${id}/`),

  getInstanceNotifications: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${instanceId}/notifications/`),

  testSend: (payload: {
    workflow_instance_id: string
    stage_execution_id?: string
    trigger_type: string
    payload?: Record<string, unknown>
  }) => http.post<ApiResponse<any>>('/workflow-notifications/test-send/', payload),

  retryNotification: (id: string) =>
    http.post<ApiResponse<any>>(`/workflow-notifications/${id}/retry/`, {}),
}
