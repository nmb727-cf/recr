import { useEffect, useRef } from 'react'
import { Spin } from 'antd'
import { MessageBubble } from './MessageBubble'
import { SystemMessageRow } from './SystemMessageRow'
import type { Message } from '@/types/communications'

interface Props {
  messages: Message[]
  currentUserId: string
  isLoading?: boolean
  hasMultipleParticipants?: boolean
}

function dateSeparator(date: string) {
  const d = new Date(date)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)

  if (d.toDateString() === today.toDateString()) return 'Today'
  if (d.toDateString() === yesterday.toDateString()) return 'Yesterday'
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function MessageTimeline({ messages, currentUserId, isLoading, hasMultipleParticipants }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Spin size="small" />
      </div>
    )
  }

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-12 px-6 text-center">
        <p className="text-sm text-slate-500">No messages yet. Start the conversation.</p>
      </div>
    )
  }

  let lastDate = ''

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-0.5">
      {messages.map((msg) => {
        const msgDate = msg.sent_at ? msg.sent_at.split('T')[0] : ''
        const showDate = msgDate !== lastDate
        lastDate = msgDate

        if (msg.is_system_generated) {
          return (
            <div key={msg.id}>
              {showDate && (
                <DateSeparator label={dateSeparator(msg.sent_at)} />
              )}
              <SystemMessageRow message={msg} />
            </div>
          )
        }

        return (
          <div key={msg.id}>
            {showDate && (
              <DateSeparator label={dateSeparator(msg.sent_at)} />
            )}
            <MessageBubble
              message={msg}
              isOwn={msg.sender_id === currentUserId}
              showSenderLabel={hasMultipleParticipants}
            />
          </div>
        )
      })}
      <div ref={bottomRef} />
    </div>
  )
}

function DateSeparator({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 py-3">
      <div className="h-px flex-1 bg-slate-200" />
      <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider px-1">{label}</span>
      <div className="h-px flex-1 bg-slate-200" />
    </div>
  )
}
