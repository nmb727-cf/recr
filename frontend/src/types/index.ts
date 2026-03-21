// ─── Auth ─────────────────────────────────────────────────────────────────────

export type UserRole =
  | 'super_admin'
  | 'tenant_admin'
  | 'recruiter'
  | 'hiring_manager'
  | 'interviewer'
  | 'candidate'
  | 'agency_owner'
  | 'agency_admin'
  | 'agency_recruiter'

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone: string
  avatar_url: string
  role: UserRole
  is_active: boolean
  email_verified: boolean
  mfa_enabled: boolean
  timezone: string
  language: string
  tenant_id: string
  created_at: string
  last_login_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterCompanyPayload {
  name: string
  company_name: string
  email: string
  password: string
  country_code?: string
}

export interface RegisterCandidatePayload {
  first_name: string
  last_name: string
  email: string
  password: string
  phone?: string
}

// ─── API response wrapper ─────────────────────────────────────────────────────

export interface ApiResponse<T = unknown> {
  success: boolean
  data: T
  message: string
  meta?: {
    total?: number
    [key: string]: unknown
  }
}

// ─── Jobs ─────────────────────────────────────────────────────────────────────

export type JobType = 'full_time' | 'part_time' | 'contract' | 'internship' | 'freelance'
export type WorkMode = 'onsite' | 'remote' | 'hybrid'
export type RequisitionStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'active'
  | 'closed'
  | 'cancelled'
export type Priority = 'low' | 'medium' | 'high' | 'urgent'

export interface JobRequisition {
  id: string
  tenant_id: string
  title: string
  department_id: string | null
  location_id: string | null
  job_type: JobType
  work_mode: WorkMode
  experience_min: number
  experience_max: number
  salary_min: string
  salary_max: string
  salary_currency: string
  salary_visible: boolean
  headcount: number
  priority: Priority
  is_confidential: boolean
  description: string
  requirements: string
  responsibilities: string
  skills_required: string[]
  status: RequisitionStatus
  approved_at: string | null
  approved_by: string | null
  target_date: string | null
  closed_at: string | null
  closed_reason: string
  created_at: string
  updated_at: string
  created_by: string
  metadata: Record<string, unknown>
}

export interface JobPosting {
  id: string
  tenant_id: string
  requisition_id: string
  title: string
  slug: string
  description_html: string
  external_description: string
  posted_at: string
  expires_at: string | null
  is_active: boolean
  views_count: number
  applications_count: number
  posted_on: string[]
  custom_application_form: Record<string, unknown>
  created_at: string
  updated_at: string
  metadata: Record<string, unknown>
}

export interface JobStage {
  id: string
  tenant_id: string
  requisition_id: string
  name: string
  stage_order: number
  stage_type: 'screening' | 'interview' | 'offer' | 'joined'
  action_deadline_hours: number
  is_active: boolean
}

// ─── Candidates ───────────────────────────────────────────────────────────────

export interface Candidate {
  id: string
  tenant_id: string
  first_name: string
  last_name: string
  full_name: string
  email: string
  phone: string
  whatsapp: string
  linkedin_url: string
  current_title: string
  current_company: string
  current_location_city: string
  current_location_country: string
  experience_years: string
  expected_salary_min: number | null
  expected_salary_max: number | null
  salary_currency: string
  notice_period_days: number | null
  availability_date: string | null
  is_actively_looking: boolean
  source: string
  source_detail: string
  passport_id: string | null
  is_duplicate: boolean
  duplicate_of: string | null
  tags: string[]
  skills: string[]
  languages: string[]
  assigned_to: string | null
  owner_user_id: string
  owner_tenant_id: string
  created_at: string
  updated_at: string
  created_by: string
  metadata: Record<string, unknown>
}

export interface CandidateProfile {
  id: string
  candidate_id: string
  summary: string
  work_experience: Record<string, unknown>[]
  education: Record<string, unknown>[]
  certifications: Record<string, unknown>[]
  projects: Record<string, unknown>[]
  cv_url: string
  cv_uploaded_at: string | null
  portfolio_url: string
  github_url: string
  stackoverflow_url: string
  created_at: string
  updated_at: string
}

export interface CandidateDetail extends Candidate {
  profile: CandidateProfile | null
  notes_count: number
}

export interface CandidateNote {
  id: string
  tenant_id: string
  candidate_id: string
  note_text: string
  note_type: string
  is_private: boolean
  created_at: string
  updated_at: string
  created_by: string
  metadata: Record<string, unknown>
}

export interface TimelineEvent {
  type: string
  note_type: string
  text: string
  created_at: string
  created_by: string
}

// ─── Pipeline / Applications ──────────────────────────────────────────────────

export type ApplicationStatus =
  | 'applied'
  | 'screening'
  | 'shortlisted'
  | 'in_review'
  | 'interview_scheduled'
  | 'offer_extended'
  | 'offer_accepted'
  | 'rejected'
  | 'withdrawn'

export interface Application {
  id: string
  tenant_id: string
  candidate_id: string
  requisition_id: string
  current_stage_id: string | null
  status: ApplicationStatus
  source: string
  source_detail: string
  submitted_by: string
  submitted_by_tenant_id: string
  agency_id: string | null
  is_agency_submission: boolean
  match_score: number | null
  rejection_reason: string
  rejection_category: string
  withdrawn_reason: string
  offer_amount: number | null
  offer_currency: string
  offer_date: string | null
  offer_accepted_at: string | null
  offer_rejected_at: string | null
  joining_date: string | null
  joined_at: string | null
  application_form_data: Record<string, unknown>
  created_at: string
  updated_at: string
  created_by: string
  metadata: Record<string, unknown>
}

// Pipeline board — the exact shape returned by GET /pipeline/{requisition_id}/
export interface PipelineStageData {
  stage: Pick<JobStage, 'id' | 'name' | 'stage_type' | 'stage_order'>
  applications: Application[]
  count: number
}

export interface PipelineData {
  requisition_id: string
  pipeline: Record<string, PipelineStageData>
  total_applications: number
}

// ─── Interviews ───────────────────────────────────────────────────────────────

export type InterviewType =
  | 'phone_screening'
  | 'video_call'
  | 'technical_assessment'
  | 'whiteboard'
  | 'coding_live'
  | 'case_study'
  | 'behavioral'
  | 'culture_fit'
  | 'on_site'
  | 'panel'
  | 'final_round'

export type InterviewStatus =
  | 'scheduled'
  | 'confirmed'
  | 'rescheduled'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'no_show'
  | 'pending_feedback'

export interface Interview {
  id: string
  tenant_id: string
  application_id: string
  interview_type: InterviewType
  title: string
  scheduled_at: string
  duration_minutes: number
  interview_round: number
  location_type: 'online' | 'office' | 'other'
  location_detail: string
  meeting_link: string
  meeting_id: string
  status: InterviewStatus
  feedback_average_score: number | null
  feedback_count: number
  interviewers: string[] // User IDs
  candidate_notified: boolean
  interviewers_notified: boolean
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string
  metadata: Record<string, unknown>
  // Expanded fields
  candidate_name?: string
  job_title?: string
}

export interface InterviewFeedback {
  id: string
  tenant_id: string
  interview_id: string
  interviewer_id: string
  score: number
  recommendation: 'strong_hire' | 'hire' | 'neutral' | 'no_hire' | 'strong_no_hire'
  feedback_text: string
  strengths: string[]
  weaknesses: string[]
  private_notes: string
  is_submitted: boolean
  submitted_at: string | null
  created_at: string
  updated_at: string
}

// ─── Agencies ─────────────────────────────────────────────────────────────────

export type AgencyStatus = 'pending' | 'active' | 'suspended' | 'terminated'
export type AgencyTier = 'bronze' | 'silver' | 'gold' | 'platinum'

export interface Agency {
  id: string
  name: string
  website: string
  contact_email: string
  contact_phone: string
  industry: string
  created_at: string
}

export interface AgencyRelationship {
  id: string
  tenant_id: string
  agency_id: string
  agency: Agency
  status: AgencyStatus
  tier: AgencyTier
  commission_percentage: number
  sla_hours: number
  contract_url: string
  notes: string
  created_at: string
  updated_at: string
}

export interface AgencyAssignment {
  id: string
  tenant_id: string
  agency_id: string
  requisition_id: string
  agency_name: string
  job_title: string
  max_submissions: number
  submissions_count: number
  deadline: string
  status: 'active' | 'closed' | 'paused'
  created_at: string
}

// ─── Candidate Portal ─────────────────────────────────────────────────────────

export interface CandidateApplication {
  id: string
  job_title: string
  company_name: string
  status: ApplicationStatus
  applied_at: string
  current_stage: string
  history: {
    stage: string
    status: string
    changed_at: string
    notes: string
  }[]
}

// ─── Passport ─────────────────────────────────────────────────────────────────

export interface Passport {
  id: string
  candidate_id: string
  headline: string
  summary: string
  current_title: string
  current_company: string
  video_intro_url: string
  linkedin_url: string
  github_url: string
  portfolio_url: string
  skills: string[]
  languages: string[]
  preferred_work_mode: WorkMode | 'any'
  is_actively_looking: boolean
  open_to_work: boolean
  notice_period_days: number
  expected_salary_min: number | null
  expected_salary_max: number | null
  availability_date: string | null
  work_history: PassportWorkExperience[]
  education: PassportEducation[]
  completeness_score: number
  updated_at: string
}

export interface PassportWorkExperience {
  id: string
  company: string
  title: string
  from_date: string
  to_date: string | null
  is_current: boolean
  description: string
  location: string
}

export interface PassportEducation {
  id: string
  institution: string
  degree: string
  field: string
  year: number
  grade?: string
}

// ─── Messaging ───────────────────────────────────────────────────────────────

export interface MessageThread {
  id: string
  tenant_id: string
  subject: string
  participants: string[] // User IDs
  last_message_at: string
  last_message_preview: string
  unread_count: number
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  thread_id: string
  sender_id: string
  body: string
  is_read: boolean
  created_at: string
}

// ─── Notifications ───────────────────────────────────────────────────────────

export interface Notification {
  id: string
  recipient_id: string
  title: string
  body: string
  type: string
  link: string
  is_read: boolean
  created_at: string
}

// ─── Organisation ─────────────────────────────────────────────────────────────

export interface Organisation {
  id: string
  tenant_id: string
  name: string
  industry: string
  size: string
  website: string
  logo_url: string
  description: string
  founded_year: number | null
}

export interface Department {
  id: string
  tenant_id: string
  name: string
  head_id: string | null
  parent_id: string | null
  is_active: boolean
}

export interface Location {
  id: string
  tenant_id: string
  name: string
  city: string
  state: string
  country: string
  is_remote: boolean
  is_active: boolean
}
