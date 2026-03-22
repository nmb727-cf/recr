import http from '@/utils/http'
import type { ApiResponse, Candidate, CandidateDetail, CandidateNote, TimelineEvent } from '@/types'

export const candidatesApi = {
  list: (params?: { search?: string; source?: string; skills?: string }) =>
    http.get<ApiResponse<{ candidates: Candidate[]; total: number }>>('/candidates/', { params }),

  get: (id: string) =>
    http.get<ApiResponse<{ candidate: CandidateDetail }>>(`/candidates/${id}/`),

  profile: (id: string) =>
    http.get<ApiResponse<{ profile: CandidateDetail['profile'] }>>(`/candidates/${id}/profile/`),

  create: (data: Partial<Candidate>) =>
    http.post<ApiResponse<{ candidate: CandidateDetail }>>('/candidates/', data),

  timeline: (id: string) =>
    http.get<ApiResponse<{ events: TimelineEvent[] }>>(`/candidates/${id}/timeline/`),

  listNotes: (id: string) =>
    http.get<ApiResponse<{ notes: CandidateNote[] }>>(`/candidates/${id}/notes/`),

  addNote: (id: string, payload: { note_text: string; note_type?: string; is_private?: boolean }) =>
    http.post<ApiResponse<{ note: CandidateNote }>>(`/candidates/${id}/notes/`, payload),

  updateNote: (candidateId: string, noteId: string, payload: Partial<CandidateNote>) =>
    http.put<ApiResponse<{ note: CandidateNote }>>(`/candidates/${candidateId}/notes/${noteId}/`, payload),

  deleteNote: (candidateId: string, noteId: string) =>
    http.delete(`/candidates/${candidateId}/notes/${noteId}/`),

  crmPipeline: () =>
    http.get<ApiResponse<Record<string, unknown[]>>>('/crm/pipeline/'),

  searchSkills: (q: string) =>
    http.get(`/candidates/skills/search/?q=${encodeURIComponent(q)}`),

  searchLocations: (q: string) =>
    http.get(`/candidates/locations/search/?q=${encodeURIComponent(q)}`),

  update: (id: string, data: any) =>
    http.put(`/candidates/${id}/`, data),

  createInviteLink: (data: {
    job_id?: string
    expires_days?: number
    max_uses?: number
  }) =>
    http.post('/organisation/invite-links/', data),

  listInviteLinks: () =>
    http.get('/organisation/invite-links/'),

  getPublicForm: (token: string) =>
    http.get(`/apply/${token}/`, { headers: { 'X-Skip-Auth': '1' } }),

  submitPublicForm: (token: string, data: any) =>
    http.post(`/apply/${token}/submit/`, data, { 
      headers: { 'X-Skip-Auth': '1' } 
    }),
}
