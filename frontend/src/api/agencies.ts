import http from '@/utils/http'
import type { ApiResponse, AgencyRelationship, AgencyAssignment } from '@/types'

export const agenciesApi = {
  listRelationships: () =>
    http.get<ApiResponse<{ relationships: AgencyRelationship[] }>>('/agencies/relationships/'),

  getRelationship: (id: string) =>
    http.get<ApiResponse<{ relationship: AgencyRelationship }>>(`/agencies/relationships/${id}/`),

  updateRelationship: (id: string, data: Partial<AgencyRelationship>) =>
    http.patch<ApiResponse<{ relationship: AgencyRelationship }>>(`/agencies/relationships/${id}/`, data),

  accept: (id: string) =>
    http.post(`/agencies/relationships/${id}/accept/`),

  suspend: (id: string) =>
    http.post(`/agencies/relationships/${id}/suspend/`),

  terminate: (id: string) =>
    http.post(`/agencies/relationships/${id}/terminate/`),

  invite: (data: { name: string; email: string; tier: string; commission: number }) =>
    http.post('/agencies/relationships/invite/', data),

  listAssignments: () =>
    http.get<ApiResponse<{ assignments: AgencyAssignment[] }>>('/agencies/assignments/'),
}
