import http from '@/utils/http'
import type { ApiResponse } from '@/types'

export const prequalificationApi = {
  // ── Forms ─────────────────────────────────────────────────────────────────
  listForms: (params?: Record<string, unknown>) =>
    http.get<ApiResponse<{ forms: any[] }>>('/prequalification/forms/', { params }),

  getForm: (id: string) =>
    http.get<ApiResponse<{ form: any }>>(`/prequalification/forms/${id}/`),

  createForm: (data: { name: string; description?: string; metadata?: object }) =>
    http.post<ApiResponse<{ form: any }>>('/prequalification/forms/', data),

  updateForm: (id: string, data: Partial<{ name: string; description: string; is_active: boolean; metadata: object }>) =>
    http.put<ApiResponse<{ form: any }>>(`/prequalification/forms/${id}/`, data),

  deleteForm: (id: string) =>
    http.delete<ApiResponse<unknown>>(`/prequalification/forms/${id}/`),

  // ── Sections ──────────────────────────────────────────────────────────────
  listSections: (formId: string) =>
    http.get<ApiResponse<{ sections: any[] }>>('/prequalification/sections/', {
      params: { form_id: formId },
    }),

  createSection: (data: { form: string; title: string; description?: string; order?: number }) =>
    http.post<ApiResponse<{ section: any }>>('/prequalification/sections/', data),

  updateSection: (id: string, data: Partial<{ title: string; description: string; order: number }>) =>
    http.patch<ApiResponse<{ section: any }>>(`/prequalification/sections/${id}/`, data),

  deleteSection: (id: string) =>
    http.delete<ApiResponse<unknown>>(`/prequalification/sections/${id}/`),

  // ── Questions ─────────────────────────────────────────────────────────────
  listQuestions: (sectionId: string) =>
    http.get<ApiResponse<{ questions: any[] }>>('/prequalification/questions/', {
      params: { section_id: sectionId },
    }),

  createQuestion: (data: {
    section: string
    question_text: string
    question_type: string
    required?: boolean
    order?: number
    help_text?: string
    options_json?: any[]
    score_weight?: number
    is_knockout?: boolean
  }) =>
    http.post<ApiResponse<{ question: any }>>('/prequalification/questions/', data),

  updateQuestion: (id: string, data: Partial<{
    question_text: string
    question_type: string
    required: boolean
    order: number
    help_text: string
    options_json: any[]
    score_weight: number
    is_knockout: boolean
    metadata: object
  }>) =>
    http.patch<ApiResponse<{ question: any }>>(`/prequalification/questions/${id}/`, data),

  deleteQuestion: (id: string) =>
    http.delete<ApiResponse<unknown>>(`/prequalification/questions/${id}/`),

  // ── Rules ─────────────────────────────────────────────────────────────────
  listRules: (questionId: string) =>
    http.get<ApiResponse<{ rules: any[] }>>('/prequalification/rules/', {
      params: { question_id: questionId },
    }),

  createRule: (data: {
    question_id: string
    condition_type: string
    compare_value?: string
    action_type: string
    outcome_code?: string
    target_question_id?: string
    target_section_id?: string
  }) =>
    http.post<ApiResponse<{ rule: any }>>('/prequalification/rules/', data),

  deleteRule: (id: string) =>
    http.delete<ApiResponse<unknown>>(`/prequalification/rules/${id}/`),

  // ── Responses ─────────────────────────────────────────────────────────────
  listResponses: (params?: { form_id?: string; candidate_id?: string }) =>
    http.get<ApiResponse<{ responses: any[] }>>('/prequalification/responses/', { params }),

  submitResponse: (data: {
    form: string
    question: string
    answer_text?: string
    answer_json?: object
  }) =>
    http.post<ApiResponse<{ response: any }>>('/prequalification/responses/', data),

  // ── Candidate Side ────────────────────────────────────────────────────────
  candidateGetForm: (id: string) =>
    http.get<ApiResponse<{ form: any }>>(`/candidate/prequalification/forms/${id}/`),

  candidateSubmitForm: (id: string, responses: any[]) =>
    http.post<ApiResponse<unknown>>(`/candidate/prequalification/forms/${id}/submit/`, { responses }),
}
