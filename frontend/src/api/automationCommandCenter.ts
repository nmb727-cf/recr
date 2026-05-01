import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export type WorkflowFilterParams = {
  search?: string
  module?: string
  status?: string
  trigger?: string
  owner?: string
  priority?: string
}

export type ActivityFilterParams = {
  limit?: number
}

export const automationCommandCenterApi = {
  // Overview cards
  getOverview: () =>
    http.get<ApiResponse<Record<string, unknown>>>('/automation-center/overview/'),

  // Active workflows table
  listWorkflows: (params?: WorkflowFilterParams) =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/automation-center/workflows/', { params }),

  // Recent automation activity feed
  getActivity: (params?: ActivityFilterParams) =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/automation-center/activity/', { params }),

  // AI insight suggestions
  getAISuggestions: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/automation-center/ai-suggestions/'),

  // Automation health indicators
  getHealth: () =>
    http.get<ApiResponse<Record<string, unknown>>>('/automation-center/health/'),

  // Running executions monitor
  getExecutions: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/automation-center/executions/'),

  // Global controls (admin only)
  pauseAll: () =>
    http.post<ApiResponse<Record<string, unknown>>>('/automation-center/pause-all/'),

  resumeAll: () =>
    http.post<ApiResponse<Record<string, unknown>>>('/automation-center/resume-all/'),

  emergencyStop: () =>
    http.post<ApiResponse<Record<string, unknown>>>('/automation-center/emergency-stop/'),
}
