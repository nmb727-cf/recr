import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const qaApi = {
  getModules: () => http.get<ApiResponse<any[]>>('/qa/readiness/modules/'),
  getBlockers: () => http.get<ApiResponse<any[]>>('/qa/readiness/blockers/'),
  getScenarios: () => http.get<ApiResponse<any[]>>('/qa/readiness/scenarios/'),
}
