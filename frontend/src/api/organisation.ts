import http from '@/utils/http'
import type { ApiResponse, Organisation, Department, Location, User } from '@/types'

export const organisationApi = {
  // Organisation
  getProfile: () =>
    http.get<ApiResponse<{ organisation: Organisation }>>('/organisation/profile/'),
  updateProfile: (data: Partial<Organisation>) =>
    http.put<ApiResponse<{ organisation: Organisation }>>('/organisation/profile/', data),

  // Users
  listUsers: () =>
    http.get<ApiResponse<{ users: User[] }>>('/organisation/users/'),
  inviteUser: (data: { email: string; role: string; first_name?: string; last_name?: string }) =>
    http.post<ApiResponse<{ user: User }>>('/organisation/users/', data),
  updateUser: (id: string, data: { role?: string; is_active?: boolean }) =>
    http.put<ApiResponse<{ user: User }>>(`/organisation/users/${id}/`, data),
  deleteUser: (id: string) =>
    http.delete<ApiResponse<null>>(`/organisation/users/${id}/`),

  // Departments
  listDepartments: () =>
    http.get<ApiResponse<{ departments: Department[] }>>('/organisation/departments/'),
  getDepartment: (id: string) =>
    http.get<ApiResponse<{ department: Department }>>(`/organisation/departments/${id}/`),
  createDepartment: (data: Partial<Department>) =>
    http.post<ApiResponse<{ department: Department }>>('/organisation/departments/', data),
  updateDepartment: (id: string, data: Partial<Department>) =>
    http.put<ApiResponse<{ department: Department }>>(`/organisation/departments/${id}/`, data),
  deleteDepartment: (id: string) =>
    http.delete<ApiResponse<null>>(`/organisation/departments/${id}/`),

  // Locations
  listLocations: () =>
    http.get<ApiResponse<{ locations: Location[] }>>('/organisation/locations/'),
  getLocation: (id: string) =>
    http.get<ApiResponse<{ location: Location }>>(`/organisation/locations/${id}/`),
  createLocation: (data: Partial<Location>) =>
    http.post<ApiResponse<{ location: Location }>>('/organisation/locations/', data),
  updateLocation: (id: string, data: Partial<Location>) =>
    http.put<ApiResponse<{ location: Location }>>(`/organisation/locations/${id}/`, data),
  deleteLocation: (id: string) =>
    http.delete<ApiResponse<null>>(`/organisation/locations/${id}/`),

}
