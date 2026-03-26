import http from '@/utils/http'
import type { ApiResponse, Passport } from '@/types'

/** Shape returned by GET /passport/my-candidate/ */
export interface LinkedCandidateData {
  id: string
  // Identity
  email: string
  phone: string
  phone_number: string
  phone_country_code: string
  // Professional
  first_name: string
  last_name: string
  current_title: string
  current_company: string
  current_location_city: string
  current_location_country: string
  experience_years: number | null
  relevant_experience_years: number | null
  linkedin_url: string
  // Lists (merge with passport)
  skills: string[]
  languages: string[]
  tags: string[]
  // Work auth / visa
  nationality: string
  work_authorization: string
  visa_status: string
  pr_status: string
  // Availability
  availability_status: string
  notice_period_days: number | null
  last_working_day: string | null
  availability_date: string | null
  is_actively_looking: boolean
  work_mode_preference: string
  // Compensation
  expected_salary_min: number | null
  expected_salary_max: number | null
  salary_currency: string
  // Documents
  resume_url: string
  // Meta
  source: string
  initial_entry_type: string
  account_status: string
}

export const passportApi = {
  get: () =>
    http.get<ApiResponse<{ passport: Passport }>>('/passport/my-passport/'),

  update: (data: Partial<Passport>) =>
    http.put<ApiResponse<{ passport: Passport }>>('/passport/my-passport/', data),

  getShareLink: () =>
    http.get<ApiResponse<{ share_url: string }>>('/passport/my-passport/share-link/'),

  regenerateShareLink: () =>
    http.post<ApiResponse<{ share_url: string }>>('/passport/my-passport/share-link/regenerate/'),

  importPassport: (token: string) =>
    http.post<ApiResponse<{ candidate: any }>>('/passport/import/', { token }),

  /**
   * Fetch the Candidate record linked to the current user.
   * Used by onboarding to prefill fields with recruiter-entered data.
   * Returns { no_candidate: true } if no linked record exists.
   */
  getLinkedCandidate: () =>
    http.get<ApiResponse<{ candidate: LinkedCandidateData | null; no_candidate?: boolean }>>(
      '/passport/my-candidate/'
    ),

  /**
   * Update Candidate-model fields that don't live on the Passport
   * (availability_status, nationality, work_authorization, etc.).
   * Uses append semantics on the backend — empty values are not written.
   */
  updateLinkedCandidate: (data: Partial<LinkedCandidateData>) =>
    http.patch<ApiResponse<{ updated: boolean; fields_updated: string[] }>>(
      '/passport/my-candidate/',
      data
    ),
}
