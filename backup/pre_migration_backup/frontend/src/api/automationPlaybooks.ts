import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const automationPlaybooksApi = {
  // Library & CRUD
  listPlaybooks: () => http.get<ApiResponse<any[]>>('/automation-playbooks/playbooks/'),
  getLibrary: () => http.get<ApiResponse<any[]>>('/automation-playbooks/playbooks/library/'),
  getPlaybook: (id: string) => http.get<ApiResponse<any>>(`/automation-playbooks/playbooks/${id}/`),
  getPreview: (id: string) => http.get<ApiResponse<any>>(`/automation-playbooks/playbooks/${id}/preview/`),

  // Installation
  installPlaybook: (id: string, config: any) => 
    http.post<ApiResponse<any>>(`/automation-playbooks/playbooks/${id}/install/`, { config }),
  rollbackInstall: (id: string) => 
    http.post<ApiResponse<any>>(`/automation-playbooks/playbooks/${id}/rollback/`, {}),
  listInstalled: () => 
    http.get<ApiResponse<any[]>>('/automation-playbooks/playbooks/installed/'),

  // Customization
  duplicatePlaybook: (id: string) => 
    http.post<ApiResponse<any>>(`/automation-playbooks/playbooks/${id}/duplicate/`, {}),

  // Recommendations
  listRecommendations: () => 
    http.get<ApiResponse<any[]>>('/automation-playbooks/recommendations/'),

  // Analytics
  getAnalytics: () => 
    http.get<ApiResponse<any>>('/automation-playbooks/analytics/'),
}
