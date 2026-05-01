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
    http.post<ApiResponse<LoginResponse>>('/auth/login/', payload),

  registerCompany: (payload: RegisterCompanyPayload) =>
    http.post<ApiResponse<LoginResponse>>('/auth/register/company/', payload),

  registerAgency: (payload: RegisterAgencyPayload) =>
    http.post<ApiResponse<LoginResponse>>('/auth/register/agency/', payload),

  registerCandidate: (payload: RegisterCandidatePayload) =>
    http.post<ApiResponse<LoginResponse>>('/auth/register/candidate/', payload),

  sendOTP: (email: string) =>
    http.post<ApiResponse<null>>('/auth/send-otp/', { email }),

  verifyOTP: (email: string, code: string) =>
    http.post<ApiResponse<{ user: User; access_token: string; refresh_token: string }>>('/auth/verify-otp/', { email, code }),

  completeOnboarding: (payload: OnboardingPayload) =>
    http.post<ApiResponse<{ user: User }>>('/auth/onboarding/complete/', payload),

  me: () =>
    http.get<ApiResponse<{ user: User }>>('/auth/me/'),

  updateMe: (data: Partial<User>) =>
    http.put<ApiResponse<{ user: User }>>('/auth/me/', data),

  logout: (refreshToken: string) =>
    http.post<ApiResponse<null>>('/auth/logout/', { refresh_token: refreshToken }),

  refreshToken: (refresh_token: string) =>
    http.post<ApiResponse<AuthTokens>>('/auth/refresh/', { refresh: refresh_token }),

  changePassword: (old_password: string, new_password: string) =>
    http.post<ApiResponse<null>>('/auth/change-password/', { old_password, new_password }),

  forgotPassword: (email: string) =>
    http.post<ApiResponse<null>>('/auth/forgot-password/', { email }),

  resetPassword: (token: string, password: string) =>
    http.post<ApiResponse<null>>('/auth/reset-password/', { token, password }),

  getRecruiterIntelligence: (params?: { user_id?: string }) =>
    http.get<ApiResponse<{ team?: any[]; metrics?: any; workload?: any }>>('/auth/recruiters/intelligence/', { params }),

  getJobRecruiterRecommendations: (jobId: string) =>
    http.get<ApiResponse<{ recommendations: any[]; overloaded: any[]; available: any[] }>>(`/auth/jobs/${jobId}/recruiter-recommendations/`),
}
