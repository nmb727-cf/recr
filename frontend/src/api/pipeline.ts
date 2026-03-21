import http from '@/utils/http'
import type { ApiResponse, Application, PipelineData } from '@/types'

export const pipelineApi = {
  listApplications: (params?: { requisition_id?: string; candidate_id?: string; status?: string }) =>
    http.get<ApiResponse<{ applications: Application[]; total: number }>>('/applications/', { params }),

  getApplication: (id: string) =>
    http.get<ApiResponse<{ application: Application }>>(`/applications/${id}/`),

  createApplication: (data: { candidate_id: string; requisition_id: string; source?: string; source_detail?: string }) =>
    http.post<ApiResponse<Application>>('/applications/', data),

  moveStage: (id: string, stage_id: string) =>
    http.post<ApiResponse<{ application: Application }>>(`/applications/${id}/move-stage/`, { stage_id }),

  shortlist: (id: string) =>
    http.post<ApiResponse<{ application: Application }>>(`/applications/${id}/shortlist/`),

  reject: (id: string, reason?: string) =>
    http.post<ApiResponse<{ application: Application }>>(`/applications/${id}/reject/`, { reason }),

  withdraw: (id: string) =>
    http.post<ApiResponse<{ application: Application }>>(`/applications/${id}/withdraw/`),

  getPipeline: (requisitionId: string) =>
    http.get<ApiResponse<PipelineData>>(`/pipeline/${requisitionId}/`),

  bulkAction: (application_ids: string[], action: string, data?: Record<string, unknown>) =>
    http.post('/pipeline/bulk-action/', { application_ids, action, ...data }),
}
