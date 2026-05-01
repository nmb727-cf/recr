import { Button, Avatar, Tooltip } from 'antd'
import { Users, Lock, Globe, MoreHorizontal, ExternalLink, BellOff, CheckCheck } from 'lucide-react'
import { EntityContextChip } from './EntityContextChip'
import type { MessageThread } from '@/types/communications'

interface Props {
  thread: MessageThread
  onMarkRead?: () => void
}

export function ThreadHeader({ thread, onMarkRead }: Props) {
  const participantCount = thread.participant_ids?.length || thread.participants?.length || 0

  return (
    <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100 bg-white flex-shrink-0">
      <div className="flex flex-col min-w-0">
        <div className="flex items-center gap-2">
          {thread.is_internal
            ? <Lock className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
            : <Globe className="h-3.5 w-3.5 text-indigo-500 flex-shrink-0" />
          }
          <h2 className="text-sm font-semibold text-slate-900 truncate max-w-[300px]">
            {thread.subject || 'Conversation'}
          </h2>
          {thread.related_entity_type && (
            <EntityContextChip
              entityType={thread.related_entity_type}
              entityId={thread.related_entity_id}
              clickable
            />
          )}
        </div>

        <div className="flex items-center gap-2 mt-1">
          <Users className="h-3 w-3 text-slate-400" />
          <div className="flex -space-x-1.5">
            {Array.from({ length: Math.min(participantCount, 4) }).map((_, i) => (
              <Avatar
                key={i}
                size={18}
                className="ring-2 ring-white bg-indigo-200 text-indigo-700 text-[9px] font-semibold"
              >
                {String.fromCharCode(65 + i)}
              </Avatar>
            ))}
          </div>
          <span className="text-[11px] text-slate-500">
            {participantCount} participant{participantCount !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-1">
        {onMarkRead && (
          <Tooltip title="Mark all read">
            <Button
              type="text"
              size="small"
              icon={<CheckCheck className="h-4 w-4 text-slate-500" />}
              onClick={onMarkRead}
              className="flex items-center justify-center"
            />
          </Tooltip>
        )}
        <Tooltip title="Mute thread">
          <Button
            type="text"
            size="small"
            icon={<BellOff className="h-4 w-4 text-slate-500" />}
            className="flex items-center justify-center"
          />
        </Tooltip>
        <Tooltip title="More options">
          <Button
            type="text"
            size="small"
            icon={<MoreHorizontal className="h-4 w-4 text-slate-500" />}
            className="flex items-center justify-center"
          />
        </Tooltip>
      </div>
    </div>
  )
}
