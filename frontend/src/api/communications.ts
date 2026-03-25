import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export interface EmailAccount {
  id: string
  provider_type: 'system' | 'gmail_oauth' | 'microsoft_oauth' | 'smtp'
  account_scope: 'user' | 'tenant_shared' | 'system'
  email_address: string
  display_name: string
  from_name: string
  status: 'connected' | 'expired' | 'disconnected' | 'error' | 'pending'
  is_default_sender: boolean
  can_send: boolean
  can_receive: boolean
  health_status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown'
  failure_reason?: string
  last_success_at?: string
  last_failure_at?: string
  last_tested_at?: string
}

export interface EmailPreference {
  id: string
  default_sender_account: string | null
  fallback_behavior: string
  default_signature_mode: string
  allow_system_fallback: boolean
  banner_dismissed: boolean
}

export interface EmailTemplateDef {
  id: string
  template_type: string
  name: string
  slug: string
  category: string
  subject_template: string
  is_active: boolean
}

export interface QuickReply {
  id: string
  name: string
  category: string
  subject_template: string
  body_text: string
  is_active: boolean
}

export interface EmailMessage {
  id: string
  actual_route_used: 'user_email' | 'system_email_fallback'
  from_email: string
  to_emails: string[]
  subject: string
  status: string
  message_purpose: string
  trigger_source: string
  created_at: string
}

export const communicationsApi = {
  listEmailAccounts: () =>
    http.get<ApiResponse<{ email_accounts: EmailAccount[] }>>('/communications/email-accounts/'),

  initiateGmailConnect: (redirect_uri?: string) =>
    http.post<ApiResponse<{ auth_url: string; state: string }>>('/communications/email-accounts/gmail/connect/initiate', { redirect_uri }),

  initiateMicrosoftConnect: (redirect_uri?: string) =>
    http.post<ApiResponse<{ auth_url: string; state: string }>>('/communications/email-accounts/microsoft/connect/initiate', { redirect_uri }),

  setDefaultSender: (id: string) =>
    http.post<ApiResponse<{ email_account: EmailAccount }>>(`/communications/email-accounts/${id}/set-default`, {}),

  testEmailAccount: (id: string) =>
    http.post<ApiResponse<{ ok: boolean; reason: string; email_account: EmailAccount }>>(`/communications/email-accounts/${id}/test`, {}),

  reconnectEmailAccount: (id: string) =>
    http.post<ApiResponse<{ ok: boolean; reason: string; email_account: EmailAccount }>>(`/communications/email-accounts/${id}/reconnect`, {}),

  disconnectEmailAccount: (id: string) =>
    http.post<ApiResponse<null>>(`/communications/email-accounts/${id}/disconnect`, {}),

  getEmailPreferences: () =>
    http.get<ApiResponse<{ email_preferences: EmailPreference }>>('/communications/email-preferences/'),

  updateEmailPreferences: (payload: Partial<EmailPreference>) =>
    http.patch<ApiResponse<{ email_preferences: EmailPreference }>>('/communications/email-preferences/', payload),

  listEmailTemplates: (params?: { template_type?: string; category?: string }) =>
    http.get<ApiResponse<{ email_templates: EmailTemplateDef[] }>>('/communications/email-templates/', { params }),

  listQuickReplies: () =>
    http.get<ApiResponse<{ quick_replies: QuickReply[] }>>('/communications/quick-replies/'),

  listEmailMessages: (params?: { related_object_type?: string; related_object_id?: string; trigger_source?: string }) =>
    http.get<ApiResponse<{ email_messages: EmailMessage[] }>>('/communications/email-messages/', { params }),
}
