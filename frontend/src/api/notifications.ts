import http from '@/utils/http'
import type { ApiResponse, Notification } from '@/types'

export const notificationsApi = {
  list: (params?: { is_read?: boolean }) =>
    http.get<ApiResponse<{ notifications: Notification[] }>>('/communications/notifications/', { params }),

  markRead: (id: string) =>
    http.post<ApiResponse<null>>(`/communications/notifications/${id}/read/`),

  markAllRead: () =>
    http.post<ApiResponse<null>>('/communications/notifications/read-all/'),
}
