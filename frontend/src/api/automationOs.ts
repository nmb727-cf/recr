import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const automationOsApi = {
  // Runtime State
  getRuntimeState: () => http.get<ApiResponse<any>>('/automation-os/runtime/'),
  recalculateRuntime: () => http.post<ApiResponse<any>>('/automation-os/runtime/recalculate/', {}),
  setRuntimeMode: (mode: string) => http.post<ApiResponse<any>>(`/automation-os/runtime/mode/${mode}/`, {}),
  globalControl: (action: 'pause-all' | 'resume-all') => http.post<ApiResponse<any>>(`/automation-os/runtime/control/${action}/`, {}),

  // Engines
  listEngines: () => http.get<ApiResponse<any[]>>('/automation-os/engines/'),
  pauseEngine: (id: string) => http.post<ApiResponse<any>>(`/automation-os/engines/${id}/pause/`, {}),
  resumeEngine: (id: string) => http.post<ApiResponse<any>>(`/automation-os/engines/${id}/resume/`, {}),
  maintenanceEngine: (id: string) => http.post<ApiResponse<any>>(`/automation-os/engines/${id}/maintenance/`, {}),

  // Policies & Buckets
  listPolicies: () => http.get<ApiResponse<any[]>>('/automation-os/policies/'),
  listWorkloads: () => http.get<ApiResponse<any[]>>('/automation-os/workloads/'),

  // Coverage & Insights
  getBusinessCoverage: () => http.get<ApiResponse<any[]>>('/automation-os/coverage/'),
  listOperatingEvents: () => http.get<ApiResponse<any[]>>('/automation-os/events/'),
  listOperatingInsights: () => http.get<ApiResponse<any[]>>('/automation-os/insights/'),
}
