import { useMemo } from 'react'
import { Spin, Button } from 'antd'
import { Bell } from 'lucide-react'
import { NotificationItem } from './NotificationItem'
import { NotificationFilters } from './NotificationFilters'
import type { Notification, NotificationFilter } from '@/types/communications'

interface Props {
  notifications: Notification[]
  isLoading: boolean
  filter: NotificationFilter
  unreadCount: number
  onFilterChange: (f: Partial<NotificationFilter>) => void
  onMarkRead: (id: string) => void
  onMarkAllRead: () => void
}

export function NotificationList({
  notifications,
  isLoading,
  filter,
  unreadCount,
  onFilterChange,
  onMarkRead,
  onMarkAllRead,
}: Props) {
  const filtered = useMemo(() => {
    switch (filter.tab) {
      case 'unread': return notifications.filter((n) => !n.is_read)
      case 'high': return notifications.filter((n) => n.severity === 'high' || n.severity === 'critical')
      case 'messages': return notifications.filter((n) => n.type?.includes('message') || n.type?.includes('thread'))
      case 'workflow': return notifications.filter((n) =>
        n.type?.includes('application') || n.type?.includes('interview') || n.type?.includes('offer'),
      )
      default: return notifications
    }
  }, [notifications, filter.tab])

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 flex-shrink-0">
        <h2 className="text-sm font-semibold text-slate-900">Notifications</h2>
        {unreadCount > 0 && (
          <Button type="text" size="small" onClick={onMarkAllRead} className="text-xs text-indigo-600 hover:text-indigo-700 px-2">
            Mark all read
          </Button>
        )}
      </div>

      <NotificationFilters filter={filter} onChange={onFilterChange} unreadCount={unreadCount} />

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Spin size="small" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
              <Bell className="h-5 w-5 text-slate-400" />
            </div>
            <p className="text-sm font-medium text-slate-700">All caught up</p>
            <p className="text-xs text-slate-500 mt-1">No notifications to show</p>
          </div>
        ) : (
          filtered.map((n) => (
            <NotificationItem key={n.id} notification={n} onMarkRead={onMarkRead} />
          ))
        )}
      </div>
    </div>
  )
}
