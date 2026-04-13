import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import ProtectedRoute from './ProtectedRoute'

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(),
}))

vi.mock('@/utils/authSession', () => ({
  readStoredAccessToken: vi.fn(),
}))

function renderProtectedRoute() {
  return render(
    <MemoryRouter initialEntries={['/intelligence']}>
      <Routes>
        <Route
          path="/intelligence"
          element={
            <ProtectedRoute>
              <div>Secure Intelligence View</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>Login Page</div>} />
        <Route path="/unauthorized" element={<div>Unauthorized Page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

function renderMasterAdminProtectedRoute() {
  return render(
    <MemoryRouter initialEntries={['/admin']}>
      <Routes>
        <Route
          path="/admin"
          element={
            <ProtectedRoute requireMasterAdmin>
              <div>Master Admin View</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>Login Page</div>} />
        <Route path="/unauthorized" element={<div>Unauthorized Page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('redirects unauthenticated users to login', async () => {
    const { useAuth } = await import('@/hooks/useAuth')
    const { readStoredAccessToken } = await import('@/utils/authSession')
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      hasHydrated: true,
      user: null,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      fetchMe: vi.fn(),
    } as any)
    vi.mocked(readStoredAccessToken).mockReturnValue(null)

    renderProtectedRoute()
    expect(await screen.findByText('Login Page')).toBeInTheDocument()
  })

  it('redirects when store says authenticated but token is missing', async () => {
    const { useAuth } = await import('@/hooks/useAuth')
    const { readStoredAccessToken } = await import('@/utils/authSession')
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      hasHydrated: true,
      user: { role: 'tenant_admin' },
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      fetchMe: vi.fn(),
    } as any)
    vi.mocked(readStoredAccessToken).mockReturnValue(null)

    renderProtectedRoute()
    expect(await screen.findByText('Login Page')).toBeInTheDocument()
  })

  it('renders protected content for authenticated users with token', async () => {
    const { useAuth } = await import('@/hooks/useAuth')
    const { readStoredAccessToken } = await import('@/utils/authSession')
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      hasHydrated: true,
      user: { role: 'tenant_admin' },
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      fetchMe: vi.fn(),
    } as any)
    vi.mocked(readStoredAccessToken).mockReturnValue('token-123')

    renderProtectedRoute()
    expect(await screen.findByText('Secure Intelligence View')).toBeInTheDocument()
  })

  it('blocks non-master-admin users when requireMasterAdmin is enabled', async () => {
    const { useAuth } = await import('@/hooks/useAuth')
    const { readStoredAccessToken } = await import('@/utils/authSession')
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      hasHydrated: true,
      user: { role: 'tenant_admin', is_staff: false, is_superuser: false, is_super_admin: false },
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      fetchMe: vi.fn(),
    } as any)
    vi.mocked(readStoredAccessToken).mockReturnValue('token-123')

    renderMasterAdminProtectedRoute()
    expect(await screen.findByText('Unauthorized Page')).toBeInTheDocument()
  })

  it('allows staff users when requireMasterAdmin is enabled', async () => {
    const { useAuth } = await import('@/hooks/useAuth')
    const { readStoredAccessToken } = await import('@/utils/authSession')
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      hasHydrated: true,
      user: { role: 'tenant_admin', is_staff: true, is_superuser: false, is_super_admin: false },
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      fetchMe: vi.fn(),
    } as any)
    vi.mocked(readStoredAccessToken).mockReturnValue('token-123')

    renderMasterAdminProtectedRoute()
    expect(await screen.findByText('Master Admin View')).toBeInTheDocument()
  })

  it('allows users with master_admin.access permission when requireMasterAdmin is enabled', async () => {
    const { useAuth } = await import('@/hooks/useAuth')
    const { readStoredAccessToken } = await import('@/utils/authSession')
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      hasHydrated: true,
      user: { role: 'tenant_admin', is_staff: false, is_superuser: false, is_super_admin: false, permissions: ['master_admin.access'] },
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      fetchMe: vi.fn(),
    } as any)
    vi.mocked(readStoredAccessToken).mockReturnValue('token-123')

    renderMasterAdminProtectedRoute()
    expect(await screen.findByText('Master Admin View')).toBeInTheDocument()
  })
})
