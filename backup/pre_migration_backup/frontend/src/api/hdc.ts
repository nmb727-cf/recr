import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const hdcApi = {
  // Hiring Committee
  listCommittees: () => http.get<ApiResponse<any[]>>('/hdc/committees/'),
  createCommittee: (data: any) => http.post<ApiResponse<any>>('/hdc/committees/', data),
  getCommittee: (id: string) => http.get<ApiResponse<any>>(`/hdc/committees/${id}/`),
  updateCommittee: (id: string, data: any) => http.put<ApiResponse<any>>(`/hdc/committees/${id}/`, data),
  submitVote: (id: string, data: any) => http.post<ApiResponse<any>>(`/hdc/committees/${id}/submit_vote/`, data),

  // Candidate Comparison
  listComparisons: () => http.get<ApiResponse<any[]>>('/hdc/comparisons/'),
  createComparison: (data: any) => http.post<ApiResponse<any>>('/hdc/comparisons/', data),
  getComparison: (id: string) => http.get<ApiResponse<any>>(`/hdc/comparisons/${id}/`),
  updateComparison: (id: string, data: any) => http.put<ApiResponse<any>>(`/hdc/comparisons/${id}/`, data),
  freezeComparison: (id: string) => http.post<ApiResponse<any>>(`/hdc/comparisons/${id}/freeze/`, {}),

  // Decision Approval
  listApprovals: () => http.get<ApiResponse<any[]>>('/hdc/approvals/'),
  createApproval: (data: any) => http.post<ApiResponse<any>>('/hdc/approvals/', data),
  getApproval: (id: string) => http.get<ApiResponse<any>>(`/hdc/approvals/${id}/`),
  approveForOffer: (id: string, data: any) => http.post<ApiResponse<any>>(`/hdc/approvals/${id}/approve_for_offer/`, data),
  rejectCandidate: (id: string, data: any) => http.post<ApiResponse<any>>(`/hdc/approvals/${id}/reject_candidate/`, data),
  sendBackToReview: (id: string, data: any) => http.post<ApiResponse<any>>(`/hdc/approvals/${id}/send_back_to_review/`, data),

  // Offer Intelligence & Compensation
  listOfferRecommendations: () => http.get<ApiResponse<any[]>>('/hdc/offer-recommendations/'),
  createOfferRecommendation: (data: any) => http.post<ApiResponse<any>>('/hdc/offer-recommendations/', data),
  getOfferRecommendation: (id: string) => http.get<ApiResponse<any>>(`/hdc/offer-recommendations/${id}/`),
  selectScenario: (id: string, scenarioId: string) => http.post<ApiResponse<any>>(`/hdc/offer-recommendations/${id}/select_scenario/`, { scenario_id: scenarioId }),

  // Negotiation
  listNegotiations: () => http.get<ApiResponse<any[]>>('/hdc/negotiations/'),
  createNegotiation: (data: any) => http.post<ApiResponse<any>>('/hdc/negotiations/', data),
  getNegotiation: (id: string) => http.get<ApiResponse<any>>(`/hdc/negotiations/${id}/`),
  addNegotiationRound: (id: string, data: any) => http.post<ApiResponse<any>>(`/hdc/negotiations/${id}/add_round/`, data),

  // Offer Release
  listOfferReleases: () => http.get<ApiResponse<any[]>>('/hdc/offer-release/'),
  createOfferRelease: (data: any) => http.post<ApiResponse<any>>('/hdc/offer-release/', data),
  getOfferRelease: (id: string) => http.get<ApiResponse<any>>(`/hdc/offer-release/${id}/`),
  freezeOffer: (id: string) => http.post<ApiResponse<any>>(`/hdc/offer-release/${id}/freeze/`, {}),
  releaseOffer: (id: string) => http.post<ApiResponse<any>>(`/hdc/offer-release/${id}/release/`, {}),
  recordCandidateResponse: (id: string, data: { response: string; reason?: string }) =>
    http.post<ApiResponse<any>>(`/hdc/offer-release/${id}/record_response/`, data),

  // Joining Tracking
  listJoiningCases: () => http.get<ApiResponse<any[]>>('/hdc/joining/'),
  createJoiningCase: (data: any) => http.post<ApiResponse<any>>('/hdc/joining/', data),
  updateJoiningCase: (id: string, data: any) => http.put<ApiResponse<any>>(`/hdc/joining/${id}/`, data),
  confirmJoining: (id: string) => http.post<ApiResponse<any>>(`/hdc/joining/${id}/confirm_joining/`, {}),
  getJoiningChecklist: (id: string) => http.get<ApiResponse<any>>(`/hdc/joining/${id}/checklist/`),
  upsertJoiningChecklistItem: (id: string, data: any) =>
    http.post<ApiResponse<any>>(`/hdc/joining/${id}/upsert_checklist_item/`, data),
  prepareOnboardingHandoff: (id: string) =>
    http.post<ApiResponse<any>>(`/hdc/joining/${id}/prepare_handoff/`, {}),

  // Operational Context
  getStats: () => http.get<ApiResponse<any>>('/hdc/stats/'),
  getApplicationStatus: (applicationId: string) => http.get<ApiResponse<any>>(`/hdc/status/${applicationId}/`),
}
