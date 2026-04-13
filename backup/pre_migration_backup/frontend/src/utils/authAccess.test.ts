import { describe, expect, it } from 'vitest'

import { canAccessMasterAdmin, resolvePostLoginRoute } from './authAccess'

describe('authAccess', () => {
  it('allows master-admin access via explicit permission', () => {
    expect(
      canAccessMasterAdmin({
        role: 'tenant_admin',
        permissions: ['master_admin.access'],
      } as any),
    ).toBe(true)
  })

  it('resolves role-based post-login dashboard routes', () => {
    expect(resolvePostLoginRoute({ role: 'super_admin', permissions: [] } as any)).toBe('/admin')
    expect(resolvePostLoginRoute({ role: 'tenant_admin', permissions: [] } as any)).toBe('/dashboard')
    expect(resolvePostLoginRoute({ role: 'agency_admin', permissions: [] } as any)).toBe('/agencies/my-jobs')
    expect(resolvePostLoginRoute({ role: 'candidate', permissions: [] } as any)).toBe('/candidate/dashboard')
  })
})
