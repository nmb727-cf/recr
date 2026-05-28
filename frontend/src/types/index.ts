// ─── Auth ─────────────────────────────────────────────────────────────────────

export type UserRole =
  | 'super_admin'
  | 'tenant_admin'
  | 'hr_manager'
  | 'recruiter'
  | 'hiring_manager'
  | 'interviewer'
  | 'viewer'
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
  phone_country_code?: string
  phone_number?: string
  avatar_url: string
  role: UserRole
  is_super_admin?: boolean
  is_superuser?: boolean
  is_staff?: boolean
  is_active: boolean
  email_verified: boolean
  mfa_enabled: boolean
  timezone: string
  language: string
  tenant_id: string
  created_at: string
  last_login_at: string
  permissions: string[]
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
  name: string // Company Name
  first_name: string
  last_name: string
  email: string
  password: string
  password_confirm: string
  country_code?: string
  timezone?: string
}

export interface RegisterAgencyPayload {
  name: string // Agency Name
  first_name: string
  last_name: string
  email: string
  password: string
  password_confirm: string
  country_code?: string
  timezone?: string
}

export interface RegisterCandidatePayload {
  first_name: string
  last_name: string
  email: string
  password: string
  password_confirm: string
  phone?: string
  timezone?: string
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
  | 'paused'
  | 'in_guarantee_period'
  | 'closed'
  | 'cancelled'
export type Priority = 'low' | 'medium' | 'high' | 'urgent'
export type SourcingMode = 'internal' | 'external' | 'hybrid'

export interface JobRequisition {
  id: string
  job_ref_id?: string
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
  hiring_status?: 'active_hiring' | 'hiring_complete' | 'in_guarantee_period' | 'replacement_required' | 'fully_closed'
  guarantee_watch_until?: string | null
  sourcing_mode: SourcingMode
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
  stage_type: string
  action_deadline_hours: number
  is_active: boolean
  is_mandatory?: boolean
  is_critical_path?: boolean
  stage_zone?: string
  trigger_type?: string
  responsible_role?: string
  responsible_user_id?: string | null
  decision_authority?: string
  metadata?: Record<string, unknown>
}

// ─── Candidates ───────────────────────────────────────────────────────────────

export interface Candidate {
  id: string
  candidate_ref_id?: string
  tenant_id: string
  first_name: string
  last_name: string
  full_name: string
  email: string
  phone: string
  phone_country_code?: string
  phone_number?: string
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
  created_at?: string
  updated_at: string
  created_by: string
  metadata: Record<string, unknown>
  // Protection fields
  is_agency_protected?: boolean
  protected_until?: string
  protection_scope?: string
}

export type WorkflowMode = 'manual' | 'semi_automated' | 'fully_automated'

export interface CandidateSmartRow {
  id: string
  candidate_ref_id?: string
  created_at?: string | null
  name: string
  current_title?: string
  company?: string
  experience?: number | null
  location?: string
  source?: string
  source_type?: string
  engagement_stage?: string
  owner?: string | null
  owner_name?: string | null
  last_touch?: string | null
  last_activity?: string | null
  signals: {
    readiness_score?: number | null
    fit_score?: number | null
    completeness_score?: number | null
    warning_signals?: string[]
  }
  job_engagement_summary?: Record<string, number>
  skills?: string[]
  pools?: string[]
  resume_url?: string | null
  passport_linked?: boolean
  is_duplicate?: boolean
  notice_period_days?: number | null
  availability_status?: string | null
  open_engagements?: number
  email?: string
  phone?: string
  tags?: string[]
  expected_salary_min?: number | null
  expected_salary_max?: number | null
  salary_currency?: string
  // Protection fields
  is_agency_protected?: boolean
  protected_until?: string
  protection_scope?: string
}

export interface CandidateSavedView {
  key: string
  label: string
  count: number
}

export interface CandidateWorkflowPolicy {
  id: string
  tenant_id: string
  team_id: string | null
  recruiter_user_id: string | null
  default_candidate_workflow_mode: WorkflowMode
  candidate_auto_assignment_mode: 'manual' | 'round_robin' | 'rule_based'
  candidate_auto_followup_mode: 'manual' | 'suggest_only' | 'automatic'
  candidate_auto_nurture_days: number
  candidate_stale_days: number
  candidate_focus_rules: Record<string, unknown>
  candidate_stage_templates: unknown[]
  candidate_required_fields_policy: Record<string, unknown>
  candidate_scoring_policy: Record<string, unknown>
  candidate_active_work_policy: Record<string, unknown>
  is_active: boolean
  metadata: Record<string, unknown>
}

export interface WorkflowBehavior {
  mode: WorkflowMode
  auto_actions_enabled: boolean
  suggestions_enabled: boolean
  user_approval_required: boolean
}

export interface ActiveWorkEngagement {
  id: string
  candidate: string
  candidate_name: string
  candidate_ref_id?: string
  job?: string | null
  job_title?: string | null
  stage: string
  priority: 'hot' | 'warm' | 'cold'
  is_active: boolean
  follow_up_at?: string | null
  last_activity_at?: string | null
  owner_name?: string | null
}

export interface CandidateCommandCenter {
  candidate: CandidateDetail
  tabs: {
    overview: Candidate
    activity_timeline: Array<Record<string, any>>
    structured_activity?: Array<{
      candidate_id: string
      engagement_id?: string | null
      actor_id?: string | null
      actor_type: string
      action_type: string
      context_type: 'job' | 'general'
      method: 'manual' | 'email' | 'system' | string
      metadata_json: Record<string, any>
      created_at: string
      actor?: string
    }>
    notes: CandidateNote[]
    structured_notes?: Array<{
      candidate_id: string
      engagement_id?: string | null
      author_id?: string | null
      author?: string
      note_type: string
      content: string
      context_type: 'job' | 'general'
      created_at: string
    }>
    jobs_matches: Array<{ job_id: string; stage: string }>
    engagement: ActiveWorkEngagement[]
    documents: {
      resume_url?: string
      profile_cv_url?: string
    }
    communication: {
      last_contact_at?: string | null
      next_follow_up_at?: string | null
    }
    history: Array<Record<string, any>>
    automations: {
      workflow_mode: WorkflowMode
      automation_enabled: boolean
      auto_nurture_enabled: boolean
      auto_followup_enabled: boolean
      auto_stage_suggestions_enabled: boolean
      behavior: WorkflowBehavior
    }
  }
  sticky_actions: string[]
}

export interface Engagement {
  id: string
  tenant_id?: string
  candidate: string
  candidate_name?: string
  stage: string
  priority: 'hot' | 'warm' | 'cold'
  is_active: boolean
  follow_up_at?: string | null
  last_activity_at?: string | null
  job?: string | null
  job_title?: string | null
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

export type ApplicationStatus = string

export type PlacementStatus =
  | 'not_applicable'
  | 'pending_join'
  | 'joined'
  | 'placement_confirmed'
  | 'cancelled'

export type CommissionStatus =
  | 'not_applicable'
  | 'pending_calculation'
  | 'calculated'
  | 'awaiting_payment_tracking'
  | 'cancelled'

export type CommissionBasisType =
  | 'inherited_from_relationship'
  | 'custom_job_rule'
  | 'percentage'
  | 'fixed'
  | 'milestone'

export type SubmissionStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'submitted'
  | 'rejected_internally'
  | 'returned'

export interface Application {
  id: string
  tenant_id: string
  candidate_id: string
  requisition_id: string
  current_stage_id: string | null
  status: ApplicationStatus
  governance_status?: SubmissionStatus
  placement_status?: PlacementStatus
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
  expected_joining_date?: string | null
  placement_confirmed_at?: string | null
  placement_notes?: string | null
  // Commission Foundation
  commission_applicable?: boolean
  commission_basis_type?: CommissionBasisType
  commission_value?: number
  expected_commission_amount?: number
  commission_currency?: string
  commission_status?: CommissionStatus
  commission_rule_source?: string
  commission_notes?: string
  application_form_data: Record<string, unknown>
  created_at: string
  updated_at: string
  created_by: string
  metadata: Record<string, unknown>
  is_under_guarantee?: boolean
  guarantee_end_date?: string | null
  guarantee_start_date?: string | null
  guarantee_status?: string | null
  guarantee_resolution_type?: string | null
  refund_mode?: string | null
  refund_percentage?: number | null
  replacement_attempt_limit?: string | null
  is_agency_protected?: boolean
  protected_until?: string | null
  protection_scope?: string | null
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
  | 'async_interview'
  | 'hr_round'

export type InterviewStatus =
  | 'scheduled'
  | 'confirmed'
  | 'rescheduled'
  | 'in_progress'
  | 'paused'
  | 'completed'
  | 'cancelled'
  | 'no_show'
  | 'pending_feedback'
  | 'awaiting_feedback'
  | 'awaiting_decision'
  | 'rejected'

export type ThresholdAction = 'pass' | 'reject' | 'manual_review'

export interface ThresholdRule {
  min_score: number
  max_score: number
  action: ThresholdAction
}

export interface InterviewRoundConfig {
  id: string
  name: string
  type: InterviewType | string
  template_id?: string
  order: number
  evaluator_type: 'hiring_manager' | 'recruiter' | 'interviewer' | 'external_agency' | 'ai'
  threshold_score: number
  threshold_rules?: ThresholdRule[]
  auto_pass_enabled: boolean
  auto_reject_enabled: boolean
  manual_review_required: boolean
  linked_stage_id?: string // Mapping to JobStage
}

export interface InterviewPackage {
  id: string
  tenant_id: string
  title: string
  description: string
  is_active: boolean
  rounds: InterviewRoundConfig[]
  created_at: string
  updated_at: string
  created_by: string
}

export interface InterviewPackageBinding {
  id: string
  job_id: string
  package_id: string
  package_title: string
  rounds_summary: InterviewRoundConfig[]
  effective_rounds: InterviewRoundConfig[]
  rounds_override: InterviewRoundConfig[]
  automation_enabled: boolean
  auto_pass_enabled: boolean
  auto_reject_enabled: boolean
  manual_review_required: boolean
  created_at: string
  updated_at: string
}

export interface Interview {
  id: string
  tenant_id: string
  application_id: string
  candidate_id: string
  requisition_id: string
  interview_type: string
  title: string
  scheduled_at: string
  duration_minutes: number
  interview_round: number
  location_type: 'online' | 'office' | 'other'
  location_detail: string
  meeting_link: string
  interview_link: string
  meeting_id: string
  status: InterviewStatus
  feedback_average_score: number | null
  feedback_count: number
  recommendation?: string
  interviewers: string[] // User IDs
  candidate_notified: boolean
  interviewers_notified: boolean
  is_active: boolean
  decision?: any
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
  agency?: Agency
  agency_tenant_id?: string | null
  company_tenant_id?: string | null
  company_name?: string
  agency_name?: string
  status: AgencyStatus
  tier: AgencyTier
  commission_percentage: number
  commission_type?: 'percentage' | 'fixed' | 'milestone'
  sla_hours: number
  sla_submission_hours?: number
  sla_feedback_hours?: number
  contract_url: string
  contract_start_date?: string | null
  contract_end_date?: string | null
  contract_file_url?: string
  recruitment_policy_url?: string
  notes: string
  retention_enabled?: boolean
  retention_days?: number
  retention_start_type?: string
  retention_scope?: string
  retention_post_expiry?: string
  replacement_guarantee_enabled?: boolean
  guarantee_period_days?: number
  guarantee_start_type?: string
  guarantee_resolution_type?: string
  refund_mode?: string
  refund_percentage?: number | null
  replacement_attempt_limit?: string
  guarantee_notes?: string
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
  assigned_by?: string
  assigned_at?: string
  notes?: string
  internal_recruiter_id?: string
  governance_mode?: 'direct' | 'approval_required'
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
  user_id?: string
  candidate_id: string | null
  passport_number?: string
  is_active?: boolean

  // Profile
  headline: string
  summary: string
  profile_photo_url?: string
  cover_image_url?: string
  video_intro_url: string

  // Professional
  current_title: string
  current_company?: string
  current_location_city?: string
  current_location_country?: string
  experience_years?: number

  // CV
  current_cv_url?: string
  current_cv_filename?: string

  // Sections
  work_history: PassportWorkExperience[]
  education: PassportEducation[]
  skills: string[]
  languages: string[]
  certifications?: PassportCertification[]
  projects?: PassportProject[]
  publications?: PassportPublication[]
  awards?: PassportAward[]
  volunteer_work?: PassportVolunteer[]

  // Social
  linkedin_url: string
  github_url: string
  portfolio_url: string
  twitter_url?: string
  behance_url?: string
  dribbble_url?: string

  // Preferences
  preferred_locations?: string[]
  preferred_work_mode: WorkMode | 'any' | ''
  preferred_job_types?: string[]
  preferred_industries?: string[]
  expected_salary_min: number | null
  expected_salary_max: number | null
  salary_currency?: string
  notice_period_days: number | null
  availability_date: string | null
  is_actively_looking: boolean
  open_to_work: boolean

  // Verification (read-only — set by platform)
  identity_verified?: boolean
  background_verified?: boolean
  employment_verified?: boolean
  education_verified?: boolean

  // Scores (read-only)
  heat_score?: number
  completeness_score: number
  market_demand_score?: number
  view_count?: number

  // Editable by candidate
  visibility_settings?: Record<string, boolean>
  metadata?: Record<string, unknown>

  created_at?: string
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
  location?: string
}

export interface PassportEducation {
  id: string
  institution: string
  degree: string
  field: string
  year: number
  grade?: string
}

export interface PassportCertification {
  id: string
  name: string
  issuer: string
  issued_date?: string | null
  expiry_date?: string | null
  credential_id?: string
  credential_url?: string
}

export interface PassportProject {
  id: string
  name: string
  description: string
  url?: string
  from_date?: string | null
  to_date?: string | null
  skills?: string[]
}

export interface PassportPublication {
  id: string
  title: string
  publisher?: string
  published_date?: string | null
  url?: string
  description?: string
}

export interface PassportAward {
  id: string
  title: string
  issuer?: string
  date?: string | null
  description?: string
}

export interface PassportVolunteer {
  id: string
  role: string
  organisation: string
  from_date?: string | null
  to_date?: string | null
  is_current?: boolean
  description?: string
}

// ─── Messaging ───────────────────────────────────────────────────────────────

export interface MessageThread {
  id: string
  tenant_id: string
  subject: string
  participants: string[] | Array<{ id?: string; user_id?: string }> // legacy + new shape
  participant_ids?: string[]
  last_message_at: string | null
  last_message_preview: string
  unread_count: number
  created_at: string
  updated_at: string
  thread_type?: string
  is_internal?: boolean
  is_archived?: boolean
  metadata?: Record<string, unknown>
}

export interface Message {
  id: string
  thread_id?: string
  tenant_id?: string
  sender_id: string
  sender_tenant_id?: string
  body: string
  content?: string
  message_type?: string
  channel_type?: string
  attachments_json?: unknown[]
  attachments?: unknown[]
  is_read: boolean
  created_at?: string
  sent_at?: string
  read_at?: string | null
  metadata?: Record<string, unknown>
}

// ─── Notifications ───────────────────────────────────────────────────────────

export interface Notification {
  id: string
  recipient_id?: string
  user_id?: string
  tenant_id?: string | null
  title: string
  body: string
  type: string
  notification_type?: string
  link?: string
  action_url?: string
  severity?: 'info' | 'medium' | 'high' | 'critical'
  is_read: boolean
  created_at: string
  read_at?: string | null
  related_entity_type?: string
  related_entity_id?: string | null
  metadata?: Record<string, unknown>
}

// ─── Organisation ─────────────────────────────────────────────────────────────

export interface Organisation {
  id: string
  tenant_id: string
  name: string
  org_type?: string
  industry: string
  size?: string
  size_range?: string
  website: string
  logo_url: string
  description: string
  country_code?: string
  timezone?: string
  settings?: Record<string, unknown>
  reference_prefix_auto?: string
  reference_prefix_custom?: string
  effective_reference_prefix?: string
  founded_year: number | null
  metadata: Record<string, unknown>
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
