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
}
