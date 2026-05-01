import { cn } from '@/utils/cn'
import { UnreadCounterBadge } from './UnreadCounterBadge'
import { EntityContextChip } from './EntityContextChip'
import { RelativeTimeText } from './RelativeTimeText'
import { THREAD_TYPE_LABELS } from '@/types/communications'
import type { MessageThread } from '@/types/communications'
import { MessageSquare, Lock, Globe } from 'lucide-react'

interface Props {
  thread: MessageThread
  isActive: boolean
  onClick: () => void
}

export function ThreadListItem({ thread, isActive, onClick }: Props) {
  const hasUnread = thread.unread_count > 0

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left px-4 py-3 border-b border-slate-100 transition-all group',
        'relative flex flex-col gap-1 focus:outline-none',
        isActive
          ? 'bg-indigo-50 border-l-[3px] border-l-indigo-500'
          : 'bg-white border-l-[3px] border-l-transparent hover:bg-slate-50',
      )}
    >
      {/* Top row: name + time */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className={cn(
            'text-[13px] truncate max-w-[150px]',
            hasUnread ? 'font-semibold text-slate-900' : 'font-medium text-slate-700',
          )}>
            {thread.subject || 'Untitled'}
          </span>
          {thread.is_internal
            ? <Lock className="h-3 w-3 text-slate-400 flex-shrink-0" />
            : <Globe className="h-3 w-3 text-slate-400 flex-shrink-0" />
          }
        </div>
        <RelativeTimeText datetime={thread.last_message_at} short className="flex-shrink-0" />
      </div>

      {/* Preview */}
      <p className={cn(
        'text-xs line-clamp-1',
        hasUnread ? 'text-slate-700' : 'text-slate-500',
      )}>
        {thread.last_message_preview || 'No messages yet'}
      </p>

      {/* Bottom row: entity chip + unread badge */}
      <div className="flex items-center justify-between mt-0.5">
        <div className="flex items-center gap-1.5">
          {thread.related_entity_type && (
            <EntityContextChip entityType={thread.related_entity_type} entityId={thread.related_entity_id} />
          )}
          {!thread.related_entity_type && (
            <span className="text-[10px] text-slate-400 uppercase tracking-wide">
              {THREAD_TYPE_LABELS[thread.thread_type] || 'General'}
            </span>
          )}
        </div>
        {hasUnread && <UnreadCounterBadge count={thread.unread_count} />}
      </div>
    </button>
  )
}
