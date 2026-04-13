import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const workflowVisualBuilderApi = {
  getWorkflowBuilderGraph: (workflowId: string) =>
    http.get<ApiResponse<any>>(`/workflow-builder/${workflowId}/`),

  createBuilderNode: (payload: {
    workflow_id: string
    node_type: 'start' | 'stage' | 'decision' | 'action' | 'human_task' | 'approval' | 'delay' | 'end'
    node_name: string
    position_x?: number
    position_y?: number
    config?: Record<string, unknown>
    tenant_id?: string
    created_by?: string
  }) => http.post<ApiResponse<any>>('/workflow-builder/node/', payload),

  updateBuilderNode: (id: string, payload: {
    node_name?: string
    position_x?: number
    position_y?: number
    config?: Record<string, unknown>
    is_active?: boolean
  }) => http.put<ApiResponse<any>>(`/workflow-builder/node/${id}/`, payload),

  deleteBuilderNode: (id: string) =>
    http.delete<ApiResponse<any>>(`/workflow-builder/node/${id}/`),

  createBuilderConnection: (payload: {
    workflow_id: string
    source_node_id: string
    target_node_id: string
    condition_label?: string
    connection_type?: 'default' | 'success' | 'failure' | 'conditional' | 'approval' | 'rejection'
    metadata?: Record<string, unknown>
    tenant_id?: string
    created_by?: string
  }) => http.post<ApiResponse<any>>('/workflow-builder/connection/', payload),

  deleteBuilderConnection: (id: string) =>
    http.delete<ApiResponse<any>>(`/workflow-builder/connection/${id}/`),

  validateBuilderGraph: (workflowId: string) =>
    http.post<ApiResponse<{ valid: boolean; errors: string[]; warnings?: string[] }>>('/workflow-builder/validate/', { workflow_id: workflowId }),

  saveBuilderGraph: (payload: {
    workflow_id: string
    payload?: Record<string, unknown>
    tenant_id?: string
    created_by?: string
    auto_layout?: boolean
  }) => http.post<ApiResponse<any>>('/workflow-builder/save/', payload),
}
