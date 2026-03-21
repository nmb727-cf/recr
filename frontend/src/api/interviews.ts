import http from '@/utils/http'
import type { ApiResponse, Interview, InterviewFeedback } from '@/types'

export interface CreateInterviewPayload {
  application_id: string
  interview_type: string
  title: string
  scheduled_at: string
  duration_minutes: number
  interview_round: number
  interviewers?: string[]
}

export const interviewsApi = {
  list: (params?: Record<string, unknown>) =>
    http.get<ApiResponse<{ interviews: Interview[] }>>('/interviews/', { params }),

  get: (id: string) =>
    http.get<ApiResponse<{ interview: Interview }>>(`/interviews/${id}/`),

  create: (data: CreateInterviewPayload) =>
    http.post<ApiResponse<{ interview: Interview }>>('/interviews/', data),

  update: (id: string, data: Partial<Interview>) =>
    http.patch<ApiResponse<{ interview: Interview }>>(`/interviews/${id}/`, data),

  delete: (id: string) =>
    http.delete<ApiResponse<unknown>>(`/interviews/${id}/`),

  submitFeedback: (id: string, data: Partial<InterviewFeedback>) =>
    http.post<ApiResponse<InterviewFeedback>>(`/interviews/${id}/feedback/`, data),

  start: (id: string) =>
    http.post<ApiResponse<Interview>>(`/interviews/${id}/start/`),

  complete: (id: string) =>
    http.post<ApiResponse<Interview>>(`/interviews/${id}/complete/`),

  cancel: (id: string, reason?: string) =>
    http.post<ApiResponse<Interview>>(`/interviews/${id}/cancel/`, { reason }),
}
