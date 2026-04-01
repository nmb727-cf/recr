import http from '@/utils/http'
import type { ApiResponse, Interview, InterviewFeedback, InterviewPackage, InterviewPackageBinding } from '@/types'

export interface CreateInterviewPayload {
  application_id: string
  interview_type: string
  title: string
  scheduled_at: string
  duration_minutes: number
  interview_round: number
  interviewers?: string[]
}

export const interviewsApi = {
  list: (params?: Record<string, unknown>) =>
    http.get<ApiResponse<{ interviews: Interview[] }>>('/interviews/', { params }),

  get: (id: string) =>
    http.get<ApiResponse<{ interview: Interview }>>(`/interviews/${id}/`),

  create: (data: CreateInterviewPayload) =>
    http.post<ApiResponse<{ interview: Interview }>>('/interviews/', data),

  update: (id: string, data: Partial<Interview>) =>
    http.patch<ApiResponse<{ interview: Interview }>>(`/interviews/${id}/`, data),

  delete: (id: string) =>
    http.delete<ApiResponse<unknown>>(`/interviews/${id}/`),

  submitFeedback: (id: string, data: Partial<InterviewFeedback>) =>
    http.post<ApiResponse<InterviewFeedback>>(`/interviews/${id}/feedback/`, data),

  start: (id: string) =>
    http.post<ApiResponse<Interview>>(`/interviews/${id}/start/`),

  complete: (id: string) =>
    http.post<ApiResponse<Interview>>(`/interviews/${id}/complete/`),

  cancel: (id: string, reason?: string) =>
    http.post<ApiResponse<Interview>>(`/interviews/${id}/cancel/`, { reason }),

  reschedule: (id: string, data: { scheduled_at: string }) =>
    http.post<ApiResponse<Interview>>(`/interviews/${id}/reschedule/`, data),

  // ─── Interview Types ─────────────────────────────────────────────────────
  listTypes: () =>
    http.get<ApiResponse<{ types: any[] }>>('/interviews/types/'),

  createType: (data: any) =>
    http.post<ApiResponse<{ type: any }>>('/interviews/types/', data),

  getType: (id: string) =>
    http.get<ApiResponse<{ type: any }>>(`/interviews/types/${id}/`),

  updateType: (id: string, data: any) =>
    http.put<ApiResponse<{ type: any }>>(`/interviews/types/${id}/`, data),

  getTypeConfig: (id: string) =>
    http.get<ApiResponse<{ type: any; configuration: any }>>(`/interviews/types/${id}/config/`),

  updateTypeConfig: (id: string, data: any) =>
    http.put<ApiResponse<{ type: any; configuration: any }>>(`/interviews/types/${id}/config/`, data),

  // ─── Interview Templates ──────────────────────────────────────────────────
  listTemplates: (params?: any) =>
    http.get<ApiResponse<{ templates: any[] }>>('/interviews/templates/', { params }),

  getTemplate: (id: string) =>
    http.get<ApiResponse<{ template: any }>>(`/interviews/templates/${id}/`),

  createTemplate: (data: any) =>
    http.post<ApiResponse<{ template: any }>>('/interviews/templates/', data),

  updateTemplate: (id: string, data: any) =>
    http.put<ApiResponse<{ template: any }>>(`/interviews/templates/${id}/`, data),

  // ─── Scorecard Templates ──────────────────────────────────────────────────
  listScorecards: (params?: any) =>
    http.get<ApiResponse<{ scorecards: any[] }>>('/interviews/scorecards/templates/', { params }),

  getScorecard: (id: string) =>
    http.get<ApiResponse<{ scorecard: any }>>(`/interviews/scorecards/templates/${id}/`),

  createScorecard: (data: any) =>
    http.post<ApiResponse<{ scorecard: any }>>('/interviews/scorecards/templates/', data),

  updateScorecard: (id: string, data: any) =>
    http.put<ApiResponse<{ scorecard: any }>>(`/interviews/scorecards/templates/${id}/`, data),

  // ─── Interview Kit / Structured Feedback ─────────────────────────────────
  getKit: (id: string) =>
    http.get<ApiResponse<any>>(`/interviews/${id}/kit/`),

  submitStructuredFeedback: (id: string, data: any) =>
    http.post<ApiResponse<any>>(`/interviews/${id}/structured-feedback/`, data),

  getPanelDecision: (id: string) =>
    http.get<ApiResponse<any>>(`/interviews/${id}/panel-decision/`),

  getDecision: (id: string) =>
    http.get<ApiResponse<any>>(`/interviews/${id}/decision/`),

  recordDecision: (id: string, data: any) =>
    http.post<ApiResponse<any>>(`/interviews/${id}/decision/`, data),

  evaluateDecision: (id: string, data: any) =>
    http.post<ApiResponse<any>>(`/interviews/${id}/decision/evaluate/`, data),

  getDecisionHistory: (id: string) =>
    http.get<ApiResponse<any>>(`/interviews/${id}/decision/history/`),

  // ─── Scheduling Engine ────────────────────────────────────────────────────
  getAvailabilityProfile: (params?: { interviewer_id?: string }) =>
    http.get<ApiResponse<any>>('/interviews/availability/profile/', { params }),

  updateAvailabilityProfile: (data: any) =>
    http.put<ApiResponse<any>>('/interviews/availability/profile/', data),

  listAvailabilityBlocks: (params?: { interviewer_id?: string }) =>
    http.get<ApiResponse<any>>('/interviews/availability/blocks/', { params }),

  createAvailabilityBlock: (data: any) =>
    http.post<ApiResponse<any>>('/interviews/availability/blocks/', data),

  getPanelSlots: (data: any) =>
    http.post<ApiResponse<any>>('/interviews/availability/panel-slots/', data),

  manualSchedule: (data: any) =>
    http.post<ApiResponse<any>>('/interviews/scheduling/manual/', data),

  scheduleInterviewFlex: (id: string, data: any) =>
    http.post<ApiResponse<any>>(`/interviews/${id}/schedule-flex/`, data),

  cancelInterviewFlex: (id: string, data?: { reason?: string }) =>
    http.post<ApiResponse<any>>(`/interviews/${id}/cancel-flex/`, data || {}),

  createSchedulingLink: (id: string, data?: any) =>
    http.post<ApiResponse<any>>(`/interviews/${id}/scheduling-link/`, data || {}),

  getPublicSchedulingLink: (token: string) =>
    http.get<ApiResponse<any>>(`/interviews/scheduling-link/${token}/`, { headers: { 'X-Skip-Auth': '1' } }),

  bookPublicSchedulingLink: (token: string, data: any) =>
    http.post<ApiResponse<any>>(`/interviews/scheduling-link/${token}/`, data, { headers: { 'X-Skip-Auth': '1' } }),

  listCalendarConnections: (params?: { interviewer_id?: string }) =>
    http.get<ApiResponse<any>>('/interviews/calendar/connections/', { params }),

  saveCalendarConnection: (data: any) =>
    http.post<ApiResponse<any>>('/interviews/calendar/connections/', data),

  // ─── Integration Engine ──────────────────────────────────────────────────
  listIntegrationProviders: (params?: any) =>
    http.get<ApiResponse<{ providers: any[] }>>('/interviews/integrations/providers/', { params }),

  updateIntegrationProvider: (id: string, data: any) =>
    http.put<ApiResponse<{ provider: any }>>(`/interviews/integrations/providers/${id}/`, data),

  listTenantProviderConnections: () =>
    http.get<ApiResponse<{ connections: any[] }>>('/interviews/integrations/connections/'),

  saveTenantProviderConnection: (data: any) =>
    http.post<ApiResponse<{ connection: any }>>('/interviews/integrations/connections/', data),

  updateTenantProviderConnection: (id: string, data: any) =>
    http.put<ApiResponse<{ connection: any }>>(`/interviews/integrations/connections/${id}/`, data),

  listExecutionMappings: (params?: any) =>
    http.get<ApiResponse<{ mappings: any[] }>>('/interviews/integrations/mappings/', { params }),

  createExecutionMapping: (data: any) =>
    http.post<ApiResponse<{ mapping: any }>>('/interviews/integrations/mappings/', data),

  updateExecutionMapping: (id: string, data: any) =>
    http.put<ApiResponse<{ mapping: any }>>(`/interviews/integrations/mappings/${id}/`, data),

  // ─── Interview Question Engine ───────────────────────────────────────────
  listQuestionBank: (params?: any) =>
    http.get<ApiResponse<{ questions: any[] }>>('/interviews/questions/bank/', { params }),

  createQuestionBank: (data: any) =>
    http.post<ApiResponse<{ question: any }>>('/interviews/questions/bank/', data),

  updateQuestionBank: (id: string, data: any) =>
    http.put<ApiResponse<{ question: any }>>(`/interviews/questions/bank/${id}/`, data),

  listQuestionAttachments: (params?: any) =>
    http.get<ApiResponse<{ attachments: any[] }>>('/interviews/questions/attachments/', { params }),

  attachQuestion: (data: any) =>
    http.post<ApiResponse<{ attachment: any }>>('/interviews/questions/attachments/', data),

  updateQuestionAttachment: (id: string, data: any) =>
    http.put<ApiResponse<{ attachment: any }>>(`/interviews/questions/attachments/${id}/`, data),

  listQuestionGroups: (params?: any) =>
    http.get<ApiResponse<{ groups: any[] }>>('/interviews/questions/groups/', { params }),

  createQuestionGroup: (data: any) =>
    http.post<ApiResponse<{ group: any }>>('/interviews/questions/groups/', data),

  updateQuestionGroup: (id: string, data: any) =>
    http.put<ApiResponse<{ group: any }>>(`/interviews/questions/groups/${id}/`, data),

  // ─── Interview Flows ─────────────────────────────────────────────────────
  listFlows: (params?: any) =>
    http.get<ApiResponse<{ flows: any[] }>>('/interviews/flows/', { params }),

  getFlow: (id: string) =>
    http.get<ApiResponse<{ flow: any }>>(`/interviews/flows/${id}/`),

  createFlow: (data: { name: string; description?: string; stages: any[]; metadata?: object }) =>
    http.post<ApiResponse<{ flow: any }>>('/interviews/flows/', data),

  updateFlow: (id: string, data: any) =>
    http.put<ApiResponse<{ flow: any }>>(`/interviews/flows/${id}/`, data),

  deleteFlow: (id: string) =>
    http.delete<ApiResponse<unknown>>(`/interviews/flows/${id}/`),

  // ─── Interview Packages (Legacy/Alias) ───────────────────────────────────
  listPackages: (params?: any) =>
    http.get<ApiResponse<{ packages: InterviewPackage[] }>>('/interviews/packages/', { params }),

  getPackage: (id: string) =>
    http.get<ApiResponse<{ package: InterviewPackage }>>(`/interviews/packages/${id}/`),

  createPackage: (data: Partial<InterviewPackage>) =>
    http.post<ApiResponse<{ package: InterviewPackage }>>('/interviews/packages/', data),

  updatePackage: (id: string, data: Partial<InterviewPackage>) =>
    http.put<ApiResponse<{ package: InterviewPackage }>>(`/interviews/packages/${id}/`, data),

  // ─── Job Bindings ────────────────────────────────────────────────────────
  getJobBinding: (jobId: string) =>
    http.get<ApiResponse<{ binding: InterviewPackageBinding | null }>>(`/jobs/requisitions/${jobId}/interview-binding/`),

  bindToJob: (jobId: string, packageId: string) =>
    http.post<ApiResponse<{ binding: InterviewPackageBinding }>>(`/jobs/requisitions/${jobId}/interview-binding/`, { package_id: packageId }),

  bindJobPackage: (jobId: string, packageId: string) =>
    http.post<ApiResponse<{ binding: InterviewPackageBinding }>>(`/jobs/requisitions/${jobId}/interview-binding/`, { package_id: packageId }),

  updateJobBinding: (jobId: string, data: Partial<InterviewPackageBinding>) =>
    http.put<ApiResponse<{ binding: InterviewPackageBinding }>>(`/jobs/requisitions/${jobId}/interview-binding/`, data),

  unbindFromJob: (jobId: string) =>
    http.delete<ApiResponse<unknown>>(`/jobs/requisitions/${jobId}/interview-binding/`),

  // ─── Candidate Runtime Engine ────────────────────────────────────────────
  candidateList: () =>
    http.get<ApiResponse<any>>('/candidate/interviews/'),

  candidateInstructions: (id: string) =>
    http.get<ApiResponse<any>>(`/candidate/interviews/${id}/instructions/`),

  candidateRuntime: (id: string, params?: { access_token?: string; session_id?: string }) =>
    http.get<ApiResponse<any>>(`/candidate/interviews/${id}/runtime/`, { params }),

  candidateStatus: (id: string) =>
    http.get<ApiResponse<any>>(`/candidate/interviews/${id}/status/`),

  candidateStart: (id: string, data?: { access_token?: string; session_id?: string }) =>
    http.post<ApiResponse<any>>(`/candidate/interviews/${id}/start/`, data || {}),

  candidateSubmitAnswer: (id: string, data: { question_id: string; answer_text?: string; video_url?: string; assignment_url?: string }) =>
    http.post<ApiResponse<any>>(`/candidate/interviews/${id}/submit-answer/`, data),

  candidateComplete: (id: string) =>
    http.post<ApiResponse<any>>(`/candidate/interviews/${id}/complete/`),

  candidateSecurityEvent: (id: string, data: { event_type: 'tab_switch' | 'copy_paste' | 'multiple_window' }) =>
    http.post<ApiResponse<any>>(`/candidate/interviews/${id}/security-event/`, data),
}
