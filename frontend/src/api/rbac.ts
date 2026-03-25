import type { ApiResponse } from '@/types'
import http from '@/utils/http'

export interface PermissionMeta {
  id?: string
  code: string
  label?: string
  description?: string
  module: string
  module_label?: string
  resource?: string
  action?: string
  is_active?: boolean
  tenant_type_applicability?: 'shared' | 'company' | 'agency' | 'candidate'
}

export interface RoleMeta {
  id: string
  role_key?: string
  role_name?: string
  name: string
  display_name: string
  description: string
  is_system: boolean
  is_system_role?: boolean
  tenant_type_applicability?: 'shared' | 'company' | 'agency' | 'candidate'
  is_assignable?: boolean
  tenant_id: string | null
  based_on_role_id: string | null
  permission_count: number
  permissions: PermissionMeta[]
}

export interface RoleCatalogResponse {
  can_manage_roles: boolean
  system_templates: RoleMeta[]
  tenant_roles: RoleMeta[]
  all_permissions: PermissionMeta[]
  current_user: {
    id: string
    email: string
    role: string
    tenant_id: string | null
    permission_count: number
    tenant_type?: 'company' | 'agency' | 'candidate'
  }
}

export const rbacApi = {
  getCatalog: () =>
    http.get<ApiResponse<RoleCatalogResponse>>('/rbac/roles/'),

  createRole: (payload: {
    name: string
    display_name: string
    description?: string
    permission_codes: string[]
    based_on_role_id?: string
  }) =>
    http.post<ApiResponse<{ role: RoleMeta }>>('/rbac/roles/', payload),

  cloneTemplate: (
    templateRoleId: string,
    payload: { name?: string; display_name?: string; description?: string }
  ) =>
    http.post<ApiResponse<{ role: RoleMeta }>>(`/rbac/roles/${templateRoleId}/clone-template/`, payload),

  updateRole: (
    roleId: string,
    payload: { name: string; display_name: string; description?: string; permission_codes: string[] }
  ) =>
    http.put<ApiResponse<{ role: RoleMeta }>>(`/rbac/roles/${roleId}/`, payload),

  deleteRole: (roleId: string) =>
    http.delete<ApiResponse<null>>(`/rbac/roles/${roleId}/`),
}
