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

  // Read from standalone key first
  let token = localStorage.getItem('access_token')

  // Fallback: read from Zustand persisted store
  if (!token) {
    try {
      const raw = localStorage.getItem('auth-store')
      if (raw) {
        const parsed = JSON.parse(raw)
        token = parsed?.state?.accessToken ?? null
        // Re-write standalone key so future requests dont need fallback
        if (token) {
          localStorage.setItem('access_token', token)
        }
      }
    } catch {
      token = null
    }
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401, clear auth and redirect to login
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default http
