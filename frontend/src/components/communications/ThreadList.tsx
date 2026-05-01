import { useMemo } from 'react'
import { Spin } from 'antd'
import { MessageSquare } from 'lucide-react'
import { ThreadListItem } from './ThreadListItem'
import { ThreadFilters } from './ThreadFilters'
import type { MessageThread, ThreadFilter } from '@/types/communications'

interface Props {
  threads: MessageThread[]
  isLoading: boolean
  activeThreadId: string | null
  filter: ThreadFilter
  onFilterChange: (f: Partial<ThreadFilter>) => void
  onSelect: (threadId: string) => void
}

export function ThreadList({ threads, isLoading, activeThreadId, filter, onFilterChange, onSelect }: Props) {
  const unreadCount = threads.filter((t) => t.unread_count > 0).length

  const filtered = useMemo(() => {
    let list = threads

    // Tab filter
    if (filter.tab === 'unread') list = list.filter((t) => t.unread_count > 0)
    else if (filter.tab === 'internal') list = list.filter((t) => t.is_internal)
    else if (filter.tab === 'external') list = list.filter((t) => !t.is_internal)
    else if (filter.tab === 'archived') list = list.filter((t) => t.is_archived)
    else list = list.filter((t) => !t.is_archived)

    // Search
    if (filter.search.trim()) {
      const q = filter.search.toLowerCase()
      list = list.filter(
        (t) =>
          (t.subject || '').toLowerCase().includes(q) ||
          (t.last_message_preview || '').toLowerCase().includes(q),
      )
    }

    return list
  }, [threads, filter])

  return (
    <div className="flex flex-col h-full bg-white">
      <ThreadFilters filter={filter} onChange={onFilterChange} unreadCount={unreadCount} />

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Spin size="small" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
              <MessageSquare className="h-5 w-5 text-slate-400" />
            </div>
            <p className="text-sm font-medium text-slate-700">No conversations</p>
            <p className="text-xs text-slate-500 mt-1">
              {filter.search ? 'No results match your search' : 'Start a new conversation to get going'}
            </p>
          </div>
        ) : (
          filtered.map((thread) => (
            <ThreadListItem
              key={thread.id}
              thread={thread}
              isActive={activeThreadId === thread.id}
              onClick={() => onSelect(thread.id)}
            />
          ))
        )}
      </div>
    </div>
  )
}
