import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const automationObservabilityApi = {
  getLiveMonitors: () => http.get<ApiResponse<any[]>>('/workflow-observability/live/'),
  getFailures: () => http.get<ApiResponse<any[]>>('/workflow-observability/failures/'),
  getLatency: () => http.get<ApiResponse<any[]>>('/workflow-observability/latency/'),
  getDependencies: () => http.get<ApiResponse<any[]>>('/workflow-observability/dependencies/'),
  getAnomalies: () => http.get<ApiResponse<any[]>>('/workflow-observability/anomalies/'),
  getAlerts: () => http.get<ApiResponse<any[]>>('/workflow-observability/alerts/'),
}
