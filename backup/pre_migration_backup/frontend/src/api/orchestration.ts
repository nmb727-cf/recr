import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const orchestrationApi = {
  listWorkflows: () =>
    http.get<ApiResponse<{ workflows: any[] }>>('/intelligence/workflows/'),
    
  listTemplates: () =>
    http.get<ApiResponse<{ templates: any[] }>>('/intelligence/workflows/templates/'),
    
  getWorkflowDetail: (id: string) =>
    http.get<ApiResponse<{ workflow: any }>>(`/intelligence/workflows/${id}/`),
}
