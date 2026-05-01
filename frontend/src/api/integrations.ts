import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const integrationsApi = {
  listIntegrations: () =>
    http.get<ApiResponse<{ integrations: any[] }>>('/integrations/'),

  updateIntegration: (data: any) =>
    http.post<ApiResponse<any>>('/integrations/', data),

  getIntegration: (id: string) =>
    http.get<ApiResponse<any>>(`/integrations/${id}/`),

  deleteIntegration: (id: string) =>
    http.delete<ApiResponse<null>>(`/integrations/${id}/`),
}
