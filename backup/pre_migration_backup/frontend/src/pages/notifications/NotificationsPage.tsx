import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useApiQuery } from '@/hooks/useApiQuery'
import { notificationsApi } from '@/api/notifications'
import { useCommunicationsStore } from '@/store/communicationsStore'
import { NotificationList } from '@/components/notifications/NotificationList'
import type { Notification } from '@/types/communications'

export default function NotificationsPage() {
  const queryClient = useQueryClient()
  const notificationFilter = useCommunicationsStore((s) => s.notificationFilter)
  const setNotificationFilter = useCommunicationsStore((s) => s.setNotificationFilter)
  const setUnreadNotificationCount = useCommunicationsStore((s) => s.setUnreadNotificationCount)

  const { data, isLoading } = useApiQuery(
    ['notifications', 'all'],
    () => notificationsApi.list(),
    { staleTime: 30_000 },
  )

  const notifications: Notification[] =
    (data as { notifications: Notification[] } | undefined)?.notifications ?? []
  const unreadCount = notifications.filter((n) => !n.is_read).length

  const handleMarkRead = useCallback(async (id: string) => {
    try {
      await notificationsApi.markRead(id)
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      setUnreadNotificationCount(Math.max(0, unreadCount - 1))
    } catch {
      // silently fail — not critical
    }
  }, [queryClient, unreadCount, setUnreadNotificationCount])

  const handleMarkAllRead = useCallback(async () => {
    try {
      await notificationsApi.markAllRead()
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      setUnreadNotificationCount(0)
    } catch {
      // silently fail
    }
  }, [queryClient, setUnreadNotificationCount])

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <NotificationList
          notifications={notifications}
          isLoading={isLoading}
          filter={notificationFilter}
          unreadCount={unreadCount}
          onFilterChange={setNotificationFilter}
          onMarkRead={handleMarkRead}
          onMarkAllRead={handleMarkAllRead}
        />
      </div>
    </div>
  )
}
