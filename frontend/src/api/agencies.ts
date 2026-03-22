import http from '@/utils/http'

export const agenciesApi = {
  // Company side
  listRelationships: () =>
    http.get('/agencies/relationships/'),

  lookup: (q: string) =>
    http.get(`/agencies/lookup/?q=${encodeURIComponent(q)}`),

  createRelationship: (data: {
    invited_via?: string
    agency_tenant_id?: string
    company_tenant_id?: string
    contact_person_name?: string
    contact_email?: string
    contact_phone?: string
    industry?: string
    commission_percentage?: number
    commission_type?: string
    payment_terms?: string[]
    sla_submission_hours?: number
    sla_feedback_hours?: number
    contract_start_date?: string | null
    contract_end_date?: string | null
    notes?: string
  }) => http.post('/agencies/relationships/', data),

  getRelationship: (id: string) =>
    http.get(`/agencies/relationships/${id}/`),

  suspendRelationship: (id: string) =>
    http.post(`/agencies/relationships/${id}/suspend/`),

  reactivateRelationship: (id: string) =>
    http.post(`/agencies/relationships/${id}/reactivate/`),

  // Agency side
  listClientRelationships: () =>
    http.get('/agencies/my-clients/'),

  acceptRelationship: (id: string) =>
    http.post(`/agencies/relationships/${id}/accept/`),
}
