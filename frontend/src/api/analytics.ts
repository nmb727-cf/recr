import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const analyticsApi = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  dashboard: () =>
    http.get<ApiResponse<any>>('/analytics/dashboard/'),

  recruitment: (params?: { start_date?: string; end_date?: string }) =>
    http.get<ApiResponse<Record<string, unknown>>>('/analytics/recruitment/', { params }),

  pipeline: () =>
    http.get<ApiResponse<Record<string, unknown>>>('/analytics/pipeline/'),

  agencies: () =>
    http.get<ApiResponse<Record<string, unknown>>>('/analytics/agencies/'),

  candidates: () =>
    http.get<ApiResponse<Record<string, unknown>>>('/analytics/candidates/'),

  interviews: () =>
    http.get<ApiResponse<Record<string, unknown>>>('/analytics/interviews/'),
}
