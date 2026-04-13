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

export interface SendEmailPayload {
  email_type: 'system' | 'business' | 'user'
  message_purpose: string
  recipients: string[]
  cc_emails?: string[]
  bcc_emails?: string[]
  related_object_type?: string
  related_object_id?: string
  subject?: string
  body_html?: string
  body_text?: string
  template_id?: string
  quick_reply_template_id?: string
  preferred_sender_account_id?: string
  allow_fallback?: boolean
  track_delivery?: boolean
}

export interface EmailFeatureStatus {
  feature_ready: boolean
  message: string
  missing_tables?: string[]
}

export interface EmailOAuthStatus {
  gmail_ready: boolean
  gmail_missing: string[]
  microsoft_ready: boolean
  microsoft_missing: string[]
  /** @deprecated use microsoft_ready */
  outlook_ready: boolean
  smtp_ready: boolean
  missing: string[]
}

export const communicationsApi = {
  getEmailFeatureStatus: () =>
    http.get<ApiResponse<EmailFeatureStatus>>('/communications/email/feature-status'),

  getEmailOAuthStatus: () =>
    http.get<ApiResponse<EmailOAuthStatus>>('/communications/email/oauth-status'),

  listEmailAccounts: () =>
    http.get<ApiResponse<{ email_accounts: EmailAccount[] }>>('/communications/email-accounts/'),

  // Backend generates the auth URL with the registered backend callback URI embedded.
  // Frontend only needs to redirect the browser to the returned auth_url.
  initiateGmailConnect: (redirect_uri: string) =>
    http.post<ApiResponse<{ authorization_url?: string; auth_url?: string; state: string }>>('/communications/email-accounts/gmail/connect/initiate', { redirect_uri }),

  initiateMicrosoftConnect: (redirect_uri: string) =>
    http.post<ApiResponse<{ authorization_url?: string; auth_url?: string; state: string }>>('/communications/email-accounts/microsoft/connect/initiate', { redirect_uri }),

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

  sendEmail: (payload: SendEmailPayload) =>
    http.post<ApiResponse<{ email_message: EmailMessage }>>('/communications/email/send', payload),

  renderEmailPreview: (payload: { template_id?: string; quick_reply_template_id?: string; variables?: Record<string, unknown> }) =>
    http.post<ApiResponse<{ preview: { subject: string; body_html: string; body_text: string } }>>('/communications/email/render-preview', payload),

  renderTemplate: (payload: {
    template_id: string
    candidate_id?: string
    job_id?: string
    interview_id?: string
    offer_id?: string
  }) =>
    http.post<ApiResponse<{
      rendered_subject: string
      rendered_body_text: string
      rendered_body_html: string
      unresolved_tags: string[]
    }>>('/communications/email/render-template', payload),

  createSmtpAccount: (payload: {
    email_address: string
    display_name: string
    from_name: string
    smtp_host: string
    smtp_port: number
    smtp_username: string
    smtp_password: string
    smtp_encryption_mode: 'ssl' | 'tls' | 'none'
    signature?: string
  }) =>
    http.post<ApiResponse<{ email_account: EmailAccount }>>('/communications/email-accounts/smtp', payload),

  updateSmtpAccount: (id: string, payload: Partial<{
    display_name: string
    from_name: string
    smtp_host: string
    smtp_port: number
    smtp_username: string
    smtp_password: string
    smtp_encryption_mode: 'ssl' | 'tls' | 'none'
    signature?: string
  }>) =>
    http.patch<ApiResponse<{ email_account: EmailAccount }>>(`/communications/email-accounts/smtp/${id}`, payload),
}
