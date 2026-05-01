import http from '@/utils/http'
import type { ApiResponse, JobRequisition, JobPosting, JobStage } from '@/types'

// ─── Public / Candidate ───────────────────────────────────────────────────────

export const jobsPublicApi = {
  search: (params?: { search?: string; q?: string; work_mode?: string; job_type?: string; location?: string; status?: string; experience?: number; limit?: number; offset?: number }) =>
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
  list: (params?: { status?: string; hiring_status?: string; department_id?: string; search?: string }) =>
    http.get<ApiResponse<{ requisitions: JobRequisition[] }>>('/jobs/requisitions/', { params }),

  getGlobalHiringBrain: () =>
    http.get<ApiResponse<{ intelligence: any }>>('/jobs/requisitions/global-intelligence/'),

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

  getHiringBrain: (id: string) =>
    http.get<ApiResponse<{ intelligence: any }>>(`/jobs/requisitions/${id}/hiring-brain/`),

  getPipelineSnapshot: (id: string) =>
    http.get<ApiResponse<{ snapshot: any }>>(`/jobs/requisitions/${id}/pipeline-snapshot/`),

  listStages: (requisitionId: string) =>
    stagesApi.list(requisitionId),
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

// ─── JD Templates ────────────────────────────────────────────────────────────

export const jdTemplatesApi = {
  list: (params?: { search?: string; category?: string; job_type?: string; active_only?: string }) =>
    http.get<ApiResponse<{ templates: any[] }>>('/jobs/templates/', { params }),

  get: (id: string) =>
    http.get<ApiResponse<{ template: any }>>(`/jobs/templates/${id}/`),

  create: (data: any) =>
    http.post<ApiResponse<{ template: any }>>('/jobs/templates/', data),

  update: (id: string, data: any) =>
    http.put<ApiResponse<{ template: any }>>(`/jobs/templates/${id}/`, data),

  delete: (id: string) =>
    http.delete(`/jobs/templates/${id}/`),

  duplicate: (id: string) =>
    http.post<ApiResponse<{ template: any }>>(`/jobs/templates/${id}/duplicate/`),

  /** Apply template content to a requisition (or get raw fields if no requisition_id) */
  apply: (id: string, requisition_id?: string, overwrite = false) =>
    http.post<ApiResponse<any>>(`/jobs/templates/${id}/apply/`, {
      ...(requisition_id ? { requisition_id, overwrite } : {}),
    }),
}

// ─── Job Locations ────────────────────────────────────────────────────────────

export const jobLocationsApi = {
  list: (requisitionId: string) =>
    http.get<ApiResponse<{ locations: any[] }>>(`/jobs/requisitions/${requisitionId}/locations/`),

  add: (requisitionId: string, data: { location_id: string; location_name?: string; is_primary?: boolean }) =>
    http.post<ApiResponse<{ location: any }>>(`/jobs/requisitions/${requisitionId}/locations/`, data),

  remove: (requisitionId: string, locationId: string) =>
    http.delete(`/jobs/requisitions/${requisitionId}/locations/${locationId}/`),
}

export const jobPrequalApi = {
  getSnapshot: (jobId: string) =>
    http.get<ApiResponse<{ prequal: any }>>(`/jobs/requisitions/${jobId}/prequal-snapshot/`),

  evaluate: (jobId: string, data: { candidate_id: string; application_id?: string }) =>
    http.post<ApiResponse<{ result: any }>>(`/jobs/requisitions/${jobId}/prequal-evaluate/`, data),
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
