// ─── Communication Hub Types ──────────────────────────────────────────────────

export type ThreadType =
  | 'internal'
  | 'company_agency'
  | 'recruiter_candidate'
  | 'company_candidate'
  | 'agency_candidate'
  | 'interview_coordination'
  | 'submission_context'
  | 'general'

export type ChannelType = 'in_app' | 'email' | 'whatsapp' | 'sms'

export type MessageType =
  | 'text'
  | 'system_event'
  | 'note'
  | 'attachment'
  | 'template_log'
  | 'file'
  | 'email'
  | 'sms'

export type NotificationSeverity = 'info' | 'medium' | 'high' | 'critical'

export type ParticipantType = 'owner' | 'member' | 'observer' | 'external'

export interface ThreadParticipant {
  id: string
  user_id: string
  participant_type: ParticipantType
  external_tenant_id?: string | null
  last_read_at?: string | null
  is_muted: boolean
  is_active: boolean
  created_at: string
}

export interface MessageThread {
  id: string
  tenant_id: string
  thread_type: ThreadType
  subject: string
  is_internal: boolean
  is_archived: boolean
  created_by?: string
  related_entity_type?: string
  related_entity_id?: string
  participant_ids: string[]
  participants: ThreadParticipant[]
  last_message_at?: string | null
  last_message_preview: string
  unread_count: number
  created_at: string
  updated_at: string
  metadata?: Record<string, unknown>
}

export interface Message {
  id: string
  tenant_id: string
  sender_id: string
  sender_tenant_id?: string
  message_type: MessageType
  channel_type: ChannelType
  body: string
  content?: string // legacy
  attachments_json: unknown[]
  attachments?: unknown[] // legacy
  related_entity_type?: string
  related_entity_id?: string
  is_read: boolean
  read_at?: string | null
  is_system_generated: boolean
  is_deleted: boolean
  sent_at: string
  delivered_at?: string | null
  metadata?: Record<string, unknown>
}

// ─── Notification Types ───────────────────────────────────────────────────────

export interface NotificationDelivery {
  id: string
  channel: 'in_app' | 'email' | 'whatsapp' | 'sms' | 'push'
  provider: string
  status: 'pending' | 'sent' | 'delivered' | 'failed' | 'skipped'
  attempted_at?: string | null
  delivered_at?: string | null
  failed_at?: string | null
  external_message_id?: string
  error_message?: string
}

export interface Notification {
  id: string
  tenant_id?: string | null
  user_id: string
  type: string
  notification_type?: string // legacy alias
  title: string
  body: string
  severity: NotificationSeverity
  action_url?: string
  is_read: boolean
  read_at?: string | null
  related_entity_type?: string
  related_entity_id?: string | null
  fallback_email_sent_at?: string | null
  escalation_level?: number
  expires_at?: string | null
  created_at: string
  updated_at?: string
  deliveries?: NotificationDelivery[]
  metadata?: Record<string, unknown>
}

export interface NotificationFilter {
  tab: 'all' | 'unread' | 'high' | 'messages' | 'workflow'
}

export interface ThreadFilter {
  tab: 'all' | 'unread' | 'internal' | 'external' | 'archived'
  search: string
  thread_type?: ThreadType
}

// ─── Realtime Events ──────────────────────────────────────────────────────────

export type RealtimeEvent =
  | { type: 'message.new'; thread_id: string; message_id: string }
  | { type: 'notification.new'; user_id: string; notification_id: string }
  | { type: 'notification.unread_count.updated'; user_id: string; unread_count: number }
  | { type: 'thread.updated'; thread_id: string }

// ─── Entity context (for chips/links) ─────────────────────────────────────────

export type EntityType =
  | 'candidate'
  | 'application'
  | 'job'
  | 'interview'
  | 'agency_submission'
  | 'offer'
  | 'agency_relationship'
  | 'general'

export const ENTITY_ROUTES: Record<string, string> = {
  candidate: '/candidates',
  application: '/pipeline',
  job: '/jobs',
  interview: '/interviews',
  offer: '/pipeline',
  agency_submission: '/agencies',
}

export const ENTITY_LABELS: Record<string, string> = {
  candidate: 'Candidate',
  application: 'Application',
  job: 'Job',
  interview: 'Interview',
  offer: 'Offer',
  agency_submission: 'Submission',
  agency_relationship: 'Agency',
  general: 'General',
}

export const THREAD_TYPE_LABELS: Record<ThreadType, string> = {
  internal: 'Internal',
  company_agency: 'Agency',
  recruiter_candidate: 'Candidate',
  company_candidate: 'Candidate',
  agency_candidate: 'Candidate',
  interview_coordination: 'Interview',
  submission_context: 'Submission',
  general: 'General',
}
