import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export interface Document {
  id: string
  name: string
  document_type: string
  file_url: string
  created_at: string
}

export interface OfferLetter {
  id: string
  application_id: string
  candidate_id: string
  status:
    | 'draft'
    | 'pending_approval'
    | 'approval_pending'
    | 'approved'
    | 'sent'
    | 'negotiation'
    | 'accepted'
    | 'rejected'
    | 'expired'
    | 'withdrawn'
    | 'revoked'
  offered_salary: number
  currency: string
  joining_date: string
  title: string
  expires_at?: string
  metadata?: Record<string, unknown>
  created_at: string
}

export const documentsApi = {
  // Documents
  list: () =>
    http.get<ApiResponse<{ documents: Document[] }>>('/documents/documents/'),
  get: (id: string) =>
    http.get<ApiResponse<{ document: Document }>>(`/documents/documents/${id}/`),
  download: (id: string) =>
    http.get(`/documents/documents/${id}/download/`, { responseType: 'blob' }),

  // Offer Letters
  listOffers: (params?: { status?: string; application_id?: string }) =>
    http.get<ApiResponse<{ offers: OfferLetter[] }>>('/documents/offers/', { params }),
  getOffer: (id: string) =>
    http.get<ApiResponse<{ offer: OfferLetter }>>(`/documents/offers/${id}/`),
  createOffer: (data: Partial<OfferLetter>) =>
    http.post<ApiResponse<{ offer: OfferLetter }>>('/documents/offers/', data),
  submitOfferApproval: (id: string, data: { mode: 'none' | 'single' | 'multi'; roles?: string[]; required_approvals?: number }) =>
    http.post<ApiResponse<{ offer: OfferLetter }>>(`/documents/offers/${id}/submit-approval/`, data),
  sendOffer: (id: string) =>
    http.post<ApiResponse<null>>(`/documents/offers/${id}/send/`),
  approveOffer: (id: string, data?: { approval_role?: string; notes?: string }) =>
    http.post<ApiResponse<null>>(`/documents/offers/${id}/approve/`, data || {}),
  negotiateOffer: (id: string, data: { counter_salary?: number; notes?: string; negotiation_round?: number }) =>
    http.post<ApiResponse<{ offer: OfferLetter }>>(`/documents/offers/${id}/negotiate/`, data),
  revokeOffer: (id: string) =>
    http.post<ApiResponse<null>>(`/documents/offers/${id}/revoke/`),

  // Candidate Actions
  acceptOffer: (id: string) =>
    http.post<ApiResponse<null>>(`/documents/candidate/offers/${id}/accept/`),
  rejectOffer: (id: string, reason?: string) =>
    http.post<ApiResponse<null>>(`/documents/candidate/offers/${id}/reject/`, { reason }),

  candidateOfferResponseCallback: (data: {
    tenant_id?: string
    callback_reference?: string
    workflow_instance_id?: string
    wait_state_id?: string
    offer_id: string
    response: 'accepted' | 'rejected' | 'counter'
    counter_salary?: number
    notes?: string
  }) =>
    http.post<ApiResponse<any>>('/company/external/candidate-offer-response/', data, { headers: { 'X-Skip-Auth': '1' } }),
  candidateDocumentUploadedCallback: (data: {
    tenant_id?: string
    callback_reference?: string
    workflow_instance_id?: string
    wait_state_id?: string
    onboarding_id: string
    document_type: string
    document_status: string
    notes?: string
  }) =>
    http.post<ApiResponse<any>>('/company/external/candidate-document-uploaded/', data, { headers: { 'X-Skip-Auth': '1' } }),
  hrmsHandoffCallback: (data: {
    tenant_id?: string
    callback_reference?: string
    workflow_instance_id?: string
    wait_state_id?: string
    onboarding_id: string
    status: 'acknowledged' | 'rejected'
    notes?: string
  }) =>
    http.post<ApiResponse<any>>('/company/external/hrms-handoff/', data, { headers: { 'X-Skip-Auth': '1' } }),
}
