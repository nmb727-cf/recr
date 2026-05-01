import http from '@/utils/http'
import type { ApiResponse } from '@/types'

// ── Channel config types ──────────────────────────────────────────────────────

export type ChannelType = 'in_app' | 'email' | 'whatsapp' | 'sms' | 'push'

export type WhatsAppProvider =
  | 'whatsapp_business_api'
  | 'twilio_whatsapp'
  | 'mock'

export type SMSProvider = 'twilio' | 'generic_http' | 'mock'

export type PushProvider = 'web_push' | 'fcm' | 'apns' | 'mock'

export interface TenantChannelConfig {
  id: string
  channel_type: 'whatsapp' | 'sms' | 'push'
  provider: string
  sender_name: string
  sender_identifier: string
  api_key_id: string
  api_token_masked: string
  whatsapp_phone_number_id: string
  whatsapp_business_account_id: string
  whatsapp_api_version: string
  sms_http_endpoint: string
  push_vapid_public_key: string
  push_fcm_project_id: string
  is_active: boolean
  is_default: boolean
  config_json: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface ChannelConfigCreatePayload {
  channel_type: 'whatsapp' | 'sms' | 'push'
  provider: string
  sender_name?: string
  sender_identifier?: string
  api_key_id?: string
  api_token?: string
  webhook_secret?: string
  whatsapp_phone_number_id?: string
  whatsapp_business_account_id?: string
  whatsapp_api_version?: string
  sms_http_endpoint?: string
  sms_http_method?: string
  push_vapid_public_key?: string
  push_vapid_private_key?: string
  push_fcm_project_id?: string
  is_active?: boolean
  config_json?: Record<string, unknown>
}

export type ChannelConfigPatchPayload = Partial<ChannelConfigCreatePayload>

// ── Delivery types ────────────────────────────────────────────────────────────

export type DeliveryStatus =
  | 'pending'
  | 'sent'
  | 'delivered'
  | 'read'
  | 'failed'
  | 'bounced'
  | 'deferred'
  | 'cancelled'
  | 'skipped'

export interface CommunicationDelivery {
  id: string
  channel_type: ChannelType
  provider: string
  status: DeliveryStatus
  priority: string
  recipient_user_id: string | null
  notification_id: string | null
  template_used: string
  attempt_number: number
  scheduled_for: string | null
  attempted_at: string | null
  delivered_at: string | null
  created_at: string
  external_message_id: string
  skip_reason: string
  // Full detail fields
  error_message?: string
  external_status_payload?: Record<string, unknown>
  metadata?: Record<string, unknown>
}

export interface DeliveryListParams {
  channel_type?: ChannelType
  status?: DeliveryStatus
  notification_id?: string
  page?: number
}

// ── Health types ──────────────────────────────────────────────────────────────

export interface ChannelHealthResult {
  healthy: boolean
  provider: string
  latency_ms?: number
  detail?: string
}

export type ChannelHealthMap = Record<string, ChannelHealthResult>

// ── Stats types ───────────────────────────────────────────────────────────────

export interface ChannelStats {
  period_days: number
  tenant_id: string
  channels: Record<string, Record<string, number>>
}

// ── API ───────────────────────────────────────────────────────────────────────

export const channelControlApi = {
  // Channel configs
  listChannelConfigs: () =>
    http.get<ApiResponse<{ results: TenantChannelConfig[] }>>('/communications/channel-configs/'),

  getChannelConfig: (id: string) =>
    http.get<ApiResponse<TenantChannelConfig>>(`/communications/channel-configs/${id}/`),

  createChannelConfig: (payload: ChannelConfigCreatePayload) =>
    http.post<ApiResponse<TenantChannelConfig>>('/communications/channel-configs/', payload),

  patchChannelConfig: (id: string, payload: ChannelConfigPatchPayload) =>
    http.patch<ApiResponse<TenantChannelConfig>>(`/communications/channel-configs/${id}/`, payload),

  deleteChannelConfig: (id: string) =>
    http.delete<ApiResponse<null>>(`/communications/channel-configs/${id}/`),

  // Deliveries
  listDeliveries: (params?: DeliveryListParams) =>
    http.get<ApiResponse<{ results: CommunicationDelivery[]; count: number }>>(
      '/communications/deliveries/',
      { params },
    ),

  getDelivery: (id: string) =>
    http.get<ApiResponse<CommunicationDelivery>>(`/communications/deliveries/${id}/`),

  retryDelivery: (id: string) =>
    http.post<ApiResponse<{ detail: string; delivery_id: string }>>(
      `/communications/deliveries/${id}/retry/`,
      {},
    ),

  // Channel health
  getChannelHealth: () =>
    http.get<ApiResponse<ChannelHealthMap>>('/communications/channel-health/'),

  // Stats
  getChannelStats: () =>
    http.get<ApiResponse<ChannelStats>>('/communications/channel-stats/'),
}
