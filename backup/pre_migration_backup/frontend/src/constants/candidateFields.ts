/**
 * Canonical Candidate Field Schema
 * ==================================
 * Single source of truth for all candidate form fields:
 * labels, option sets, validation rules, and backend field mapping.
 *
 * Import from here in every form — Quick Add, Detailed Add, Apply Form,
 * Onboarding, Claim Profile, and portal display pages — so the same data
 * is never collected with different names or option values in different places.
 *
 * BACKEND STORAGE MAP
 * ────────────────────────────────────────────────────────────────────────
 * Candidate model   → apps/candidates/models.py  (recruiter-managed record)
 * CandidateProfile  → apps/candidates/models.py  (rich profile detail)
 * TalentPassport    → apps/passport/models.py     (candidate-owned passport)
 * CustomUser        → apps/accounts/models.py     (auth / account)
 *
 * When the same concept maps to BOTH Candidate and Passport (e.g. skills,
 * linkedin_url, notice_period_days) the field must be kept in sync on write.
 * ────────────────────────────────────────────────────────────────────────
 */

// ── Categories ────────────────────────────────────────────────────────────────

/**
 * Full canonical field list, organised by category.
 * Used to validate that every form covers all required fields.
 *
 * Backend columns:
 *   C  = Candidate model
 *   CP = CandidateProfile model
 *   P  = TalentPassport model
 *   U  = CustomUser model
 *   M  = Candidate.metadata (JSON, until promoted to a real column)
 */
export const CANDIDATE_FIELD_MAP = {
  // ── Identity ───────────────────────────────────────────────────────────────
  first_name:         { label: 'First Name',        required: true,  backend: 'C+P+U',  type: 'text' },
  last_name:          { label: 'Last Name',          required: true,  backend: 'C+P+U',  type: 'text' },
  email:              { label: 'Email',              required: false, backend: 'C+U',    type: 'email' },
  phone:              { label: 'Phone',              required: false, backend: 'C+U',    type: 'phone' },
  whatsapp:           { label: 'WhatsApp',           required: false, backend: 'C',      type: 'text' },

  // ── Professional links ─────────────────────────────────────────────────────
  linkedin_url:       { label: 'LinkedIn URL',       required: false, backend: 'C+P',    type: 'url' },
  github_url:         { label: 'GitHub URL',         required: false, backend: 'CP+P',   type: 'url' },
  portfolio_url:      { label: 'Portfolio URL',      required: false, backend: 'CP+P',   type: 'url' },

  // ── Location ───────────────────────────────────────────────────────────────
  current_location_city:    { label: 'Current City',    required: false, backend: 'C+P', type: 'text' },
  current_location_country: { label: 'Current Country', required: false, backend: 'C+P', type: 'select' },

  // ── Professional summary ───────────────────────────────────────────────────
  current_title:      { label: 'Current Job Title',  required: false, backend: 'C+P',   type: 'text' },
  current_company:    { label: 'Current Company',    required: false, backend: 'C+P',   type: 'text' },
  headline:           { label: 'Headline',            required: false, backend: 'P',     type: 'text' },
  summary:            { label: 'Professional Summary', required: false, backend: 'CP+P', type: 'textarea' },

  // ── Experience ─────────────────────────────────────────────────────────────
  experience_years:           { label: 'Total Experience (years)', required: false, backend: 'C+P', type: 'number' },
  relevant_experience_years:  { label: 'Relevant Experience (years)', required: false, backend: 'C', type: 'number' },

  // ── Education ──────────────────────────────────────────────────────────────
  highest_education:  { label: 'Highest Education',  required: false, backend: 'C',     type: 'select' },
  graduation_year:    { label: 'Graduation Year',    required: false, backend: 'C',     type: 'number' },

  // ── Skills ─────────────────────────────────────────────────────────────────
  skills:             { label: 'Skills',              required: false, backend: 'C+P',   type: 'tags' },

  // ── Languages ──────────────────────────────────────────────────────────────
  languages:          { label: 'Languages',           required: false, backend: 'C+P',   type: 'tags' },

  // ── Work authorization / visa / nationality ────────────────────────────────
  nationality:        { label: 'Nationality',         required: false, backend: 'C',     type: 'select' },
  work_authorization: { label: 'Work Authorization',  required: false, backend: 'C',     type: 'select' },
  visa_status:        { label: 'Visa / Permit Type',  required: false, backend: 'C.M',   type: 'text' },
  pr_status:          { label: 'PR / Residency Status', required: false, backend: 'C.M', type: 'text' },

  // ── Availability ───────────────────────────────────────────────────────────
  availability_status:  { label: 'Availability',          required: false, backend: 'C',   type: 'select' },
  notice_period_days:   { label: 'Notice Period (days)',   required: false, backend: 'C+P', type: 'number' },
  last_working_day:     { label: 'Last Working Day',       required: false, backend: 'C',   type: 'date' },
  availability_date:    { label: 'Available From',         required: false, backend: 'C+P', type: 'date' },
  is_actively_looking:  { label: 'Actively Looking',       required: false, backend: 'C+P', type: 'boolean' },
  work_mode_preference: { label: 'Work Mode Preference',   required: false, backend: 'C',   type: 'select',
    note: 'Stored as work_mode_preference on Candidate, preferred_work_mode on Passport — same options' },

  // ── Compensation ───────────────────────────────────────────────────────────
  current_ctc:          { label: 'Current CTC',           required: false, backend: 'C',   type: 'number' },
  current_ctc_currency: { label: 'Current CTC Currency',  required: false, backend: 'C',   type: 'select' },
  expected_salary_min:  { label: 'Expected Salary (Min)', required: false, backend: 'C+P', type: 'number' },
  expected_salary_max:  { label: 'Expected Salary (Max)', required: false, backend: 'C+P', type: 'number' },
  salary_currency:      { label: 'Salary Currency',       required: false, backend: 'C+P', type: 'select' },

  // ── Offer on hand ──────────────────────────────────────────────────────────
  offer_in_hand:        { label: 'Offer in Hand?',        required: false, backend: 'C',   type: 'boolean' },
  offer_in_hand_amount: { label: 'Offer Amount',          required: false, backend: 'C',   type: 'number' },
  offer_currency:       { label: 'Offer Currency',        required: false, backend: 'C.M', type: 'select',
    note: 'Stored in Candidate.metadata.offer_currency until promoted to a dedicated column' },

  // ── Documents ──────────────────────────────────────────────────────────────
  resume_url:           { label: 'Resume / CV Link',      required: false, backend: 'C',   type: 'url',
    note: 'Also synced to CandidateProfile.cv_url and TalentPassport.current_cv_url' },

  // ── Source & tracking ──────────────────────────────────────────────────────
  source:               { label: 'Source',                required: false, backend: 'C',   type: 'select' },
  source_detail:        { label: 'Source Detail',         required: false, backend: 'C',   type: 'text' },
  tags:                 { label: 'Tags',                  required: false, backend: 'C',   type: 'tags' },

  // ── Tenant-level assignment (recruiter UI only) ────────────────────────────
  assigned_to:          { label: 'Assigned Recruiter',    required: false, backend: 'C',   type: 'user-select' },
  owner_user_id:        { label: 'Owner',                 required: false, backend: 'C',   type: 'user-select' },
} as const

// ── Shared option sets ────────────────────────────────────────────────────────
// Import these in every form to guarantee consistent values and labels.

/** Canonical work authorization options. Use these everywhere. */
export const WORK_AUTHORIZATION_OPTIONS = [
  { value: 'citizen',             label: 'Citizen / National' },
  { value: 'permanent_resident',  label: 'Permanent Resident' },
  { value: 'work_visa',           label: 'Work Visa / Work Permit' },
  { value: 'sponsorship_required',label: 'Requires Sponsorship' },
  { value: 'not_specified',       label: 'Prefer not to say' },
]

/** Canonical education level options. */
export const EDUCATION_OPTIONS = [
  { value: 'high_school', label: 'High School / Secondary' },
  { value: 'diploma',     label: 'Diploma / Certificate' },
  { value: 'bachelor',    label: "Bachelor's Degree" },
  { value: 'master',      label: "Master's Degree" },
  { value: 'phd',         label: 'PhD / Doctorate' },
  { value: 'other',       label: 'Other' },
]

/**
 * Canonical work mode options.
 * Used as `work_mode_preference` on the Candidate model and
 * `preferred_work_mode` on the Passport model.
 */
export const WORK_MODE_OPTIONS = [
  { value: 'any',    label: 'Open to Any (Remote / On-site / Hybrid)' },
  { value: 'remote', label: 'Remote Only' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'onsite', label: 'On-site Only' },
]

/** Canonical availability status options. */
export const AVAILABILITY_STATUS_OPTIONS = [
  { value: 'available_now',  label: 'Available Now' },
  { value: 'notice_period',  label: 'Serving Notice Period' },
  { value: 'open_to_offers', label: 'Open to Offers' },
  { value: 'not_looking',    label: 'Not Currently Looking' },
]

/** Canonical notice period select options (days). Used on public forms. */
export const NOTICE_PERIOD_OPTIONS = [
  { value: 0,  label: 'Immediate / No Notice' },
  { value: 15, label: '15 Days' },
  { value: 30, label: '30 Days' },
  { value: 45, label: '45 Days' },
  { value: 60, label: '60 Days' },
  { value: 90, label: '90 Days' },
]

/** Canonical source options for recruiter-facing forms. */
export const SOURCE_OPTIONS = [
  { value: 'self',      label: 'Self Registered' },
  { value: 'agency',    label: 'Agency' },
  { value: 'company',   label: 'Company / Internal' },
  { value: 'linkedin',  label: 'LinkedIn' },
  { value: 'referral',  label: 'Referral' },
  { value: 'job_board', label: 'Job Board' },
  { value: 'passport',  label: 'Talent Passport' },
  { value: 'cafe',      label: 'Interview Café' },
  { value: 'other',     label: 'Other' },
]

/** Pre-defined tag options (recruiter UI only). */
export const TAG_OPTIONS = [
  'Hot Profile', 'Referred', 'Nurture', 'Leadership', 'Urgent', 'Shortlisted',
]

/** Pre-defined language options. */
export const LANGUAGE_OPTIONS = [
  'English', 'Hindi', 'Arabic', 'French', 'German', 'Spanish',
  'Mandarin', 'Portuguese', 'Russian', 'Japanese', 'Korean',
]

// ── Coverage matrix (documentation) ───────────────────────────────────────────
/**
 * Which fields each entry point collects.
 * ✅ = present   ⚠️ = partial/different name   ❌ = missing
 *
 * Field                   | Quick Add | Detailed Add | Apply Form | Onboarding | Register |
 * ─────────────────────────────────────────────────────────────────────────────────────────
 * first_name              |    ✅     |      ✅      |     ✅     |     ✅     |    ✅    |
 * last_name               |    ✅     |      ✅      |     ✅     |     ✅     |    ✅    |
 * email                   |    ✅     |      ✅      |     ✅     |     —      |    ✅    |
 * phone                   |    ✅     |      ✅      |     ✅     |     ✅     |    ✅    |
 * linkedin_url            |    ❌     |      ✅      |     ✅     |     ❌     |    ❌    |
 * current_title           |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
 * current_company         |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
 * current_location_city   |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
 * current_location_country|    ❌     |      ✅      |     ❌     |     ✅     |    ❌    |
 * experience_years        |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
 * relevant_exp_years      |    ❌     |      ❌      |     ✅     |     ❌     |    ❌    |
 * highest_education       |    ❌     |      ❌      |     ✅     |     ❌     |    ❌    |
 * graduation_year         |    ❌     |      ❌      |     ✅     |     ❌     |    ❌    |
 * skills                  |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
 * languages               |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
 * nationality             |    ❌     |      ✅      |     ✅     |     ❌     |    ❌    |
 * work_authorization      |    ❌     |   ⚠️ diff   |  ⚠️ diff  |     ❌     |    ❌    |
 * availability_status     |    ❌     |      ❌      |     ✅     |     ❌     |    ❌    |
 * notice_period_days      |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
 * last_working_day        |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
 * is_actively_looking     |    ❌     |      ✅      |     ❌     |     ✅     |    ❌    |
 * work_mode_preference    |    ❌     |      ❌      |     ✅     |     ✅     |    ❌    |
 * expected_salary_min     |    ❌     |      ✅      |     ❌     |     ✅     |    ❌    |
 * expected_salary_max     |    ❌     |      ✅      |     ❌     |     ✅     |    ❌    |
 * salary_currency         |    ❌     |      ✅      |     ❌     |     ✅     |    ❌    |
 * offer_in_hand           |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
 * offer_in_hand_amount    |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
 * resume_url              |    ✅     |      ✅      |     ✅     |     ✅     |    ❌    |
 * source                  |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
 * source_detail           |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
 * tags                    |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
 */
