import http from '@/utils/http'
import type { ApiResponse, AgencyRelationship, AgencyAssignment, JobRequisition, Application } from '@/types'

export const agenciesApi = {
  listRelationships: () =>
    http.get<ApiResponse<{ relationships: AgencyRelationship[] }>>('/agencies/relationships/'),

  getRelationship: (id: string) =>
    http.get<ApiResponse<{ relationship: AgencyRelationship }>>(`/agencies/relationships/${id}/`),

  updateRelationship: (id: string, data: Partial<AgencyRelationship>) =>
    http.patch<ApiResponse<{ relationship: AgencyRelationship }>>(`/agencies/relationships/${id}/`, data),

  accept: (id: string) =>
    http.post(`/agencies/relationships/${id}/accept/`),

  suspend: (id: string) =>
    http.post(`/agencies/relationships/${id}/suspend/`),

  terminate: (id: string) =>
    http.post(`/agencies/relationships/${id}/terminate/`),

  invite: (data: { name: string; email: string; tier: string; commission: number }) =>
    http.post('/agencies/relationships/invite/', data),

  listAssignments: (params?: { agency_id?: string }) =>
    http.get<ApiResponse<{ assignments: AgencyAssignment[] }>>('/agencies/assignments/', { params }),

  performance: (params?: { agency_id?: string }) =>
    http.get<ApiResponse<{ performance: Record<string, unknown>[] }>>('/agencies/performance/', { params }),

  createAssignment: (data: {
    agency_id: string
    requisition_id: string
    max_submissions: number
    deadline: string
    notes?: string
  }) => http.post<ApiResponse<{ assignment: AgencyAssignment }>>('/agencies/assignments/', data),

  myJobs: () =>
    http.get<ApiResponse<{ jobs: { assignment: AgencyAssignment; requisition: JobRequisition }[] }>>('/agencies/my-jobs/'),

  mySubmissions: () =>
    http.get<ApiResponse<{ submissions: Application[] }>>('/agencies/my-submissions/'),

  submitCandidate: (data: { candidate_id: string; requisition_id: string; cover_note: string }) =>
    http.post<ApiResponse<Application>>('/agencies/submit-candidate/', data),
}
