import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'
import { authApi } from '@/api/auth'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  hasHydrated: boolean
  pendingVerificationEmail: string | null

  // Actions
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  setUser: (user: User) => void
  setTokens: (access: string, refresh: string) => void
  clearAuth: () => void
  fetchMe: () => Promise<void>
  setPendingVerificationEmail: (email: string | null) => void
  setHasHydrated: (hydrated: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      hasHydrated: false,
      pendingVerificationEmail: null,

      setUser: (user) => set({ user }),

      setPendingVerificationEmail: (email) => set({ pendingVerificationEmail: email }),
      setHasHydrated: (hydrated) => set({ hasHydrated: hydrated }),

      setTokens: (access, refresh) => {
        localStorage.setItem('access_token', access)
        localStorage.setItem('refresh_token', refresh)
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true })
      },

      clearAuth: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          pendingVerificationEmail: null,
        })
      },

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const axiosResponse = await authApi.login({ email, password })
          const access_token = axiosResponse.data.data.access_token
          const refresh_token = axiosResponse.data.data.refresh_token
          const user = axiosResponse.data.data.user
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', refresh_token)
          set({
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            pendingVerificationEmail: null,
          })
        } catch (err) {
          throw err
        } finally {
          set({ isLoading: false })
        }
      },

      logout: async () => {
        try {
          const token = get().refreshToken ?? localStorage.getItem('refresh_token') ?? ''
          if (token) await authApi.logout(token)
        } catch {
          // ignore errors — still clear local state
        }
        get().clearAuth()
      },

      fetchMe: async () => {
        try {
          const { data: res } = await authApi.me()
          set({ user: res.data.user })
        } catch (err: any) {
          // Only clear auth on a real 401 — not on network errors or server errors
          if (err?.response?.status === 401) {
            get().clearAuth()
          }
        }
      },
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        pendingVerificationEmail: state.pendingVerificationEmail,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.setHasHydrated(true)
        }
      },
    }
  )
)
