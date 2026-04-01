import http from '@/utils/http'
import type { ApiResponse, Application, JobPosting } from '@/types'

export const candidateApi = {
  listApplications: () =>
    http.get<ApiResponse<{ applications: Application[] }>>('/candidate/applications/'),

  getApplication: (id: string) =>
    http.get<ApiResponse<{ application: Application; stage_history: any[] }>>(`/candidate/applications/${id}/`),

  searchJobs: (params?: Record<string, unknown>) =>
    http.get<ApiResponse<{ jobs: JobPosting[] }>>('/jobs/search/', { params }),

  applyJob: (jobId: string, notes?: string) =>
    http.post(`/jobs/${jobId}/apply/`, { cover_note: notes }),

  recommendedJobs: () =>
    http.get<ApiResponse<{ jobs: JobPosting[] }>>('/candidate/recommended-jobs/'),

  getProfile: () =>
    http.get('/candidate/profile/'),

  updateProfile: (data: Record<string, unknown>) =>
    http.put('/candidate/profile/', data),
}
