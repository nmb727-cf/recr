import type { User } from '@/types'

const COMPANY_ROLES = new Set([
  'tenant_admin',
  'hr_manager',
  'recruiter',
  'hiring_manager',
  'interviewer',
  'viewer',
])

const AGENCY_ROLES = new Set([
  'agency_owner',
  'agency_admin',
  'agency_recruiter',
])
const MASTER_ADMIN_PERMISSION = 'master_admin.access'

export function canAccessMasterAdmin(user: User | null | undefined): boolean {
  if (!user) return false
  const permissions = Array.isArray(user.permissions) ? user.permissions : []
  return Boolean(
    user.role === 'super_admin' ||
      user.is_super_admin ||
      user.is_superuser ||
      user.is_staff ||
      permissions.includes(MASTER_ADMIN_PERMISSION)
  )
}

export function resolvePostLoginRoute(user: User | null | undefined): string {
  if (!user) return '/unauthorized'
  if (canAccessMasterAdmin(user)) return '/admin'
  if (user.role === 'candidate') return '/candidate/dashboard'
  if (AGENCY_ROLES.has(user.role)) return '/agencies/my-jobs'
  if (COMPANY_ROLES.has(user.role)) return '/dashboard'
  return '/unauthorized'
}
