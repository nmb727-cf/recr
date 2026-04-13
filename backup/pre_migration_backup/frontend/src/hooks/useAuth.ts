import { useAuthStore } from '@/store/authStore'

/** Convenience hook — re-exports store state and actions */
export function useAuth() {
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const isLoading = useAuthStore((s) => s.isLoading)
  const hasHydrated = useAuthStore((s) => s.hasHydrated)
  const login = useAuthStore((s) => s.login)
  const logout = useAuthStore((s) => s.logout)
  const fetchMe = useAuthStore((s) => s.fetchMe)

  return { user, isAuthenticated, isLoading, hasHydrated, login, logout, fetchMe }
}
