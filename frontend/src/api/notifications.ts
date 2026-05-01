import http from '@/utils/http'
import type { ApiResponse } from '@/types'
import type { Notification } from '@/types/communications'

export const notificationsApi = {
  list: (params?: { is_read?: boolean; severity?: string; type?: string }) =>
    http.get<ApiResponse<{ notifications: Notification[]; meta?: { total: number; unread: number } }>>(
      '/communications/notifications/',
      { params }
    ),

  getUnreadCount: () =>
    http.get<ApiResponse<{ unread_count: number }>>('/communications/notifications/unread-count/'),

  markRead: (id: string) =>
    http.post<ApiResponse<{ notification: Notification }>>(`/communications/notifications/${id}/mark-read/`),

  markAllRead: () =>
    http.post<ApiResponse<{ updated_count: number }>>('/communications/notifications/mark-all-read/'),
}
