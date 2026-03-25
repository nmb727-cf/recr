import { useAuthStore } from '@/store/authStore'

/**
 * Returns true if the current user holds the given permission code.
 * Reads directly from the permissions array already embedded in the user object,
 * so no extra network call is needed.
 *
 * Usage:
 *   const canView = usePermission('candidates.candidate.view')
 */
export function usePermission(code: string): boolean {
  const permissions = useAuthStore((s) => s.user?.permissions)
  if (!permissions) return false
  return permissions.includes(code)
}

/**
 * Returns true if the user holds ALL of the given codes.
 */
export function usePermissionAll(...codes: string[]): boolean {
  const permissions = useAuthStore((s) => s.user?.permissions)
  if (!permissions) return false
  return codes.every((c) => permissions.includes(c))
}

/**
 * Returns true if the user holds ANY of the given codes.
 */
export function usePermissionAny(...codes: string[]): boolean {
  const permissions = useAuthStore((s) => s.user?.permissions)
  if (!permissions) return false
  return codes.some((c) => permissions.includes(c))
}
