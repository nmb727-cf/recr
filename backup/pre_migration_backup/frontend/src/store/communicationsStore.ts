import { create } from 'zustand'
import type { ThreadFilter, NotificationFilter } from '@/types/communications'

interface CommunicationsState {
  // Active thread
  activeThreadId: string | null
  setActiveThreadId: (id: string | null) => void

  // Thread filters
  threadFilter: ThreadFilter
  setThreadFilter: (filter: Partial<ThreadFilter>) => void

  // Notification filters
  notificationFilter: NotificationFilter
  setNotificationFilter: (filter: Partial<NotificationFilter>) => void

  // Global unread counts
  unreadNotificationCount: number
  setUnreadNotificationCount: (count: number) => void

  unreadThreadCount: number
  setUnreadThreadCount: (count: number) => void

  // Composer
  composerText: string
  setComposerText: (text: string) => void
  clearComposer: () => void

  // Realtime: tracks which thread IDs have pending new messages
  incomingMessageThreadIds: Set<string>
  markThreadHasIncoming: (threadId: string) => void
  clearThreadIncoming: (threadId: string) => void
}

export const useCommunicationsStore = create<CommunicationsState>((set) => ({
  activeThreadId: null,
  setActiveThreadId: (id) => set({ activeThreadId: id }),

  threadFilter: { tab: 'all', search: '' },
  setThreadFilter: (filter) =>
    set((state) => ({ threadFilter: { ...state.threadFilter, ...filter } })),

  notificationFilter: { tab: 'all' },
  setNotificationFilter: (filter) =>
    set((state) => ({ notificationFilter: { ...state.notificationFilter, ...filter } })),

  unreadNotificationCount: 0,
  setUnreadNotificationCount: (count) => set({ unreadNotificationCount: count }),

  unreadThreadCount: 0,
  setUnreadThreadCount: (count) => set({ unreadThreadCount: count }),

  composerText: '',
  setComposerText: (text) => set({ composerText: text }),
  clearComposer: () => set({ composerText: '' }),

  incomingMessageThreadIds: new Set(),
  markThreadHasIncoming: (threadId) =>
    set((state) => ({
      incomingMessageThreadIds: new Set([...state.incomingMessageThreadIds, threadId]),
    })),
  clearThreadIncoming: (threadId) =>
    set((state) => {
      const s = new Set(state.incomingMessageThreadIds)
      s.delete(threadId)
      return { incomingMessageThreadIds: s }
    }),
}))
