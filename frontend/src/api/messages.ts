import http from '@/utils/http'
import type { ApiResponse, MessageThread, Message } from '@/types'

export const messagesApi = {
  listThreads: () =>
    http.get<ApiResponse<{ threads: MessageThread[] }>>('/messages/threads/'),

  getThreadMessages: (threadId: string) =>
    http.get<ApiResponse<{ messages: Message[] }>>(`/messages/threads/${threadId}/`),

  createThread: (data: { recipient_id: string; subject: string; message: string }) =>
    http.post<ApiResponse<{ thread: MessageThread }>>('/messages/threads/', data),

  replyToThread: (threadId: string, message: string) =>
    http.post<ApiResponse<{ message: Message }>>(`/messages/threads/${threadId}/reply/`, { message }),
}
