import http from '@/utils/http'
import type { ApiResponse } from '@/types/api'

export interface OrganisationProfile {
  id: string
  tenant_id: string
  name: string
  industry?: string
  website?: string
  size_range?: string
  country_code: string
  primary_language: string
  primary_currency: string
  timezone: string
  cin?: string
  gst_number?: string
  registration_number?: string
}

export interface DepartmentPayload {
  name: string
  parent_id?: string
  description?: string
}

export interface LocationPayload {
  name: string
  address_line1?: string
  city?: string
  state?: string
  country?: string
  is_headquarters?: boolean
}

export interface TeamPayload {
  name: string
  department_id?: string
  location_id?: string
  description?: string
}

export interface HierarchySetupPayload {
  locations: LocationPayload[]
  departments: DepartmentPayload[]
  teams: TeamPayload[]
}

export const organisationApi = {
  getProfile: () => http.get<ApiResponse<{ organisation: OrganisationProfile }>>('/organisations/profile/'),
  
  updateProfile: (data: Partial<OrganisationProfile>) => 
    http.patch<ApiResponse<{ organisation: OrganisationProfile }>>('/organisations/profile/', data),

  // New Hierarchy Endpoints
  setupHierarchy: (data: HierarchySetupPayload) =>
    http.post<ApiResponse<any>>('/organisations/setup-hierarchy/', data),

  listDepartments: () => http.get<ApiResponse<any[]>>('/organisations/departments/'),
  listLocations: () => http.get<ApiResponse<any[]>>('/organisations/locations/'),
  listTeams: () => http.get<ApiResponse<any[]>>('/organisations/teams/'),
}
