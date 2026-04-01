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
  candidate_id: string
  job_id: string
  status: 'draft' | 'pending_approval' | 'approved' | 'sent' | 'accepted' | 'rejected' | 'revoked'
  salary_offered: number
  joining_date: string
  document_id?: string
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
  listOffers: () =>
    http.get<ApiResponse<{ offers: OfferLetter[] }>>('/documents/offers/'),
  getOffer: (id: string) =>
    http.get<ApiResponse<{ offer: OfferLetter }>>(`/documents/offers/${id}/`),
  createOffer: (data: Partial<OfferLetter>) =>
    http.post<ApiResponse<{ offer: OfferLetter }>>('/documents/offers/', data),
  sendOffer: (id: string) =>
    http.post<ApiResponse<null>>(`/documents/offers/${id}/send/`),
  approveOffer: (id: string) =>
    http.post<ApiResponse<null>>(`/documents/offers/${id}/approve/`),
  revokeOffer: (id: string) =>
    http.post<ApiResponse<null>>(`/documents/offers/${id}/revoke/`),

  // Candidate Actions
  acceptOffer: (id: string) =>
    http.post<ApiResponse<null>>(`/documents/candidate/offers/${id}/accept/`),
  rejectOffer: (id: string, reason?: string) =>
    http.post<ApiResponse<null>>(`/documents/candidate/offers/${id}/reject/`, { reason }),
}
