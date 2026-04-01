import http from '@/utils/http'
import type { ApiResponse, Application, PipelineData } from '@/types'

export const pipelineApi = {
  listApplications: (params?: { requisition_id?: string; candidate_id?: string; status?: string }) =>
    http.get<ApiResponse<{ applications: Application[]; total: number }>>('/pipeline/pipeline/applications/', { params }),

  getApplication: (id: string) =>
    http.get<ApiResponse<{ application: Application }>>(`/pipeline/pipeline/applications/${id}/`),

  updateApplication: (id: string, data: Partial<Application>) =>
    http.patch<ApiResponse<{ application: Application }>>(`/pipeline/pipeline/applications/${id}/`, data),

  createApplication: (data: { candidate_id: string; requisition_id: string; source?: string; source_detail?: string }) =>
    http.post<ApiResponse<Application>>('/pipeline/pipeline/applications/', data),

  moveStage: (id: string, stage_id: string, note: string) =>
    http.post<ApiResponse<{ application: Application }>>(`/pipeline/pipeline/applications/${id}/move-stage/`, { stage_id, note }),

  shortlist: (id: string, note: string) =>
    http.post<ApiResponse<{ application: Application }>>(`/pipeline/pipeline/applications/${id}/shortlist/`, { note }),

  reject: (id: string, note: string, category?: string) =>
    http.post<ApiResponse<{ application: Application }>>(`/pipeline/pipeline/applications/${id}/reject/`, { note, category }),

  withdraw: (id: string, note: string) =>
    http.post<ApiResponse<{ application: Application }>>(`/pipeline/pipeline/applications/${id}/withdraw/`, { note }),

  getPipeline: (requisitionId: string) =>
    http.get<ApiResponse<PipelineData>>(`/pipeline/pipeline/${requisitionId}/`),

  getRequisitionActivity: (requisitionId: string) =>
    http.get<ApiResponse<{ events: any[] }>>(`/pipeline/pipeline/${requisitionId}/activity/`),

  bulkAction: (application_ids: string[], action: string, data?: Record<string, unknown>) =>
    http.post('/pipeline/pipeline/bulk-action/', { application_ids, action, data: data || {} }),

  updatePlacement: (id: string, data: {
    placement_status: string;
    expected_joining_date?: string;
    joined_at?: string;
    placement_confirmed_at?: string;
    note?: string;
  }) =>
    http.post<ApiResponse<{ application: Application }>>(`/pipeline/pipeline/applications/${id}/update-placement/`, data),

  updateCommission: (id: string, data: {
    commission_applicable: boolean;
    commission_basis_type: string;
    commission_value?: number;
    expected_commission_amount?: number;
    commission_currency?: string;
    commission_status: string;
    commission_rule_source?: string;
    commission_notes?: string;
  }) =>
    http.post<ApiResponse<{ application: Application }>>(`/pipeline/pipeline/applications/${id}/update-commission/`, data),
}
