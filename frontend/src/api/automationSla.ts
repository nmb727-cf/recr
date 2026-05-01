import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const automationSlaApi = {
  // Policies
  listPolicies: () => http.get<ApiResponse<any[]>>('/workflow-sla/policies/'),
  createPolicy: (data: any) => http.post<ApiResponse<any>>('/workflow-sla/policies/', data),
  updatePolicy: (id: string, data: any) => http.put<ApiResponse<any>>(`/workflow-sla/policies/${id}/`, data),
  deletePolicy: (id: string) => http.delete<ApiResponse<any>>(`/workflow-sla/policies/${id}/`),

  // Executions
  listExecutions: () => http.get<ApiResponse<any[]>>('/workflow-sla/executions/'),
  completeSla: (id: string) => http.post<ApiResponse<any>>(`/workflow-sla/executions/${id}/complete/`, {}),
  cancelSla: (id: string) => http.post<ApiResponse<any>>(`/workflow-sla/executions/${id}/cancel/`, {}),

  // Reminders
  listReminders: () => http.get<ApiResponse<any[]>>('/workflow-sla/reminders/'),

  // Escalation Rules
  listEscalationRules: () => http.get<ApiResponse<any[]>>('/workflow-sla/escalation-rules/'),
  createEscalationRule: (data: any) => http.post<ApiResponse<any>>('/workflow-sla/escalation-rules/', data),
  updateEscalationRule: (id: string, data: any) => http.put<ApiResponse<any>>(`/workflow-sla/escalation-rules/${id}/`, data),

  // Analytics & Insights
  getAnalytics: () => http.get<ApiResponse<any>>('/workflow-sla/analytics/'),
  listBreachInsights: () => http.get<ApiResponse<any[]>>('/workflow-sla/breach-insights/'),
  triggerInsightGeneration: () => http.post<ApiResponse<any>>('/workflow-sla/breach-insights/', {}),
}
