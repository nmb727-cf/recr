import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const workflowSlaApi = {
  listSla: (params?: { tenant_id?: string; workflow_instance_id?: string; status?: string }) =>
    http.get<ApiResponse<any[]>>('/workflow-sla/', { params }),

  getInstanceSla: (instanceId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-instances/${instanceId}/sla/`),

  getStageSla: (stageId: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-stages/${stageId}/sla/`),

  resolveSla: (trackerId: string) =>
    http.post<ApiResponse<any>>(`/workflow-sla/${trackerId}/resolve/`, {}),
}
