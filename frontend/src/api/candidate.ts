import http from '@/utils/http'
import type { ApiResponse, Application, JobPosting } from '@/types'

export const candidateApi = {
  listApplications: () =>
    http.get<ApiResponse<{ applications: Application[] }>>('/candidate/applications/'),

  getApplication: (id: string) =>
    http.get<ApiResponse<{ application: Application }>>(`/candidate/applications/${id}/`),

  searchJobs: (params?: Record<string, unknown>) =>
    http.get<ApiResponse<{ jobs: JobPosting[] }>>('/jobs/search/', { params }),

  applyJob: (jobId: string, notes?: string) =>
    http.post(`/jobs/${jobId}/apply/`, { notes }),
}
