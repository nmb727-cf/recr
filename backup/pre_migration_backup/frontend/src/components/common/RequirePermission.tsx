import { ReactNode } from 'react'
import { usePermission, usePermissionAll, usePermissionAny } from '@/hooks/usePermission'

interface RequirePermissionProps {
  /** Single permission code that must be held */
  code?: string
  /** All of these codes must be held */
  all?: string[]
  /** At least one of these codes must be held */
  any?: string[]
  /** Rendered when permission check fails. Defaults to null (hidden). */
  fallback?: ReactNode
  children: ReactNode
}

/**
 * Conditionally renders children based on the current user's permissions.
 *
 * Usage:
 *   <RequirePermission code="candidates.candidate.view">
 *     <CandidatesPage />
 *   </RequirePermission>
 *
 *   <RequirePermission any={['jobs.job.create', 'jobs.job.edit']} fallback={<Locked />}>
 *     <JobActions />
 *   </RequirePermission>
 */
export function RequirePermission({
  code,
  all,
  any,
  fallback = null,
  children,
}: RequirePermissionProps) {
  const single = usePermission(code ?? '')
  const allPassed = usePermissionAll(...(all ?? []))
  const anyPassed = usePermissionAny(...(any ?? []))

  let allowed = true
  if (code) allowed = single
  else if (all?.length) allowed = allPassed
  else if (any?.length) allowed = anyPassed

  return <>{allowed ? children : fallback}</>
}
