import http from '@/utils/http'
import type { ApiResponse } from '@/types'

// ── Types ────────────────────────────────────────────────────────────────────

export type RuleCategory =
  | 'candidate' | 'application' | 'interview' | 'offer'
  | 'approval' | 'agency' | 'deadline' | 'messaging' | 'passport' | 'system'

export type RulePriority = 'info' | 'medium' | 'high' | 'critical'

export type EscalationTargetType =
  | 'assigned_manager' | 'hiring_manager' | 'recruiter_lead' | 'tenant_admin'

export interface NotificationRule {
  id: string
  tenant_id: string | null
  event_key: string
  business_label: string
  category: RuleCategory
  priority: RulePriority
  is_active: boolean
  is_system: boolean
  is_locked: boolean
  in_app_enabled: boolean
  email_enabled: boolean
  whatsapp_enabled: boolean
  sms_enabled: boolean
  send_immediately: boolean
  fallback_enabled: boolean
  fallback_delay_minutes: number
  escalation_enabled: boolean
  escalation_delay_minutes: number
  escalation_target_type: EscalationTargetType
  template_id: string | null
  template_name: string
  allow_user_override: boolean
  admin_notes: string
  is_tenant_override: boolean
  created_at: string
  updated_at: string
}

export interface ChannelSetting {
  id: string
  tenant_id: string
  channel_type: 'in_app' | 'email' | 'whatsapp' | 'sms' | 'push'
  is_enabled: boolean
  provider: string
  quiet_hours_enabled: boolean
  quiet_hours_start: string | null
  quiet_hours_end: string | null
  sender_name: string
  sender_email: string
  updated_at: string
}

export interface NotificationPreferenceDefaults {
  id: string
  tenant_id: string
  default_in_app_enabled: boolean
  default_email_enabled: boolean
  default_reminder_enabled: boolean
  allow_user_override: boolean
  digest_frequency: 'immediate' | 'hourly' | 'daily'
  updated_at: string
}

export interface NotificationControlSummary {
  total_rules: number
  active_rules: number
  fallback_enabled_count: number
  escalation_enabled_count: number
  high_priority_count: number
  email_channel_enabled: boolean
  in_app_channel_enabled: boolean
}

export type RuleUpdatePayload = Partial<Omit<
  NotificationRule,
  'id' | 'tenant_id' | 'is_system' | 'is_tenant_override' | 'created_at' | 'updated_at'
>>

// ── API calls ────────────────────────────────────────────────────────────────

export const notificationControlApi = {
  getSummary: () =>
    http.get<ApiResponse<{ summary: NotificationControlSummary }>>('/communications/notification-control/summary/'),

  listRules: (params?: { category?: string; search?: string }) =>
    http.get<ApiResponse<{ rules: NotificationRule[]; total: number }>>('/communications/notification-control/rules/', { params }),

  getRule: (eventKey: string) =>
    http.get<ApiResponse<{ rule: NotificationRule }>>(`/communications/notification-control/rules/${eventKey}/`),

  updateRule: (eventKey: string, data: RuleUpdatePayload) =>
    http.put<ApiResponse<{ rule: NotificationRule }>>(`/communications/notification-control/rules/${eventKey}/`, data),

  createRule: (data: RuleUpdatePayload & { event_key: string }) =>
    http.post<ApiResponse<{ rule: NotificationRule }>>('/communications/notification-control/rules/', data),

  getChannelSettings: () =>
    http.get<ApiResponse<{ channel_settings: ChannelSetting[] }>>('/communications/notification-control/channel-settings/'),

  updateChannelSettings: (settings: { channel_type: string; is_enabled: boolean }[]) =>
    http.put<ApiResponse<{ channel_settings: ChannelSetting[] }>>('/communications/notification-control/channel-settings/', { settings }),

  getPreferenceDefaults: () =>
    http.get<ApiResponse<{ preferences: NotificationPreferenceDefaults }>>('/communications/notification-control/default-preferences/'),

  updatePreferenceDefaults: (data: Partial<NotificationPreferenceDefaults>) =>
    http.put<ApiResponse<{ preferences: NotificationPreferenceDefaults }>>('/communications/notification-control/default-preferences/', data),
}
