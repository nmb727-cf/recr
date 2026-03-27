import http from '@/utils/http'
import type { ApiResponse, MessageThread, Message } from '@/types'

export const messagesApi = {
  listThreads: () =>
    http.get<ApiResponse<{ threads: MessageThread[] }>>('/communications/messages/threads/'),

  getThreadMessages: (threadId: string) =>
    http.get<ApiResponse<{ messages: Message[] }>>(`/communications/messages/threads/${threadId}/`),

  createThread: (data: { recipient_id: string; subject: string; message: string }) =>
    http.post<ApiResponse<{ thread: MessageThread }>>('/communications/messages/threads/', data),

  replyToThread: (threadId: string, message: string) =>
    http.post<ApiResponse<{ message: Message }>>(`/communications/messages/threads/${threadId}/reply/`, { message }),
}
