import { User, JobRequisition } from '@/types'

/**
 * Resolves if a user is the owner of a job, including fallback logic for tenant admins.
 * Follows the Phase 5C requirement: 
 * If created_by is missing/inactive/unavailable, fallback to Tenant Admin.
 */
export function isJobOwner(user: User | null, job: JobRequisition | null): boolean {
  if (!user || !job) return false

  // 1. Super Admin always has full access (safe system override)
  if (user.role === 'super_admin') return true

  // 2. Tenant Admin acts as owner for all jobs in their tenant (Primary Fallback)
  if (user.role === 'tenant_admin' && user.tenant_id === job.tenant_id) return true

  // 3. Direct ownership check based on created_by
  if (job.created_by === user.id) return true

  // Future improvement: check active team assignments if ownership is shared
  
  return false
}

/**
 * Centralized helper for checking if a user can perform an action on a job.
 * Ensures backend enforcement rules are mirrored in the frontend.
 */
export function canPerformJobAction(
  action: 'move_stage' | 'edit_job' | 'assign_agency' | 'make_offer' | 'view_commercials',
  job: JobRequisition | null,
  user: User | null
): boolean {
  if (!user || !job) return false

  // For manual stage moves, ownership is strictly required post-submission
  if (action === 'move_stage') {
    return isJobOwner(user, job)
  }

  // Management actions
  if (['edit_job', 'assign_agency', 'make_offer'].includes(action)) {
    return isJobOwner(user, job)
  }

  // Commercial visibility
  if (action === 'view_commercials') {
    return isJobOwner(user, job) || ['hr_manager', 'finance_admin'].includes(user.role)
  }

  return false
}
