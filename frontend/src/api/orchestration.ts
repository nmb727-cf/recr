import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const orchestrationApi = {
  listWorkflows: () =>
    http.get<ApiResponse<{ workflows: any[] }>>('/intelligence/workflows/'),
    
  listTemplates: () =>
    http.get<ApiResponse<{ templates: any[] }>>('/intelligence/workflows/templates/'),

  getTemplateDetail: (id: string) =>
    http.get<ApiResponse<{ template: any }>>(`/intelligence/workflows/templates/${id}/`),
    
  getWorkflowDetail: (id: string) =>
    http.get<ApiResponse<{ workflow: any }>>(`/intelligence/workflows/${id}/`),
}
