type PersistedAuthSnapshot = {
  state?: Record<string, unknown>
  [key: string]: unknown
}

function safeParse(raw: string | null): PersistedAuthSnapshot | null {
  if (!raw) return null
  try {
    return JSON.parse(raw) as PersistedAuthSnapshot
  } catch {
    return null
  }
}

export function readStoredAccessToken(): string | null {
  const persisted = safeParse(localStorage.getItem('auth-store'))
  const state = (persisted?.state ?? persisted ?? {}) as Record<string, unknown>
  const token =
    (typeof state.accessToken === 'string' && state.accessToken) ||
    (typeof state.access_token === 'string' && state.access_token) ||
    (typeof (persisted as Record<string, unknown> | null)?.accessToken === 'string' &&
      ((persisted as Record<string, unknown>).accessToken as string)) ||
    (typeof (persisted as Record<string, unknown> | null)?.access_token === 'string' &&
      ((persisted as Record<string, unknown>).access_token as string)) ||
    localStorage.getItem('access_token') ||
    null
  return token || null
}

export function readStoredTenantId(): string | null {
  const persisted = safeParse(localStorage.getItem('auth-store'))
  const state = (persisted?.state ?? persisted ?? {}) as Record<string, unknown>
  const user = (state.user as Record<string, unknown> | undefined) || {}
  const tenantId =
    (typeof user.tenant_id === 'string' && user.tenant_id) ||
    (typeof user.tenantId === 'string' && user.tenantId) ||
    localStorage.getItem('tenant_id') ||
    null
  return tenantId || null
}
