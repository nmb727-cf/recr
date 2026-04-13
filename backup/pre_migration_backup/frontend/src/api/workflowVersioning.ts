import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const workflowVersioningApi = {
  listWorkflowVersions: (params?: { workflow_id?: string; status?: string }) =>
    http.get<ApiResponse<any[]>>('/workflow-versions/', { params }),

  getWorkflowVersion: (id: string) =>
    http.get<ApiResponse<any>>(`/workflow-versions/${id}/`),

  getWorkflowDraft: (workflowId: string) =>
    http.get<ApiResponse<any>>(`/workflows/${workflowId}/draft/`),

  getWorkflowVersionsByWorkflow: (workflowId: string) =>
    http.get<ApiResponse<any[]>>(`/workflows/${workflowId}/versions/`),

  compareWorkflowVersions: (workflowId: string, fromVersionId: string, toVersionId: string) =>
    http.get<ApiResponse<any>>(`/workflows/${workflowId}/versions/compare/`, {
      params: { from: fromVersionId, to: toVersionId },
    }),

  createWorkflowDraft: (
    workflowId: string,
    payload?: { name?: string; description?: string; builder_mode?: 'guided' | 'advanced'; created_by?: string }
  ) => http.post<ApiResponse<any>>(`/workflows/${workflowId}/draft/create/`, payload || {}),

  saveWorkflowDraft: (
    workflowId: string,
    payload?: {
      draft_id?: string
      name?: string
      description?: string
      builder_mode?: 'guided' | 'advanced'
      config_snapshot?: Record<string, unknown>
      ready_for_publish?: boolean
      changed_by?: string
    }
  ) => http.post<ApiResponse<any>>(`/workflows/${workflowId}/draft/save/`, payload || {}),

  publishWorkflowDraft: (
    workflowId: string,
    payload?: { draft_id?: string; notes?: string; changed_by?: string }
  ) => http.post<ApiResponse<any>>(`/workflows/${workflowId}/draft/publish/`, payload || {}),

  rollbackWorkflowVersion: (
    workflowId: string,
    versionId: string,
    payload?: { changed_by?: string }
  ) => http.post<ApiResponse<any>>(`/workflows/${workflowId}/versions/${versionId}/rollback/`, payload || {}),

  cloneWorkflowVersion: (
    workflowId: string,
    versionId: string,
    payload?: { changed_by?: string }
  ) => http.post<ApiResponse<any>>(`/workflows/${workflowId}/versions/${versionId}/clone/`, payload || {}),

  discardWorkflowDraft: (
    workflowId: string,
    payload?: { draft_id?: string; changed_by?: string }
  ) => http.post<ApiResponse<any>>(`/workflows/${workflowId}/draft/discard/`, payload || {}),
}
