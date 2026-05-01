/**
 * Communications WebSocket Service
 * ==================================
 * Clean abstraction over WebSocket connections for real-time communication.
 * Supports notification stream and per-thread message stream.
 *
 * When backend WebSocket is live (Django Channels), connects to:
 *   ws://.../ws/notifications/
 *   ws://.../ws/threads/{threadId}/
 *
 * Falls back gracefully when backend WS is not available.
 * Event handlers are decoupled — callers register handlers and the service
 * routes events to them.
 */

import type { RealtimeEvent } from '@/types/communications'

type EventHandler = (event: RealtimeEvent) => void

const WS_BASE =
  typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`
    : 'ws://localhost:8000/ws'

const RECONNECT_DELAY = 3000
const MAX_RECONNECT_ATTEMPTS = 5

class SocketConnection {
  private ws: WebSocket | null = null
  private handlers: Set<EventHandler> = new Set()
  private reconnectAttempts = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private shouldReconnect = true
  private url: string

  constructor(url: string) {
    this.url = url
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return
    try {
      this.ws = new WebSocket(this.url)
      this.ws.onopen = () => {
        this.reconnectAttempts = 0
      }
      this.ws.onmessage = (event) => {
        try {
          const data: RealtimeEvent = JSON.parse(event.data)
          this.handlers.forEach((h) => h(data))
        } catch {
          // ignore malformed messages
        }
      }
      this.ws.onclose = () => {
        if (this.shouldReconnect && this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          this.reconnectAttempts++
          this.reconnectTimer = setTimeout(() => this.connect(), RECONNECT_DELAY)
        }
      }
      this.ws.onerror = () => {
        this.ws?.close()
      }
    } catch {
      // WebSocket not available
    }
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.ws?.close()
    this.ws = null
  }

  addHandler(handler: EventHandler) {
    this.handlers.add(handler)
  }

  removeHandler(handler: EventHandler) {
    this.handlers.delete(handler)
  }

  send(data: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

// ─── Notification Socket ──────────────────────────────────────────────────────

let notificationSocket: SocketConnection | null = null

export function connectNotificationsSocket(onEvent: EventHandler): () => void {
  if (!notificationSocket) {
    notificationSocket = new SocketConnection(`${WS_BASE}/notifications/`)
    notificationSocket.connect()
  }
  notificationSocket.addHandler(onEvent)
  return () => {
    notificationSocket?.removeHandler(onEvent)
  }
}

// ─── Thread Socket ─────────────────────────────────────────────────────────────

const threadSockets = new Map<string, SocketConnection>()

export function connectThreadSocket(threadId: string, onEvent: EventHandler): () => void {
  if (!threadSockets.has(threadId)) {
    const sock = new SocketConnection(`${WS_BASE}/threads/${threadId}/`)
    sock.connect()
    threadSockets.set(threadId, sock)
  }
  const sock = threadSockets.get(threadId)!
  sock.addHandler(onEvent)
  return () => {
    sock.removeHandler(onEvent)
    // Auto-close if no more listeners
    if ((sock as unknown as { handlers: Set<unknown> })['handlers']?.size === 0) {
      sock.disconnect()
      threadSockets.delete(threadId)
    }
  }
}

export function disconnectAllSockets() {
  notificationSocket?.disconnect()
  notificationSocket = null
  threadSockets.forEach((sock) => sock.disconnect())
  threadSockets.clear()
}

// ─── Unified event handler ────────────────────────────────────────────────────

export function handleIncomingEvent(event: RealtimeEvent, callbacks: {
  onMessageNew?: (threadId: string, messageId: string) => void
  onNotificationNew?: (notificationId: string) => void
  onUnreadCountUpdated?: (count: number) => void
  onThreadUpdated?: (threadId: string) => void
}) {
  switch (event.type) {
    case 'message.new':
      callbacks.onMessageNew?.(event.thread_id, event.message_id)
      break
    case 'notification.new':
      callbacks.onNotificationNew?.(event.notification_id)
      break
    case 'notification.unread_count.updated':
      callbacks.onUnreadCountUpdated?.(event.unread_count)
      break
    case 'thread.updated':
      callbacks.onThreadUpdated?.(event.thread_id)
      break
  }
}
