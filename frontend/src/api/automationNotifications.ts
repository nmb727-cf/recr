import http from '@/utils/http'
import type { ApiResponse } from '@/types'

// ─── Types ────────────────────────────────────────────────────────────────────

export type NotificationChannel = 'email' | 'whatsapp' | 'in_app' | 'sms' | 'push'
export type RecipientType       = 'candidate' | 'assigned_recruiter' | 'hiring_manager' | 'recruiter_manager' | 'agency_contact' | 'custom_user' | 'workflow_owner'
export type DeliveryStatus      = 'queued' | 'sent' | 'delivered' | 'failed' | 'skipped' | 'throttled' | 'deduplicated'
export type EscalationStatus    = 'pending' | 'sent' | 'resolved' | 'cancelled'
export type InsightType         = 'high_failure_rate' | 'duplicate_risk' | 'channel_underperforming' | 'escalation_spike' | 'candidate_non_response_pattern'

export interface NotificationRule {
  id: string
  tenant_id: string
  workflow_id: string
  action_node_id: string
  notification_event: string
  recipient_type: RecipientType
  channel: NotificationChannel
  template_id: string | null
  fallback_channels: NotificationChannel[]
  send_delay_minutes: number
  throttle_window_minutes: number
  dedupe_key_template: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface NotificationDelivery {
  id: string
  tenant_id: string
  execution_id: string | null
  workflow_id: string | null
  notification_rule: string | null
  recipient_user_id: string | null
  recipient_email: string
  channel: NotificationChannel
  status: DeliveryStatus
  subject: string
  dedupe_key: string
  sent_at: string | null
  delivered_at: string | null
  failed_at: string | null
  retry_count: number
  failure_reason: string
  created_at: string
}

export interface NotificationPreference {
  id: string
  tenant_id: string
  user_id: string
  notification_type: string
  preferred_channels: NotificationChannel[]
  quiet_hours_start: string | null
  quiet_hours_end: string | null
  allow_escalation_override: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface EscalationNotification {
  id: string
  tenant_id: string
  workflow_id: string
  execution_id: string | null
  escalation_level: number
  trigger_reason: string
  target_recipient_type: RecipientType
  channel: NotificationChannel
  status: EscalationStatus
  sent_at: string | null
  created_at: string
}

export interface NotificationInsight {
  id: string
  tenant_id: string
  workflow_id: string | null
  insight_type: InsightType
  title: string
  description: string
  metric_value: number
  created_at: string
}

export interface ChannelHealth {
  total: number
  sent: number
  failed: number
  fallback_used: number
  delivery_rate: number
  failure_rate: number
}

export type ChannelHealthMap = Record<NotificationChannel, ChannelHealth>

export interface RuleWritePayload {
  workflow_id: string
  action_node_id?: string
  notification_event: string
  recipient_type: RecipientType
  channel: NotificationChannel
  template_id?: string | null
  fallback_channels?: NotificationChannel[]
  send_delay_minutes?: number
  throttle_window_minutes?: number
  dedupe_key_template?: string
  is_active?: boolean
}

export interface DeliveryFilterParams {
  workflow_id?: string
  channel?: NotificationChannel
  status?: DeliveryStatus
  limit?: number
  offset?: number
}

// ─── API client ───────────────────────────────────────────────────────────────

export const automationNotificationsApi = {
  // Rules
  listRules: (params?: { workflow_id?: string }) =>
    http.get<ApiResponse<{ rules: NotificationRule[] }>>('/workflow-notifications/rules/', { params }),

  createRule: (data: RuleWritePayload) =>
    http.post<ApiResponse<{ rule: NotificationRule }>>('/workflow-notifications/rules/', data),

  getRule: (id: string) =>
    http.get<ApiResponse<{ rule: NotificationRule }>>(`/workflow-notifications/rules/${id}/`),

  updateRule: (id: string, data: Partial<RuleWritePayload>) =>
    http.put<ApiResponse<{ rule: NotificationRule }>>(`/workflow-notifications/rules/${id}/`, data),

  deleteRule: (id: string) =>
    http.delete<ApiResponse<Record<string, never>>>(`/workflow-notifications/rules/${id}/`),

  // Deliveries
  listDeliveries: (params?: DeliveryFilterParams) =>
    http.get<ApiResponse<{ deliveries: NotificationDelivery[]; meta: Record<string, number> }>>('/workflow-notifications/deliveries/', { params }),

  retryDelivery: (deliveryId: string) =>
    http.post<ApiResponse<{ result: Record<string, unknown> }>>(`/workflow-notifications/retry/${deliveryId}/`),

  // Escalations
  listEscalations: (params?: { limit?: number; offset?: number }) =>
    http.get<ApiResponse<{ escalations: EscalationNotification[] }>>('/workflow-notifications/escalations/', { params }),

  // Channel health
  getChannelHealth: () =>
    http.get<ApiResponse<{ channel_health: ChannelHealthMap }>>('/workflow-notifications/channel-health/'),

  // Preferences
  listPreferences: (params?: { user_id?: string }) =>
    http.get<ApiResponse<{ preferences: NotificationPreference[] }>>('/workflow-notifications/preferences/', { params }),

  // Insights
  listInsights: () =>
    http.get<ApiResponse<{ insights: NotificationInsight[] }>>('/workflow-notifications/insights/'),

  // Test send
  testSend: (data: { workflow_id: string; rule_id: string; recipient_id?: string; channel: string }) =>
    http.post<ApiResponse<{ result: Record<string, unknown> }>>('/workflow-notifications/test-send/', data),
}
