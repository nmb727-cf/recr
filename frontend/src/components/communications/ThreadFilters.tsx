import { Input } from 'antd'
import { Search } from 'lucide-react'
import { cn } from '@/utils/cn'
import type { ThreadFilter } from '@/types/communications'

interface Props {
  filter: ThreadFilter
  onChange: (filter: Partial<ThreadFilter>) => void
  totalCount?: number
  unreadCount?: number
}

const TABS: { key: ThreadFilter['tab']; label: string }[] = [
  { key: 'all',      label: 'All' },
  { key: 'unread',   label: 'Unread' },
  { key: 'internal', label: 'Internal' },
  { key: 'external', label: 'External' },
  { key: 'archived', label: 'Archived' },
]

export function ThreadFilters({ filter, onChange, unreadCount }: Props) {
  return (
    <div className="border-b border-slate-100 bg-white">
      {/* Search */}
      <div className="px-4 pt-3 pb-2">
        <Input
          prefix={<Search className="h-3.5 w-3.5 text-slate-400" />}
          placeholder="Search conversations…"
          value={filter.search}
          onChange={(e) => onChange({ search: e.target.value })}
          allowClear
          size="small"
          className="rounded-lg border-slate-200 text-sm"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-0 overflow-x-auto no-scrollbar px-3 pb-0">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => onChange({ tab: tab.key })}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 text-xs font-medium whitespace-nowrap border-b-2 transition-all',
              filter.tab === tab.key
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300',
            )}
          >
            {tab.label}
            {tab.key === 'unread' && unreadCount != null && unreadCount > 0 && (
              <span className="rounded-full bg-indigo-600 text-white text-[10px] px-1.5 py-px leading-none">
                {unreadCount}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}
