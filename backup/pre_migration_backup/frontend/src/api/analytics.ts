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

  interviewIntelligence: (params?: { start_date?: string; end_date?: string; interview_type?: string; interviewer_id?: string }) =>
    http.get<ApiResponse<Record<string, unknown>>>('/analytics/interviews/intelligence/', { params }),

  hiringIntelligence: () =>
    http.get<ApiResponse<any>>('/analytics/hiring-intelligence/'),

  getAIBrainIntelligence: () =>
    http.get<ApiResponse<any>>('/analytics/hiring-ai-brain/'),

  getUnifiedOperations: () =>
    http.get<ApiResponse<any>>('/analytics/unified-operations/'),

  getExecutiveDecisionCenter: () =>
    http.get<ApiResponse<any>>('/analytics/executive-decision/'),

  getControlTower: (params?: any) =>
    http.get<ApiResponse<any>>('/analytics/control-tower/', { params }),

  getIntelligenceMemory: (params?: any) =>
    http.get<ApiResponse<any>>('/analytics/intelligence-memory/', { params }),

  recruiterIntelligence: () =>
    http.get<ApiResponse<any>>('/analytics/recruiter-intelligence/'),
}
