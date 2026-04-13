import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const automationChangeImpactApi = {
  listAnalysis: () => http.get<ApiResponse<any[]>>('/workflow-change/analysis/'),
  analyzeChange: (data: any) => http.post<ApiResponse<any>>('/workflow-change/analyze/', data),
  listDependencies: () => http.get<ApiResponse<any[]>>('/workflow-change/dependencies/'),
  listDeploymentPlans: () => http.get<ApiResponse<any[]>>('/workflow-change/deployment-plan/'),
  deployChange: (data: any) => http.post<ApiResponse<any>>('/workflow-change/deploy/', data),
  listRollbackPreviews: (params?: any) => http.get<ApiResponse<any[]>>('/workflow-change/rollback-preview/', { params }),
}
