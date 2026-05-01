import dayjs from 'dayjs'
import { Info } from 'lucide-react'
import { cn } from '@/utils/cn'
import type { Message } from '@/types/communications'

interface Props {
  message: Message
  className?: string
}

export function SystemMessageRow({ message, className }: Props) {
  const body = message.body || message.content || ''
  const time = dayjs(message.sent_at).format('HH:mm')

  return (
    <div className={cn('flex items-center justify-center gap-2 py-1.5 px-4', className)}>
      <div className="h-px flex-1 bg-slate-200" />
      <div className="flex items-center gap-1.5 bg-slate-100 rounded-full px-3 py-1 max-w-[80%]">
        <Info className="h-3 w-3 text-slate-400 flex-shrink-0" />
        <span className="text-[11px] text-slate-500 text-center leading-snug">{body}</span>
        <span className="text-[10px] text-slate-400 tabular-nums flex-shrink-0">{time}</span>
      </div>
      <div className="h-px flex-1 bg-slate-200" />
    </div>
  )
}
