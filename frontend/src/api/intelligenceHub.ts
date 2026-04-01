import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const intelligenceHubApi = {
  listPrompts: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/prompts/'),

  getPrompt: (id: string) =>
    http.get<ApiResponse<Record<string, unknown>>>(`/intelligence/prompts/${id}/`),

  listProviders: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/providers/'),

  listAutomations: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/automations/'),

  getAutomation: (id: string) =>
    http.get<ApiResponse<Record<string, unknown>>>(`/intelligence/automations/${id}/`),

  listAutomationRuns: (id: string) =>
    http.get<ApiResponse<Record<string, unknown>[]>>(`/intelligence/automations/${id}/runs/`),

  listExecutionsAI: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/executions/ai/'),

  listExecutionsAutomation: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/executions/automation/'),

  getExecutionDetail: (id: string) =>
    http.get<ApiResponse<Record<string, unknown>>>(`/intelligence/executions/${id}/`),

  listSuggestions: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/suggestions/'),

  getSuggestion: (id: string) =>
    http.get<ApiResponse<Record<string, unknown>>>(`/intelligence/suggestions/${id}/`),

  listFailures: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/failures/'),

  listDeadLetter: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/dead-letter/'),

  listApprovals: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/approvals/'),

  listConnectors: () =>
    http.get<ApiResponse<Record<string, unknown>[]>>('/intelligence/connectors/'),

  getSettings: () =>
    http.get<ApiResponse<Record<string, unknown>>>('/intelligence/settings/'),

  updateSettings: (payload: Record<string, unknown>) =>
    http.put<ApiResponse<Record<string, unknown>>>('/intelligence/settings/', payload),
}
