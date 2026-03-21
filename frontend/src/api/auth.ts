import http from '@/utils/http'
import type { ApiResponse, User, AuthTokens, LoginPayload, RegisterCompanyPayload, RegisterCandidatePayload } from '@/types'

interface LoginResponse {
  user: User
  access_token: string
  refresh_token: string
}

export const authApi = {
  login: (payload: LoginPayload) =>
    http.post<ApiResponse<LoginResponse>>('/auth/login/', payload),

  registerCompany: (payload: RegisterCompanyPayload) =>
    http.post<ApiResponse<LoginResponse>>('/auth/register/company/', payload),

  registerCandidate: (payload: RegisterCandidatePayload) =>
    http.post<ApiResponse<LoginResponse>>('/auth/register/candidate/', payload),

  me: () =>
    http.get<ApiResponse<{ user: User }>>('/auth/me/'),

  updateMe: (data: Partial<User>) =>
    http.put<ApiResponse<{ user: User }>>('/auth/me/', data),

  logout: () =>
    http.post<ApiResponse<null>>('/auth/logout/'),

  refreshToken: (refresh_token: string) =>
    http.post<ApiResponse<AuthTokens>>('/auth/refresh/', { refresh: refresh_token }),

  changePassword: (old_password: string, new_password: string) =>
    http.post<ApiResponse<null>>('/auth/change-password/', { old_password, new_password }),

  forgotPassword: (email: string) =>
    http.post<ApiResponse<null>>('/auth/forgot-password/', { email }),

  resetPassword: (token: string, password: string) =>
    http.post<ApiResponse<null>>('/auth/reset-password/', { token, password }),
}
