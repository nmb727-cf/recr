import http from '@/utils/http'
import type { ApiResponse, User, AuthTokens, LoginPayload, RegisterCompanyPayload, RegisterAgencyPayload, RegisterCandidatePayload } from '@/types'

interface LoginResponse {
  user: User
  access_token: string
  refresh_token: string
}

export interface OnboardingPayload {
  // user_type is derived server-side from the user's role; not sent by the wizard
  hiring_style: 'internal' | 'agency' | 'mixed'
  team_size: '1-5' | '5-20' | '20+'
  automation_preference: 'manual' | 'smart' | 'fully_automated'
}

export const authApi = {
  login: (payload: LoginPayload) =>
    http.post<ApiResponse<LoginResponse>>('/accounts/login/', payload),

  registerCompany: (payload: RegisterCompanyPayload) =>
    http.post<ApiResponse<LoginResponse>>('/accounts/register/company/', payload),

  registerAgency: (payload: RegisterAgencyPayload) =>
    http.post<ApiResponse<LoginResponse>>('/accounts/register/agency/', payload),

  registerCandidate: (payload: RegisterCandidatePayload) =>
    http.post<ApiResponse<LoginResponse>>('/accounts/register/candidate/', payload),

  sendOTP: (email: string) =>
    http.post<ApiResponse<null>>('/accounts/send-otp/', { email }),

  verifyOTP: (email: string, code: string) =>
    http.post<ApiResponse<{ user: User; access_token: string; refresh_token: string }>>('/accounts/verify-otp/', { email, code }),

  completeOnboarding: (payload: OnboardingPayload) =>
    http.post<ApiResponse<{ user: User }>>('/accounts/onboarding/complete/', payload),

  me: () =>
    http.get<ApiResponse<{ user: User }>>('/accounts/me/'),

  updateMe: (data: Partial<User>) =>
    http.put<ApiResponse<{ user: User }>>('/accounts/me/', data),

  logout: () =>
    http.post<ApiResponse<null>>('/accounts/logout/'),

  refreshToken: (refresh_token: string) =>
    http.post<ApiResponse<AuthTokens>>('/accounts/refresh/', { refresh: refresh_token }),

  changePassword: (old_password: string, new_password: string) =>
    http.post<ApiResponse<null>>('/accounts/change-password/', { old_password, new_password }),

  forgotPassword: (email: string) =>
    http.post<ApiResponse<null>>('/accounts/forgot-password/', { email }),

  resetPassword: (token: string, password: string) =>
    http.post<ApiResponse<null>>('/accounts/reset-password/', { token, password }),
}
