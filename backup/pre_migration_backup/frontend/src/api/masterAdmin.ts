import http from '@/utils/http'

export const masterAdminApi = {
  listTenants: (params?: { tenant_type?: string; status?: string; search?: string }) =>
    http.get('/admin/tenants/', { params }),

  getTenant: (tenantId: string) =>
    http.get(`/admin/tenants/${tenantId}/`),

  verifyTenant: (tenantId: string) =>
    http.post(`/admin/tenants/${tenantId}/verify/`, {}),

  suspendTenant: (tenantId: string, reason?: string) =>
    http.post(`/admin/tenants/${tenantId}/suspend/`, { reason: reason || '' }),

  reactivateTenant: (tenantId: string, reason?: string) =>
    http.post(`/admin/tenants/${tenantId}/reactivate/`, { reason: reason || '' }),

  deactivateTenant: (tenantId: string, reason?: string) =>
    http.post(`/admin/tenants/${tenantId}/deactivate/`, { reason: reason || '' }),

  updateTenantFeatureFlags: (tenantId: string, featureFlags: Record<string, boolean>) =>
    http.put(`/admin/tenants/${tenantId}/feature-flags/`, { feature_flags: featureFlags }),

  updateTenantLimits: (
    tenantId: string,
    limits: { user_limit?: number; job_limit?: number; candidate_limit?: number }
  ) =>
    http.put(`/admin/tenants/${tenantId}/limits/`, limits),

  listPlatformSettings: () =>
    http.get('/admin/settings/'),

  updatePlatformSettings: (settings: Array<{ key: string; value_json: Record<string, unknown> }>) =>
    http.put('/admin/settings/', { settings }),

  listAudit: (params?: { action_type?: string; target_type?: string; tenant_id?: string; limit?: number }) =>
    http.get('/admin/audit/', { params }),
}
