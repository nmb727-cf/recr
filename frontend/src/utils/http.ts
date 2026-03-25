import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

const PUBLIC_ENDPOINTS = [
  '/auth/login/',
  '/auth/register/company/',
  '/auth/register/agency/',
  '/auth/register/candidate/',
  '/auth/forgot-password/',
  '/auth/reset-password/',
  '/jobs/search/',
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

  // Always check Zustand store first for most up-to-date token
  let token = null
  try {
    const raw = localStorage.getItem('auth-store')
    if (raw) {
      const parsed = JSON.parse(raw)
      token = parsed?.state?.accessToken ?? null
    }
  } catch (err) {
    console.error('Error parsing auth-store', err)
  }

  // Fallback to standalone key
  if (!token) {
    token = localStorage.getItem('access_token')
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
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
    }
    return Promise.reject(error)
  }
)

export default http
