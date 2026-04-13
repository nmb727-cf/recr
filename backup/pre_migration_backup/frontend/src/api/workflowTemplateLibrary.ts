import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const workflowTemplateLibraryApi = {
  listTemplates: (params?: {
    category?: string
    template_type?: 'system' | 'company' | 'agency' | 'custom'
    visibility?: 'private' | 'organization' | 'public'
    is_active?: boolean
  }) => http.get<ApiResponse<any[]>>('/workflow-templates/', { params }),

  getTemplate: (id: string) =>
    http.get<ApiResponse<any>>(`/workflow-templates/${id}/`),

  getTemplateVersions: (id: string) =>
    http.get<ApiResponse<any[]>>(`/workflow-templates/${id}/versions/`),

  createTemplate: (payload: {
    name: string
    description?: string
    category?: string
    template_type?: 'system' | 'company' | 'agency' | 'custom'
    visibility?: 'private' | 'organization' | 'public'
    tenant_id?: string
    created_by?: string
    config_snapshot?: Record<string, unknown>
    metadata?: Record<string, unknown>
  }) => http.post<ApiResponse<any>>('/workflow-templates/', payload),

  cloneTemplate: (id: string, payload?: { tenant_id?: string; created_by?: string; name?: string }) =>
    http.post<ApiResponse<any>>(`/workflow-templates/${id}/clone/`, payload || {}),

  applyTemplate: (
    id: string,
    payload: {
      tenant_id: string
      workflow_name?: string
      workflow_description?: string
      trigger_event?: string
      used_by?: string
    }
  ) => http.post<ApiResponse<any>>(`/workflow-templates/${id}/apply/`, payload),

  publishTemplate: (id: string, payload?: { visibility?: 'private' | 'organization' | 'public' }) =>
    http.post<ApiResponse<any>>(`/workflow-templates/${id}/publish/`, payload || {}),

  archiveTemplate: (id: string) =>
    http.post<ApiResponse<any>>(`/workflow-templates/${id}/archive/`, {}),

  importTemplate: (payload: {
    tenant_id?: string
    created_by?: string
    payload: Record<string, unknown>
  }) => http.post<ApiResponse<any>>('/workflow-templates/import/', payload),

  exportTemplate: (id: string) =>
    http.get<ApiResponse<any>>(`/workflow-templates/${id}/export/`),

  rateTemplate: (id: string, payload: { rating: number; review?: string; tenant_id?: string; created_by?: string }) =>
    http.post<ApiResponse<any>>(`/workflow-templates/${id}/rate/`, payload),
}
