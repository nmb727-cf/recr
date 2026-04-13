import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const automationApi = {
  listRules: (params?: Record<string, unknown>) =>
    http.get<ApiResponse<{ rules: any[] }>>('/automation/rules/', { params }),

  getRule: (id: string) =>
    http.get<ApiResponse<{ rule: any }>>(`/automation/rules/${id}/`),

  createRule: (data: any) =>
    http.post<ApiResponse<{ rule: any }>>('/automation/rules/', data),

  updateRule: (id: string, data: any) =>
    http.put<ApiResponse<{ rule: any }>>(`/automation/rules/${id}/`, data),

  deleteRule: (id: string) =>
    http.delete<ApiResponse<unknown>>(`/automation/rules/${id}/`),

  trigger: (data: any) =>
    http.post<ApiResponse<{ result: any }>>('/automation/trigger/', data),

  listLogs: (params?: Record<string, unknown>) =>
    http.get<ApiResponse<{ logs: any[] }>>('/automation/logs/', { params }),

  getOrchestratorDashboard: () =>
    http.get<ApiResponse<{ orchestrator: any }>>('/automation/orchestrator/'),

  getAutonomousEngine: () =>
    http.get<ApiResponse<{ autonomous: any }>>('/automation/autonomous-engine/'),

  updateAutonomousAction: (id: string, data: { action: 'approve' | 'reject', item_type: 'suggestion' | 'approval' }) =>
    http.post<ApiResponse<any>>(`/automation/autonomous-engine/actions/${id}/`, data),
}

