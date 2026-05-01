import http from '@/utils/http'
import type { ApiResponse, Organisation, Department, Location, User } from '@/types'

export const organisationApi = {
  // Organisation
  getProfile: () =>
    http.get<ApiResponse<{ organisation: Organisation }>>('/organisations/profile/'),
  updateProfile: (data: Partial<Organisation>) =>
    http.put<ApiResponse<{ organisation: Organisation }>>('/organisations/profile/', data),

  // Users
  listUsers: (params?: { search?: string; role?: string; status?: string }) =>
    http.get<ApiResponse<{ users: User[] }>>('/organisations/users/', { params }),
  inviteUser: (data: { email: string; role: string; first_name?: string; last_name?: string }) =>
    http.post<ApiResponse<{ user: User }>>('/organisations/users/', data),
  updateUser: (id: string, data: { role?: string; is_active?: boolean }) =>
    http.put<ApiResponse<{ user: User }>>(`/organisations/users/${id}/`, data),
  deleteUser: (id: string) =>
    http.delete<ApiResponse<null>>(`/organisations/users/${id}/`),

  globalSearch: (params?: { search?: string; q?: string; limit?: number }) =>
    http.get<ApiResponse<{
      query: string
      candidates: Array<{ id: string; name: string; email?: string; current_title?: string; current_company?: string }>
      jobs: Array<{ id: string; title: string; status?: string; job_ref_id?: string; work_mode?: string }>
      agencies: Array<{ id: string; name: string; status?: string; contact_email?: string }>
    }>>('/organisations/search/', { params }),

  // Departments
  listDepartments: () =>
    http.get<ApiResponse<{ departments: Department[] }>>('/organisations/departments/'),
  getDepartment: (id: string) =>
    http.get<ApiResponse<{ department: Department }>>(`/organisations/departments/${id}/`),
  createDepartment: (data: Partial<Department>) =>
    http.post<ApiResponse<{ department: Department }>>('/organisations/departments/', data),
  updateDepartment: (id: string, data: Partial<Department>) =>
    http.put<ApiResponse<{ department: Department }>>(`/organisations/departments/${id}/`, data),
  deleteDepartment: (id: string) =>
    http.delete<ApiResponse<null>>(`/organisations/departments/${id}/`),

  // Locations
  listLocations: () =>
    http.get<ApiResponse<{ locations: Location[] }>>('/organisations/locations/'),
  getLocation: (id: string) =>
    http.get<ApiResponse<{ location: Location }>>(`/organisations/locations/${id}/`),
  createLocation: (data: Partial<Location>) =>
    http.post<ApiResponse<{ location: Location }>>('/organisations/locations/', data),
  updateLocation: (id: string, data: Partial<Location>) =>
    http.put<ApiResponse<{ location: Location }>>(`/organisations/locations/${id}/`, data),
  deleteLocation: (id: string) =>
    http.delete<ApiResponse<null>>(`/organisations/locations/${id}/`),

}
