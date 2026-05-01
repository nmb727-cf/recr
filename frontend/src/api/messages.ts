import http from '@/utils/http'
import type { ApiResponse } from '@/types'
import type { MessageThread, Message } from '@/types/communications'

export interface CreateThreadPayload {
  subject?: string
  thread_type?: string
  is_internal?: boolean
  related_entity_type?: string
  related_entity_id?: string
  participant_user_ids?: string[]
  message: string
}

export interface SendMessagePayload {
  message?: string
  body?: string
  message_type?: string
  attachments?: unknown[]
}

export const messagesApi = {
  listThreads: (params?: {
    thread_type?: string
    related_entity_type?: string
    related_entity_id?: string
    include_archived?: boolean
  }) =>
    http.get<ApiResponse<{ threads: MessageThread[] }>>('/communications/messages/threads/', { params }),

  getThread: (threadId: string) =>
    http.get<ApiResponse<{ thread: MessageThread }>>(`/communications/messages/threads/${threadId}/`),

  getThreadMessages: (threadId: string) =>
    http.get<ApiResponse<{ messages: Message[] }>>(`/communications/messages/threads/${threadId}/messages/`),

  createThread: (data: CreateThreadPayload) =>
    http.post<ApiResponse<{ thread: MessageThread; message: Message }>>('/communications/messages/threads/', data),

  sendMessage: (threadId: string, data: SendMessagePayload) =>
    http.post<ApiResponse<{ message: Message }>>(`/communications/messages/threads/${threadId}/messages/`, data),

  // Legacy compat
  replyToThread: (threadId: string, message: string) =>
    http.post<ApiResponse<{ message: Message }>>(`/communications/messages/threads/${threadId}/reply/`, { message }),

  markThreadRead: (threadId: string) =>
    http.post<ApiResponse<null>>(`/communications/messages/threads/${threadId}/mark-read/`),
}
