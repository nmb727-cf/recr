import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { Button, Tooltip } from 'antd'
import { Check, ExternalLink } from 'lucide-react'
import { cn } from '@/utils/cn'
import { SeverityBadge } from '@/components/communications/SeverityBadge'
import type { Notification } from '@/types/communications'
import { ENTITY_ROUTES } from '@/types/communications'

dayjs.extend(relativeTime)

interface Props {
  notification: Notification
  onMarkRead?: (id: string) => void
}

export function NotificationItem({ notification, onMarkRead }: Props) {
  const navigate = useNavigate()
  const isUnread = !notification.is_read

  const handleClick = () => {
    if (notification.action_url) {
      navigate(notification.action_url)
    } else if (notification.related_entity_type && notification.related_entity_id) {
      const base = ENTITY_ROUTES[notification.related_entity_type]
      if (base) navigate(`${base}/${notification.related_entity_id}`)
    }
    if (isUnread) onMarkRead?.(notification.id)
  }

  return (
    <div
      className={cn(
        'flex items-start gap-3 px-4 py-3 border-b border-slate-100 group transition-colors',
        isUnread ? 'bg-indigo-50/50 hover:bg-indigo-50' : 'bg-white hover:bg-slate-50',
        (notification.action_url || notification.related_entity_id) && 'cursor-pointer',
      )}
      onClick={handleClick}
    >
      {/* Unread indicator */}
      <div className="flex-shrink-0 mt-1.5">
        {isUnread ? (
          <div className="w-2 h-2 rounded-full bg-indigo-500" />
        ) : (
          <div className="w-2 h-2" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className={cn(
            'text-sm leading-snug',
            isUnread ? 'font-semibold text-slate-900' : 'font-medium text-slate-700',
          )}>
            {notification.title}
          </p>
          <div className="flex items-center gap-1 flex-shrink-0 mt-0.5">
            <SeverityBadge severity={notification.severity} />
          </div>
        </div>

        {notification.body && (
          <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{notification.body}</p>
        )}

        <div className="flex items-center justify-between mt-1.5">
          <span className="text-[10px] text-slate-400 tabular-nums">
            {dayjs(notification.created_at).fromNow()}
          </span>

          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {notification.action_url && (
              <Tooltip title="Open">
                <Button
                  type="text"
                  size="small"
                  icon={<ExternalLink className="h-3 w-3 text-slate-400" />}
                  className="flex items-center justify-center h-5 w-5 min-w-0 p-0"
                  onClick={(e) => { e.stopPropagation(); navigate(notification.action_url!) }}
                />
              </Tooltip>
            )}
            {isUnread && (
              <Tooltip title="Mark as read">
                <Button
                  type="text"
                  size="small"
                  icon={<Check className="h-3 w-3 text-slate-400" />}
                  className="flex items-center justify-center h-5 w-5 min-w-0 p-0"
                  onClick={(e) => { e.stopPropagation(); onMarkRead?.(notification.id) }}
                />
              </Tooltip>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
