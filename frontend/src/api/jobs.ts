import http from '@/utils/http'
import type { ApiResponse, JobRequisition, JobPosting, JobStage } from '@/types'

// ─── Public / Candidate ───────────────────────────────────────────────────────

export const jobsPublicApi = {
  search: (params?: { q?: string; work_mode?: string; location?: string; experience?: number }) =>
    http.get<ApiResponse<{ jobs: JobPosting[] }>>('/jobs/search/', {
      params,
      headers: { 'X-Skip-Auth': 'true' }
    }),

  getPosting: (id: string) =>
    http.get<ApiResponse<{ posting: JobPosting; requisition: JobRequisition }>>(`/jobs/${id}/`, {
      headers: { 'X-Skip-Auth': 'true' }
    }),

  apply: (id: string, cover_note?: string) =>
    http.post(`/jobs/${id}/apply/`, { cover_note }),

  save: (id: string) =>
    http.post(`/jobs/${id}/save/`),
}

// ─── Admin / Recruiter ────────────────────────────────────────────────────────

export const requisitionsApi = {
  list: (params?: { status?: string; department_id?: string; search?: string }) =>
    http.get<ApiResponse<{ requisitions: JobRequisition[] }>>('/jobs/requisitions/', { params }),

  get: (id: string) =>
    http.get<ApiResponse<{ requisition: JobRequisition; stages: JobStage[] }>>(`/jobs/requisitions/${id}/`),

  create: (data: Partial<JobRequisition>) =>
    http.post<ApiResponse<{ requisition: JobRequisition }>>('/jobs/requisitions/', data),

  update: (id: string, data: Partial<JobRequisition>) =>
    http.put<ApiResponse<{ requisition: JobRequisition }>>(`/jobs/requisitions/${id}/`, data),

  delete: (id: string) =>
    http.delete(`/jobs/requisitions/${id}/`),

  submitForApproval: (id: string) =>
    http.post<ApiResponse<{ requisition: JobRequisition }>>(`/jobs/requisitions/${id}/submit-for-approval/`),

  approve: (id: string) =>
    http.post<ApiResponse<{ requisition: JobRequisition }>>(`/jobs/requisitions/${id}/approve/`),

  reject: (id: string, reason: string) =>
    http.post<ApiResponse<{ requisition: JobRequisition }>>(`/jobs/requisitions/${id}/reject/`, { reason }),

  publish: (id: string) =>
    http.post<ApiResponse<{ requisition: JobRequisition; posting: JobPosting }>>(`/jobs/requisitions/${id}/publish/`),

  clone: (id: string) =>
    http.post<ApiResponse<{ requisition: JobRequisition }>>(`/jobs/requisitions/${id}/clone/`),
}

export const postingsApi = {
  list: () =>
    http.get<ApiResponse<{ postings: JobPosting[] }>>('/jobs/postings/'),

  get: (id: string) =>
    http.get<ApiResponse<{ posting: JobPosting }>>(`/jobs/postings/${id}/`),

  update: (id: string, data: Partial<JobPosting>) =>
    http.put<ApiResponse<{ posting: JobPosting }>>(`/jobs/postings/${id}/`, data),

  pause: (id: string) =>
    http.post<ApiResponse<{ posting: JobPosting }>>(`/jobs/postings/${id}/pause/`),

  close: (id: string) =>
    http.post<ApiResponse<{ posting: JobPosting }>>(`/jobs/postings/${id}/close/`),
}

export const stagesApi = {
  list: (requisitionId: string) =>
    http.get<ApiResponse<{ stages: JobStage[] }>>(`/jobs/requisitions/${requisitionId}/stages/`),

  create: (requisitionId: string, data: Partial<JobStage>) =>
    http.post<ApiResponse<{ stage: JobStage }>>(`/jobs/requisitions/${requisitionId}/stages/`, data),

  update: (requisitionId: string, stageId: string, data: Partial<JobStage>) =>
    http.put(`/jobs/requisitions/${requisitionId}/stages/${stageId}/`, data),

  delete: (requisitionId: string, stageId: string) =>
    http.delete(`/jobs/requisitions/${requisitionId}/stages/${stageId}/`),

  reorder: (requisitionId: string, stageIds: string[]) =>
    http.post(`/jobs/requisitions/${requisitionId}/stages/reorder/`, { stage_ids: stageIds }),
}
