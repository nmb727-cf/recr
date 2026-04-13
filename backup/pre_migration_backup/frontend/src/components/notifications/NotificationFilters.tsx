import { cn } from '@/utils/cn'
import type { NotificationFilter } from '@/types/communications'

interface Props {
  filter: NotificationFilter
  onChange: (f: Partial<NotificationFilter>) => void
  unreadCount?: number
}

const TABS: { key: NotificationFilter['tab']; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'unread', label: 'Unread' },
  { key: 'high', label: 'High Priority' },
  { key: 'messages', label: 'Messages' },
  { key: 'workflow', label: 'Workflow' },
]

export function NotificationFilters({ filter, onChange, unreadCount }: Props) {
  return (
    <div className="flex gap-0 overflow-x-auto no-scrollbar border-b border-slate-100 bg-white px-3">
      {TABS.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange({ tab: tab.key })}
          className={cn(
            'flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium whitespace-nowrap border-b-2 transition-all',
            filter.tab === tab.key
              ? 'border-indigo-500 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300',
          )}
        >
          {tab.label}
          {tab.key === 'unread' && unreadCount != null && unreadCount > 0 && (
            <span className="rounded-full bg-indigo-600 text-white text-[10px] px-1.5 py-px leading-none">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>
      ))}
    </div>
  )
}
