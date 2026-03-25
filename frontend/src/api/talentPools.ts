import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export interface TalentPool {
  id: string
  tenant_id: string
  tenant_type: 'company' | 'agency'
  name: string
  slug: string
  description: string
  pool_type: 'manual' | 'smart'
  color: string
  is_active: boolean
  created_by: string
  created_at: string
  updated_at: string
  member_count: number
  filters_json: Record<string, any>
  metadata: Record<string, any>
}

export interface TalentPoolMembership {
  id: string
  tenant_id: string
  talent_pool: string
  candidate: string
  candidate_details: {
    id: string
    first_name: string
    last_name: string
    email: string
    phone: string
    current_title: string
    current_location_city: string
    experience_years: number
  }
  added_by: string
  added_at: string
  source: 'manual' | 'rule' | 'import'
  note: string
}

export const talentPoolsApi = {
  list: (params?: { search?: string }) =>
    http.get<ApiResponse<{ talent_pools: TalentPool[] }>>('/talent-pools/pools/', { params }),

  get: (id: string) =>
    http.get<ApiResponse<{ talent_pool: TalentPool }>>(`/talent-pools/pools/${id}/`),

  create: (data: Partial<TalentPool>) =>
    http.post<ApiResponse<{ talent_pool: TalentPool }>>('/talent-pools/pools/', data),

  update: (id: string, data: Partial<TalentPool>) =>
    http.put<ApiResponse<{ talent_pool: TalentPool }>>(`/talent-pools/pools/${id}/`, data),

  delete: (id: string) =>
    http.delete(`/talent-pools/pools/${id}/`),

  listMembers: (poolId: string) =>
    http.get<ApiResponse<{ memberships: TalentPoolMembership[] }>>('/talent-pools/memberships/', { 
      params: { talent_pool_id: poolId } 
    }),

  bulkAdd: (poolId: string, data: { candidate_ids: string[]; note?: string; source?: string }) =>
    http.post<ApiResponse<{ added_count: number }>>(`/talent-pools/pools/${poolId}/bulk-add/`, data),

  bulkRemove: (poolId: string, data: { candidate_ids: string[] }) =>
    http.post<ApiResponse<{ removed_count: number }>>(`/talent-pools/pools/${poolId}/bulk-remove/`, data),

  getCandidatePools: (candidateId: string) =>
    http.get<ApiResponse<{ talent_pools: TalentPool[] }>>(`/candidates/${candidateId}/talent-pools/`),
}
