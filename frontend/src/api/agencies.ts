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
    tier?: string
    [key: string]: any
  }) => http.post('/agencies/relationships/', data),

  getRelationship: (id: string) =>
    http.get(`/agencies/relationships/${id}/`),

  updateRelationship: (id: string, data: any) => 
    http.put(`/agencies/relationships/${id}/`, data),

  deleteRelationship: (id: string) => 
    http.delete(`/agencies/relationships/${id}/`),

  suspendRelationship: (id: string) =>
    http.post(`/agencies/relationships/${id}/suspend/`),

  suspend: (id: string) => 
    http.post(`/agencies/relationships/${id}/suspend/`),

  reactivateRelationship: (id: string) =>
    http.post(`/agencies/relationships/${id}/reactivate/`),

  listAvailableAgencies: () => 
    http.get('/agencies/available/'),

  listAssignments: (params?: any) => 
    http.get('/agencies/assignments/', { params }),

  getJobIntelligence: (jobId: string) =>
    http.get(`/agencies/jobs/${jobId}/intelligence/`),

  createAssignment: (data: any) => 
    http.post('/agencies/assignments/', data),

  createGuestPortal: (data: any) => 
    http.post('/agencies/guest-portals/', data),

  createEmailTracking: (data: any) => 
    http.post('/agencies/email-tracking/', data),

  createOfflineClient: (data: any) => 
    http.post('/agencies/offline-clients/', data),

  resendPortalInvite: (portalId: string) => 
    http.post(`/agencies/guest-portals/${portalId}/resend/`),

  // Agency side
  listClientRelationships: () =>
    http.get('/agencies/my-clients/'),

  acceptRelationship: (id: string) =>
    http.post(`/agencies/relationships/${id}/accept/`),

  accept: (id: string) => 
    http.post(`/agencies/relationships/${id}/accept/`),

  myJobs: () => 
    http.get('/agencies/my-jobs/'),

  submitCandidate: (data: any) => 
    http.post('/agencies/submit-candidate/', data),

  mySubmissions: (params?: any) => 
    http.get('/agencies/my-submissions/', { params }),

  assignInternalRecruiter: (assignmentId: string, recruiterId: string) =>
    http.post(`/agencies/assignments/${assignmentId}/assign-recruiter/`, { recruiter_id: recruiterId }),

  updateSubmissionGovernance: (submissionId: string, status: string, note?: string) =>
    http.post(`/agencies/submissions/${submissionId}/governance/`, { status, note }),
}
