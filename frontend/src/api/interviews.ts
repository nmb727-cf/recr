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

  // ─── Interview Packages ──────────────────────────────────────────────────
  listPackages: (params?: any) =>
    http.get<ApiResponse<{ packages: InterviewPackage[] }>>('/interviews/packages/', { params }),

  getPackage: (id: string) =>
    http.get<ApiResponse<{ package: InterviewPackage }>>(`/interviews/packages/${id}/`),

  createPackage: (data: Partial<InterviewPackage>) =>
    http.post<ApiResponse<{ package: InterviewPackage }>>('/interviews/packages/', data),

  updatePackage: (id: string, data: Partial<InterviewPackage>) =>
    http.put<ApiResponse<{ package: InterviewPackage }>>(`/interviews/packages/${id}/`, data),

  // ─── Job Bindings ────────────────────────────────────────────────────────
  getJobBinding: (jobId: string) =>
    http.get<ApiResponse<{ binding: InterviewPackageBinding | null }>>(`/jobs/requisitions/${jobId}/interview-binding/`),

  bindToJob: (jobId: string, packageId: string) =>
    http.post<ApiResponse<{ binding: InterviewPackageBinding }>>(`/jobs/requisitions/${jobId}/interview-binding/`, { package_id: packageId }),

  updateJobBinding: (jobId: string, data: Partial<InterviewPackageBinding>) =>
    http.put<ApiResponse<{ binding: InterviewPackageBinding }>>(`/jobs/requisitions/${jobId}/interview-binding/`, data),

  unbindFromJob: (jobId: string) =>
    http.delete<ApiResponse<unknown>>(`/jobs/requisitions/${jobId}/interview-binding/`),
}
