import http from '@/utils/http'
import type { ApiResponse } from '@/types'

// ─── Types ────────────────────────────────────────────────────────────────────

export type PermissionLevel = 'allow' | 'deny' | 'require_approval'
export type AuditDecision   = 'allowed' | 'denied' | 'approval_required'
export type Severity        = 'low' | 'medium' | 'high' | 'critical'
export type ResourceType    = 'workflow' | 'workflow_template' | 'workflow_execution' | 'workflow_governance' | 'workflow_analytics' | 'automation_center'
export type ActionType      = 'view' | 'create' | 'edit' | 'delete' | 'activate' | 'pause' | 'archive' | 'duplicate' | 'import_template' | 'emergency_stop' | 'rollback' | 'approve' | 'dry_run' | 'view_logs' | 'view_analytics'

export interface PermissionRule {
  id?: string
  role_code: string
  module_scope: string
  resource_type: ResourceType
  action_type: ActionType
  permission_level: PermissionLevel
  conditions: Record<string, unknown>
  created_at?: string
}

export interface PermissionPolicy {
  id: string
  tenant_id: string
  name: string
  description: string
  is_active: boolean
  created_by: string
  created_at: string
  updated_at: string
  rules: PermissionRule[]
}

export interface RestrictedAction {
  id: string
  tenant_id: string
  action_key: string
  description: string
  severity: Severity
  requires_approval: boolean
  requires_admin: boolean
  created_at: string
}

export interface AuditLog {
  id: string
  tenant_id: string
  user_id: string
  workflow_id: string | null
  action_attempted: string
  decision: AuditDecision
  reason: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface PermissionCheckResult {
  allowed: boolean
  requires_approval: boolean
  decision: AuditDecision
  reason: string
}

export type RoleMatrix = Record<string, Record<string, PermissionLevel>>

export interface PolicyWritePayload {
  name: string
  description?: string
  is_active?: boolean
  rules?: Omit<PermissionRule, 'id' | 'created_at'>[]
}

export interface AuditFilterParams {
  user_id?: string
  workflow_id?: string
  decision?: AuditDecision
  limit?: number
  offset?: number
}

// ─── API client ───────────────────────────────────────────────────────────────

export const automationPermissionsApi = {
  // Policies
  listPolicies: () =>
    http.get<ApiResponse<{ policies: PermissionPolicy[] }>>('/workflow-permissions/policies/'),

  createPolicy: (data: PolicyWritePayload) =>
    http.post<ApiResponse<{ policy: PermissionPolicy }>>('/workflow-permissions/policies/', data),

  getPolicy: (id: string) =>
    http.get<ApiResponse<{ policy: PermissionPolicy }>>(`/workflow-permissions/policies/${id}/`),

  updatePolicy: (id: string, data: Partial<PolicyWritePayload>) =>
    http.put<ApiResponse<{ policy: PermissionPolicy }>>(`/workflow-permissions/policies/${id}/`, data),

  deletePolicy: (id: string) =>
    http.delete<ApiResponse<Record<string, never>>>(`/workflow-permissions/policies/${id}/`),

  // Restricted actions
  listRestrictedActions: () =>
    http.get<ApiResponse<{ restricted_actions: RestrictedAction[] }>>('/workflow-permissions/restricted-actions/'),

  updateRestrictedAction: (id: string, data: Partial<Pick<RestrictedAction, 'severity' | 'requires_approval' | 'requires_admin'>>) =>
    http.put<ApiResponse<{ restricted_action: RestrictedAction }>>(`/workflow-permissions/restricted-actions/${id}/`, data),

  // Audit
  getAuditLogs: (params?: AuditFilterParams) =>
    http.get<ApiResponse<{ audit_logs: AuditLog[] }>>('/workflow-permissions/audit/', { params }),

  // Role matrix
  getRoleMatrix: () =>
    http.get<ApiResponse<{ matrix: RoleMatrix }>>('/workflow-permissions/matrix/'),

  // Permission check
  checkPermission: (data: { workflow_id?: string; action: string; resource_type?: string }) =>
    http.post<ApiResponse<PermissionCheckResult>>('/workflow-permissions/check/', data),
}
