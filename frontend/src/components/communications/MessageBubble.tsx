import dayjs from 'dayjs'
import { Tooltip } from 'antd'
import { CheckCheck } from 'lucide-react'
import { cn } from '@/utils/cn'
import type { Message } from '@/types/communications'

interface Props {
  message: Message
  isOwn: boolean
  showSenderLabel?: boolean
}

export function MessageBubble({ message, isOwn, showSenderLabel }: Props) {
  const body = message.body || message.content || ''
  const time = dayjs(message.sent_at).format('HH:mm')
  const fullTime = dayjs(message.sent_at).format('MMM D, YYYY HH:mm')

  return (
    <div className={cn('flex', isOwn ? 'justify-end' : 'justify-start', 'mb-2')}>
      <div className={cn('max-w-[70%] flex flex-col', isOwn ? 'items-end' : 'items-start')}>
        {showSenderLabel && !isOwn && (
          <span className="text-[10px] text-slate-400 mb-0.5 px-1">
            {message.sender_id.slice(0, 8)}…
          </span>
        )}
        <div
          className={cn(
            'px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm',
            isOwn
              ? 'bg-indigo-600 text-white rounded-br-md'
              : 'bg-white text-slate-800 border border-slate-200 rounded-bl-md',
          )}
        >
          <p className="whitespace-pre-wrap break-words">{body}</p>
        </div>
        <Tooltip title={fullTime}>
          <div className={cn('flex items-center gap-1 mt-0.5 px-1', isOwn ? 'flex-row-reverse' : '')}>
            <span className="text-[10px] text-slate-400 tabular-nums">{time}</span>
            {isOwn && (
              <CheckCheck className={cn('h-3 w-3', message.is_read ? 'text-indigo-500' : 'text-slate-400')} />
            )}
          </div>
        </Tooltip>
      </div>
    </div>
  )
}
