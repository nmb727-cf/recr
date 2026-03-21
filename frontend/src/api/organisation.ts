import http from '@/utils/http'
import type { ApiResponse, Organisation, Department, Location } from '@/types'

export const organisationApi = {
  getProfile: () =>
    http.get<ApiResponse<{ organisation: Organisation }>>('/organisation/profile/'),

  updateProfile: (data: Partial<Organisation>) =>
    http.put<ApiResponse<{ organisation: Organisation }>>('/organisation/profile/', data),

  listUsers: () =>
    http.get('/organisation/users/'),

  listDepartments: () =>
    http.get<ApiResponse<{ departments: Department[] }>>('/organisation/departments/'),

  createDepartment: (data: Partial<Department>) =>
    http.post<ApiResponse<{ department: Department }>>('/organisation/departments/', data),

  listLocations: () =>
    http.get<ApiResponse<{ locations: Location[] }>>('/organisation/locations/'),

  createLocation: (data: Partial<Location>) =>
    http.post<ApiResponse<{ location: Location }>>('/organisation/locations/', data),
}
