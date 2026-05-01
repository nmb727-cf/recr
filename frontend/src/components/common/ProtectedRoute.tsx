import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import type { UserRole } from '@/types'
import { readStoredAccessToken } from '@/utils/authSession'
import { canAccessMasterAdmin } from '@/utils/authAccess'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: UserRole[]
  requireMasterAdmin?: boolean
}

export default function ProtectedRoute({ children, allowedRoles, requireMasterAdmin = false }: ProtectedRouteProps) {
  const { isAuthenticated, user, hasHydrated } = useAuth()
  const location = useLocation()
  const token = readStoredAccessToken()

  if (!hasHydrated) {
    return null
  }

  if (!isAuthenticated || !token) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  if (requireMasterAdmin && !canAccessMasterAdmin(user)) {
    return <Navigate to="/unauthorized" replace />
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />
  }

  return <>{children}</>
}
