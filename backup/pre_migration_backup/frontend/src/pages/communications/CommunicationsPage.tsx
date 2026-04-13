import { useState, useCallback, useEffect } from 'react'
import { Button, Tooltip, message as antMessage } from 'antd'
import { Plus } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { useApiQuery } from '@/hooks/useApiQuery'
import { useAuth } from '@/hooks/useAuth'
import { messagesApi } from '@/api/messages'
import { useCommunicationsStore } from '@/store/communicationsStore'
import { ThreadList } from '@/components/communications/ThreadList'
import { ThreadHeader } from '@/components/communications/ThreadHeader'
import { MessageTimeline } from '@/components/communications/MessageTimeline'
import { MessageComposer } from '@/components/communications/MessageComposer'
import { EmptyThreadState } from '@/components/communications/EmptyThreadState'
import { NewThreadDrawer } from '@/components/communications/NewThreadDrawer'
import type { MessageThread, Message } from '@/types/communications'

export default function CommunicationsPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [newThreadOpen, setNewThreadOpen] = useState(false)
  const [isSending, setIsSending] = useState(false)

  const activeThreadId = useCommunicationsStore((s) => s.activeThreadId)
  const setActiveThreadId = useCommunicationsStore((s) => s.setActiveThreadId)
  const threadFilter = useCommunicationsStore((s) => s.threadFilter)
  const setThreadFilter = useCommunicationsStore((s) => s.setThreadFilter)
  const setUnreadThreadCount = useCommunicationsStore((s) => s.setUnreadThreadCount)

  // ── Thread list ───────────────────────────────────────────────────────────
  const { data: threadsData, isLoading: threadsLoading } = useApiQuery(
    ['threads'],
    () => messagesApi.listThreads(),
  )
  const threads: MessageThread[] = (threadsData as { threads: MessageThread[] } | undefined)?.threads ?? []

  // Sync unread thread count to store for header badge
  useEffect(() => {
    const count = threads.filter((t) => t.unread_count > 0).length
    setUnreadThreadCount(count)
  }, [threads, setUnreadThreadCount])

  // ── Active thread ─────────────────────────────────────────────────────────
  const { data: threadData } = useApiQuery(
    ['thread', activeThreadId],
    () => messagesApi.getThread(activeThreadId!),
    { enabled: !!activeThreadId },
  )
  const activeThread: MessageThread | undefined = (threadData as { thread: MessageThread } | undefined)?.thread

  // ── Messages ──────────────────────────────────────────────────────────────
  const { data: messagesData, isLoading: messagesLoading, refetch: refetchMessages } = useApiQuery(
    ['thread-messages', activeThreadId],
    () => messagesApi.getThreadMessages(activeThreadId!),
    { enabled: !!activeThreadId },
  )
  const messages: Message[] = (messagesData as { messages: Message[] } | undefined)?.messages ?? []

  // ── Actions ───────────────────────────────────────────────────────────────
  const handleSelectThread = useCallback((threadId: string) => {
    setActiveThreadId(threadId)
  }, [setActiveThreadId])

  const handleSend = useCallback(async (text: string) => {
    if (!activeThreadId) return
    setIsSending(true)
    try {
      await messagesApi.sendMessage(activeThreadId, { body: text })
      refetchMessages()
      queryClient.invalidateQueries({ queryKey: ['threads'] })
    } catch {
      antMessage.error('Failed to send message')
    } finally {
      setIsSending(false)
    }
  }, [activeThreadId, refetchMessages, queryClient])

  const handleMarkRead = useCallback(async () => {
    if (!activeThreadId) return
    try {
      await messagesApi.markThreadRead(activeThreadId)
      queryClient.invalidateQueries({ queryKey: ['threads'] })
    } catch {
      antMessage.error('Failed to mark as read')
    }
  }, [activeThreadId, queryClient])

  const handleThreadCreated = useCallback((threadId: string) => {
    setNewThreadOpen(false)
    queryClient.invalidateQueries({ queryKey: ['threads'] })
    setActiveThreadId(threadId)
  }, [queryClient, setActiveThreadId])

  const hasMultipleParticipants = (activeThread?.participants?.length ?? activeThread?.participant_ids?.length ?? 0) > 2

  return (
    <div className="flex h-[calc(100vh-56px)] -mx-6 -my-6 overflow-hidden bg-slate-50">
      {/* ── Thread List Panel ──────────────────────────────────────────────── */}
      <div className="w-[300px] flex-shrink-0 border-r border-slate-200 flex flex-col bg-white">
        {/* Panel header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 flex-shrink-0">
          <h1 className="text-sm font-semibold text-slate-900">Messages</h1>
          <Tooltip title="New conversation">
            <Button
              type="primary"
              size="small"
              shape="circle"
              icon={<Plus className="h-3.5 w-3.5" />}
              onClick={() => setNewThreadOpen(true)}
              className="flex items-center justify-center"
            />
          </Tooltip>
        </div>

        <ThreadList
          threads={threads}
          isLoading={threadsLoading}
          activeThreadId={activeThreadId}
          filter={threadFilter}
          onFilterChange={setThreadFilter}
          onSelect={handleSelectThread}
        />
      </div>

      {/* ── Thread View Panel ──────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {activeThread ? (
          <>
            <ThreadHeader thread={activeThread} onMarkRead={handleMarkRead} />
            <MessageTimeline
              messages={messages}
              currentUserId={user?.id ?? ''}
              isLoading={messagesLoading}
              hasMultipleParticipants={hasMultipleParticipants}
            />
            <MessageComposer
              threadId={activeThreadId!}
              onSend={handleSend}
              isSending={isSending}
            />
          </>
        ) : (
          <EmptyThreadState onNewThread={() => setNewThreadOpen(true)} />
        )}
      </div>

      <NewThreadDrawer
        open={newThreadOpen}
        onClose={() => setNewThreadOpen(false)}
        onCreated={handleThreadCreated}
      />
    </div>
  )
}
