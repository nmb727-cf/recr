import axios from 'axios'
import { readStoredAccessToken, readStoredTenantId } from '@/utils/authSession'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

const PUBLIC_ENDPOINTS = [
  '/auth/login/',
  '/auth/register/company/',
  '/auth/register/agency/',
  '/auth/register/candidate/',
  '/auth/send-otp/',
  '/auth/verify-otp/',
  '/auth/verify-email/',
  '/auth/forgot-password/',
  '/auth/reset-password/',
  '/auth/refresh/',
  '/jobs/search/',
  '/passport/public/',
]

// Attach token from localStorage on every request
http.interceptors.request.use((config) => {
  if (config.headers?.['X-Skip-Auth']) {
    delete config.headers['X-Skip-Auth']
    return config
  }

  // Skip auth for public endpoints
  const url = config.url || ''
  const isPublic = PUBLIC_ENDPOINTS.some(endpoint => url.includes(endpoint))
  if (isPublic) {
    return config
  }

  const token = readStoredAccessToken()
  const tenantId = readStoredTenantId()

  if (token) {
    // Keep legacy consumers in sync with persisted auth-store sessions.
    if (!localStorage.getItem('access_token')) {
      localStorage.setItem('access_token', token)
    }
    config.headers.Authorization = `Bearer ${token}`
  }
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId
  }
  return config
})

// On 401, clear all auth state (both standalone keys and Zustand persist) and redirect to login
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn('[http] 401 received — clearing auth state and redirecting to login', error.config?.url)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('auth-store')
      window.location.href = '/login'
    } else {
      // Show errors without relying on static antd message API
      // (static API is deprecated under dynamic theming contexts).
      const errData = error.response?.data
      const errorMsg = errData?.message || error.message || 'An unexpected error occurred'
      
      // Check if this request explicitly wants to skip the toast
      if (!(error.config as any)?.hideErrorToast) {
        console.error('[http]', errorMsg)
      }
    }
    return Promise.reject(error)
  }
)

export default http
