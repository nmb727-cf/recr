import http from '@/utils/http'
import type { ApiResponse, Passport } from '@/types'

export const passportApi = {
  get: () =>
    http.get<ApiResponse<{ passport: Passport }>>('/passport/my-passport/'),

  update: (data: Partial<Passport>) =>
    http.put<ApiResponse<{ passport: Passport }>>('/passport/my-passport/', data),

  getShareLink: () =>
    http.get<ApiResponse<{ share_url: string }>>('/passport/my-passport/share-link/'),

  regenerateShareLink: () =>
    http.post<ApiResponse<{ share_url: string }>>('/passport/my-passport/share-link/regenerate/'),

  importPassport: (token: string) =>
    http.post<ApiResponse<{ candidate: any }>>('/passport/import/', { token }),
}
