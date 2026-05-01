import type { UserRole } from '@/types'

export const COMPANY_ROLES: UserRole[] = [
  'tenant_admin',
  'super_admin',
  'hr_manager',
  'recruiter',
  'hiring_manager',
  'interviewer',
  'viewer',
]

export const AGENCY_ROLES: UserRole[] = [
  'agency_owner',
  'agency_admin',
  'agency_recruiter',
]

export const CANDIDATE_ROLES: UserRole[] = ['candidate']

export const NON_CANDIDATE_ROLES: UserRole[] = [
  ...COMPANY_ROLES,
  ...AGENCY_ROLES,
]

export const RECRUITER_OPERATIONAL_ROLES: UserRole[] = [
  'tenant_admin',
  'super_admin',
  'recruiter',
  'hiring_manager',
]

export const COMPANY_AND_AGENCY_RECRUITER_ROLES: UserRole[] = [
  ...RECRUITER_OPERATIONAL_ROLES,
  ...AGENCY_ROLES,
]

export const COMPANY_HIRING_ROLES: UserRole[] = [
  ...RECRUITER_OPERATIONAL_ROLES,
  'hr_manager',
]

export const ADMIN_ONLY_ROLES: UserRole[] = [
  'tenant_admin',
  'super_admin',
]

export const COMPANY_ADMIN_ROLES: UserRole[] = [...ADMIN_ONLY_ROLES]

export const TENANT_OR_AGENCY_ADMIN_ROLES: UserRole[] = [
  ...ADMIN_ONLY_ROLES,
  'agency_owner',
  'agency_admin',
]

export const COMPANY_HR_ROLES: UserRole[] = [
  ...ADMIN_ONLY_ROLES,
  'hr_manager',
]

export const COMPANY_HR_HIRING_ROLES: UserRole[] = [
  ...COMPANY_HR_ROLES,
  'hiring_manager',
]

export function isAgencyRole(role: string | null | undefined): boolean {
  return AGENCY_ROLES.includes((role || '') as UserRole)
}

export function isCompanyAdminRole(role: string | null | undefined): boolean {
  return COMPANY_ADMIN_ROLES.includes((role || '') as UserRole)
}
