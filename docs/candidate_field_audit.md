# Candidate Data Audit — Step 1: DB Field Inventory
**Date:** 2026-03-26
**Status:** Review only — no code changes

---

## Section 1: Candidate DB Field Inventory

### 1.1 Table: `candidates_candidate`
Model: `apps/candidates/models.py → Candidate`
Scope: Tenant-level (tenant_id nullable — null = self-registered candidate without a tenant)

| Field | Type | Purpose | Scope | Editable By | API Exposed |
|---|---|---|---|---|---|
| `id` | UUIDField (PK) | Primary key | global | system | ✅ |
| `tenant_id` | UUIDField (nullable) | Owning tenant; null = self-registered | tenant | system | ✅ |
| `first_name` | CharField(100) | Given name | tenant | candidate, recruiter | ✅ |
| `last_name` | CharField(100) | Family name | tenant | candidate, recruiter | ✅ |
| `full_name` | @property | Computed: first + last | — | system | ✅ (computed) |
| `email` | EmailField | Primary email | tenant | candidate, recruiter | ✅ |
| `phone` | CharField(20) | Raw phone string (legacy) | tenant | candidate, recruiter | ✅ |
| `phone_country_code` | CharField(10) | ISO country code for phone, default 'IN' | tenant | candidate, recruiter | ❌ |
| `phone_number` | CharField(20) | Normalized local number | tenant | candidate, recruiter | ❌ |
| `whatsapp` | CharField(20) | WhatsApp number | tenant | candidate, recruiter | ✅ |
| `linkedin_url` | TextField | LinkedIn profile URL | tenant | candidate, recruiter | ✅ |
| `current_title` | CharField(255) | Current job title | tenant | candidate, recruiter | ✅ |
| `current_company` | CharField(255) | Current employer | tenant | candidate, recruiter | ✅ |
| `current_location_city` | CharField(100) | City of residence | tenant | candidate, recruiter | ✅ |
| `current_location_country` | CharField(100) | Country of residence | tenant | candidate, recruiter | ✅ |
| `experience_years` | Decimal(4,1) | Total experience in years | tenant | candidate, recruiter | ✅ |
| `designation` | CharField(255) | Internal designation/level label | tenant | recruiter | ✅ |
| `relevant_experience_years` | Decimal(4,1) | Relevant (domain-specific) experience | tenant | candidate, recruiter | ✅ |
| `current_ctc` | Decimal(15,2) | Current compensation | tenant | recruiter | ✅ |
| `current_ctc_currency` | CharField(10) | Currency of current CTC, default 'INR' | tenant | recruiter | ✅ |
| `offer_in_hand` | BooleanField | Whether candidate has a competing offer | tenant | recruiter | ✅ |
| `offer_in_hand_amount` | Decimal(15,2) | Amount of competing offer | tenant | recruiter | ✅ |
| `counter_offer` | Decimal(15,2) | Counter offer amount made | tenant | recruiter | ✅ |
| `availability_status` | CharField(50) | Choices: available_now, notice_period, open_to_offers, not_looking | tenant | candidate, recruiter | ✅ |
| `last_working_day` | DateField | Last day at current employer | tenant | candidate, recruiter | ✅ |
| `work_mode_preference` | CharField(20) | any/remote/hybrid/onsite | tenant | candidate, recruiter | ✅ |
| `fitment_score` | IntegerField | Recruiter manual fitment rating | tenant | recruiter | ✅ |
| `profile_status` | CharField(20) | draft/partial/complete/claimed | tenant | system | ✅ |
| `initial_entry_type` | CharField(20) | How the record was first created | tenant | system | ✅ |
| `claim_token` | CharField(100) | Token for candidate to claim their record | tenant | system | ❌ |
| `claim_token_expires_at` | DateTimeField | Expiry of claim token | tenant | system | ❌ |
| `claimed_at` | DateTimeField | When candidate claimed their record | tenant | system | ✅ |
| `account_status` | CharField(20) | none/invited/claimed/active | tenant | system | ✅ |
| `invite_sent_at` | DateTimeField | When invite was last sent | tenant | system | ✅ |
| `expected_salary_min` | Decimal(15,2) | Minimum expected salary | tenant | candidate, recruiter | ✅ |
| `expected_salary_max` | Decimal(15,2) | Maximum expected salary | tenant | candidate, recruiter | ✅ |
| `salary_currency` | CharField(10) | Currency for expected salary, default 'INR' | tenant | candidate, recruiter | ✅ |
| `notice_period_days` | IntegerField | Notice period in calendar days | tenant | candidate, recruiter | ✅ |
| `availability_date` | DateField | Date available to start | tenant | candidate, recruiter | ✅ |
| `is_actively_looking` | BooleanField | Whether actively seeking new role | tenant | candidate, recruiter | ✅ |
| `nationality` | CharField(100) | Country of citizenship | tenant | candidate, recruiter | ❌ (in serializer?) |
| `work_authorization` | CharField(50) | citizen/permanent_resident/work_visa/sponsorship_required/not_specified | tenant | candidate, recruiter | ❌ (in serializer?) |
| `highest_education` | CharField(50) | high_school/diploma/bachelor/master/phd/other | tenant | candidate, recruiter | ❌ |
| `graduation_year` | IntegerField | Year of highest degree completion | tenant | candidate, recruiter | ❌ |
| `relocation_willing` | CharField(50) | Free-text / flag for relocation willingness | tenant | candidate, recruiter | ❌ |
| `preferred_locations` | JSONField (list) | List of preferred work locations | tenant | candidate, recruiter | ❌ |
| `resume_url` | TextField | Direct URL to stored resume file | tenant | candidate, recruiter | ✅ |
| `source` | CharField(100) | How candidate was acquired: self/agency/linkedin/etc | tenant | recruiter | ✅ |
| `source_detail` | TextField | Free-text detail about source | tenant | recruiter | ✅ |
| `workflow_mode` | CharField(30) | manual/semi_automated/fully_automated | tenant | recruiter, system | ✅ |
| `source_type` | CharField(50) | direct/agency/referral/job_board/passport/import/internal/other | tenant | system | ✅ |
| `source_subtype` | CharField(100) | Sub-category of source | tenant | system | ✅ |
| `lifecycle_state` | CharField(30) | new/active/nurture/dormant/archived | tenant | system | ✅ |
| `engagement_stage` | CharField(30) | Current general track stage (synced from engagement) | tenant | system | ✅ |
| `priority_level` | CharField(20) | low/medium/high/urgent | tenant | recruiter | ✅ |
| `readiness_score` | IntegerField | System-computed readiness to move | tenant | system | ✅ |
| `fit_score` | IntegerField | Computed fit for any job | tenant | system | ✅ |
| `profile_completeness` | PositiveSmallIntegerField | 0–100 percentage | tenant | system | ✅ |
| `is_in_active_work` | BooleanField | Whether in recruiter active work queue | tenant | system | ✅ |
| `active_job_id` | UUIDField | FK to currently active JobRequisition | tenant | system | ✅ |
| `next_follow_up_at` | DateTimeField | Scheduled follow-up datetime | tenant | recruiter | ✅ |
| `last_contact_at` | DateTimeField | Last time recruiter contacted candidate | tenant | system | ✅ |
| `last_activity_at` | DateTimeField | Last system or user activity | tenant | system | ✅ |
| `passport_linked` | BooleanField | Whether candidate has linked a TalentPassport | global | system | ✅ |
| `passport_visibility_mode` | CharField(30) | internal_only/shared_with_client/private | tenant | recruiter | ✅ |
| `automation_enabled` | BooleanField | Global automation toggle for this candidate | tenant | recruiter | ✅ |
| `auto_nurture_enabled` | BooleanField | Auto-nurture sequences enabled | tenant | recruiter | ✅ |
| `auto_followup_enabled` | BooleanField | Auto follow-up enabled | tenant | recruiter | ✅ |
| `auto_stage_suggestions_enabled` | BooleanField | AI stage suggestions enabled | tenant | recruiter | ✅ |
| `duplicate_review_status` | CharField(30) | not_flagged/pending_review/confirmed_duplicate/merged/ignored | tenant | system, recruiter | ✅ |
| `passport_id` | UUIDField | FK to TalentPassport record | global | system | ✅ |
| `duplicate_of` | UUIDField | FK to canonical candidate if this is a duplicate | tenant | system | ✅ (read-only) |
| `is_duplicate` | BooleanField | Whether flagged as duplicate | tenant | system | ✅ (read-only) |
| `global_hash` | CharField(64) | SHA-256 of normalized email+phone for cross-tenant deduplication | global | system | ❌ |
| `tags` | JSONField (list) | Free-form recruiter/system tags | tenant | recruiter | ✅ |
| `skills` | JSONField (list) | Skill strings (flat, from all sources) | tenant | candidate, recruiter | ✅ |
| `languages` | JSONField (list) | Language strings | tenant | candidate, recruiter | ✅ |
| `assigned_to` | UUIDField | User currently responsible for this candidate | tenant | recruiter | ✅ |
| `owner_user_id` | UUIDField | User who originally sourced | tenant | recruiter | ✅ |
| `owner_tenant_id` | UUIDField | Tenant of the sourcing user | tenant | system | ✅ |
| `created_at` | DateTimeField | Record creation timestamp | tenant | system | ✅ (read-only) |
| `updated_at` | DateTimeField | Record last-modified timestamp | tenant | system | ✅ (read-only) |
| `created_by` | UUIDField | User who created the record | tenant | system | ✅ |
| `is_deleted` | BooleanField | Soft delete flag | tenant | system | ❌ |
| `deleted_at` | DateTimeField | Soft delete timestamp | tenant | system | ❌ |
| `metadata` | JSONField (dict) | Arbitrary extension data | tenant | system | ✅ |
| `candidate_state` | CharField(30) | NEW_LEAD/JOB_ASSOCIATED/REVIVED | tenant | system | ✅ |
| `candidate_pool` | CharField(20) | GENERAL/NONE | tenant | system | ✅ |
| `is_general_pool_used` | BooleanField | Whether candidate has ever been in job track | tenant | system | ✅ |

**Fields missing from CandidateSerializer (in DB but NOT exposed):**
- `phone_country_code`
- `phone_number`
- `nationality`
- `work_authorization`
- `highest_education`
- `graduation_year`
- `relocation_willing`
- `preferred_locations`
- `global_hash`
- `claim_token` *(intentionally omitted for security)*
- `claim_token_expires_at` *(intentionally omitted)*
- `is_deleted` *(intentionally omitted)*
- `deleted_at` *(intentionally omitted)*

---

### 1.2 Table: `candidates_profile`
Model: `apps/candidates/models.py → CandidateProfile`
Scope: Tenant-level, one-to-one with Candidate via `candidate_id`

| Field | Type | Purpose | Editable By | API Exposed |
|---|---|---|---|---|
| `id` | UUIDField (PK) | Primary key | system | ✅ |
| `tenant_id` | UUIDField | Owning tenant | system | ❌ (not in serializer) |
| `candidate_id` | UUIDField (unique) | FK to Candidate | system | ✅ (read-only) |
| `summary` | TextField | Professional bio / bio paragraph | candidate, recruiter | ✅ |
| `work_experience` | JSONField (list) | Structured work history entries | candidate, recruiter | ✅ |
| `education` | JSONField (list) | Structured education entries | candidate, recruiter | ✅ |
| `certifications` | JSONField (list) | Certification list | candidate, recruiter | ✅ |
| `projects` | JSONField (list) | Project portfolio entries | candidate, recruiter | ✅ |
| `publications` | JSONField (list) | Publications list | candidate, recruiter | ✅ |
| `awards` | JSONField (list) | Awards and recognition | candidate, recruiter | ✅ |
| `references` | JSONField (list) | Professional references | candidate, recruiter | ✅ |
| `cv_url` | TextField | URL to parsed/stored CV in profile | candidate, recruiter | ✅ |
| `cv_parsed_data` | JSONField (dict) | Machine-parsed CV data | system | ✅ |
| `cv_uploaded_at` | DateTimeField | When CV was uploaded | system | ✅ |
| `portfolio_url` | TextField | Portfolio website URL | candidate, recruiter | ✅ |
| `github_url` | TextField | GitHub profile URL | candidate, recruiter | ✅ |
| `stackoverflow_url` | TextField | Stack Overflow profile URL | candidate, recruiter | ✅ |
| `created_at` | DateTimeField | Record creation | system | ✅ (read-only) |
| `updated_at` | DateTimeField | Record last-modified | system | ✅ (read-only) |
| `created_by` | UUIDField | Creating user | system | ❌ (not in serializer) |
| `is_deleted` | BooleanField | Soft delete flag | system | ❌ |
| `deleted_at` | DateTimeField | Soft delete timestamp | system | ❌ |
| `metadata` | JSONField (dict) | Extension data | system | ✅ |

**Note:** `CandidateProfile` is only fetched and returned when using `CandidateDetailSerializer` or `CandidateCommandCenterView`. The `CandidateListView` and `CandidateDatabaseView` do NOT return profile data at all.

---

### 1.3 Table: `passport_talent_passport`
Model: `apps/passport/models.py → TalentPassport`
Scope: Global (not tenant-bound — belongs to the candidate user, shared across tenants)

| Field | Type | Purpose | Editable By | API Exposed |
|---|---|---|---|---|
| `id` | UUIDField (PK) | Primary key | system | ✅ |
| `user_id` | UUIDField (unique) | FK to auth user | system | ✅ |
| `candidate_id` | UUIDField | FK to Candidate (populated on import) | system | ✅ |
| `passport_number` | CharField(50) (unique) | Human-readable identifier (TP + hex) | system | ✅ |
| `share_link_token` | CharField(100) (unique) | Secure shareable link token | system | ❌ (not in TalentPassportSerializer) |
| `is_active` | BooleanField | Whether passport is enabled | system | ✅ |
| `headline` | CharField(255) | Professional headline / tagline | candidate | ✅ |
| `summary` | TextField | Professional summary paragraph | candidate | ✅ |
| `profile_photo_url` | TextField | Profile picture URL | candidate | ✅ |
| `cover_image_url` | TextField | Cover image URL | candidate | ✅ |
| `video_intro_url` | TextField | Video introduction URL | candidate | ✅ |
| `current_title` | CharField(255) | Current job title | candidate | ✅ |
| `current_company` | CharField(255) | Current employer | candidate | ✅ |
| `current_location_city` | CharField(100) | City | candidate | ✅ |
| `current_location_country` | CharField(100) | Country | candidate | ✅ |
| `experience_years` | Decimal(4,1) | Total experience years | candidate | ✅ |
| `current_cv_url` | TextField | Current CV file URL | candidate | ✅ |
| `current_cv_filename` | CharField(255) | CV filename | candidate | ✅ |
| `current_cv_uploaded_at` | DateTimeField | CV upload timestamp | system | ✅ |
| `cv_parsed_data` | JSONField | Machine-parsed CV data | system | ✅ |
| `work_history` | JSONField (list) | Structured work history | candidate | ✅ |
| `education` | JSONField (list) | Structured education | candidate | ✅ |
| `skills` | JSONField (list) | Skills list | candidate | ✅ |
| `certifications` | JSONField (list) | Certifications | candidate | ✅ |
| `projects` | JSONField (list) | Projects | candidate | ✅ |
| `publications` | JSONField (list) | Publications | candidate | ✅ |
| `awards` | JSONField (list) | Awards | candidate | ✅ |
| `volunteer_work` | JSONField (list) | Volunteer history | candidate | ✅ |
| `test_scores` | JSONField (list) | Test / exam scores | candidate | ✅ |
| `featured_media` | JSONField (list) | Featured media items | candidate | ❌ (not in TalentPassportSerializer) |
| `languages` | JSONField (list) | Languages spoken | candidate | ✅ |
| `references` | JSONField (list) | References | candidate | ✅ |
| `linkedin_url` | TextField | LinkedIn | candidate | ✅ |
| `github_url` | TextField | GitHub | candidate | ✅ |
| `portfolio_url` | TextField | Portfolio | candidate | ✅ |
| `twitter_url` | TextField | Twitter/X | candidate | ✅ |
| `behance_url` | TextField | Behance | candidate | ✅ |
| `dribbble_url` | TextField | Dribbble | candidate | ✅ |
| `other_social_urls` | JSONField (dict) | Any other social links | candidate | ❌ (not in TalentPassportSerializer) |
| `preferred_locations` | JSONField (list) | Preferred work locations | candidate | ✅ |
| `preferred_work_mode` | CharField(50) | onsite/remote/hybrid/any | candidate | ✅ |
| `preferred_job_types` | JSONField (list) | e.g. full-time, contract | candidate | ✅ |
| `preferred_industries` | JSONField (list) | Preferred industries | candidate | ✅ |
| `expected_salary_min` | Decimal(15,2) | Min expected salary | candidate | ✅ |
| `expected_salary_max` | Decimal(15,2) | Max expected salary | candidate | ✅ |
| `salary_currency` | CharField(10) | Salary currency | candidate | ✅ |
| `notice_period_days` | IntegerField | Notice period | candidate | ✅ |
| `availability_date` | DateField | Start availability | candidate | ✅ |
| `is_actively_looking` | BooleanField | Actively seeking | candidate | ✅ |
| `open_to_work` | BooleanField | Open to work flag | candidate | ✅ |
| `identity_verified` | BooleanField | Identity verified by system | system | ✅ (read-only) |
| `identity_verified_at` | DateTimeField | When verified | system | ❌ (not in serializer) |
| `background_verified` | BooleanField | Background check done | system | ✅ (read-only) |
| `employment_verified` | BooleanField | Employment verification done | system | ✅ (read-only) |
| `education_verified` | BooleanField | Education verification done | system | ✅ (read-only) |
| `interview_scores` | JSONField (list) | Historical interview scores | system | ❌ (not in TalentPassportSerializer) |
| `assessment_results` | JSONField (list) | Assessment outcomes | system | ❌ (not in TalentPassportSerializer) |
| `heat_score` | Decimal(5,2) | Algorithmic heat / desirability score | system | ✅ (read-only) |
| `completeness_score` | Decimal(5,2) | Profile completeness 0–100 | system | ✅ (read-only) |
| `market_demand_score` | Decimal(5,2) | Market demand score | system | ✅ (read-only) |
| `visibility_settings` | JSONField (dict) | Privacy per-field settings | candidate | ✅ |
| `view_count` | IntegerField | How many times passport was viewed | system | ✅ (read-only) |
| `last_viewed_at` | DateTimeField | Last view timestamp | system | ✅ |
| `created_at` | DateTimeField | Creation timestamp | system | ✅ |
| `updated_at` | DateTimeField | Last modified | system | ✅ |
| `is_deleted` | BooleanField | Soft delete | system | ❌ |
| `deleted_at` | DateTimeField | Soft delete timestamp | system | ❌ |
| `metadata` | JSONField | Extension data | system | ❌ (not in TalentPassportSerializer) |

**Fields in DB but missing from `TalentPassportSerializer`:**
- `share_link_token`
- `featured_media`
- `other_social_urls`
- `identity_verified_at`
- `interview_scores`
- `assessment_results`
- `metadata`

---

### 1.4 Table: `pipeline_application`
Model: `apps/pipeline/models.py → Application`
Scope: Tenant-level, links Candidate to JobRequisition

| Field | Type | Purpose | Editable By | API Exposed (candidate-relevant) |
|---|---|---|---|---|
| `id` | UUIDField (PK) | Primary key | system | ✅ |
| `tenant_id` | UUIDField | Owning tenant | system | ✅ |
| `candidate_id` | UUIDField | FK to Candidate | system | ✅ |
| `requisition_id` | UUIDField | FK to JobRequisition | system | ✅ |
| `status` | CharField(50) | applied/screening/shortlisted/interview/assessment/offer/joined/rejected/withdrawn/on_hold | system | ✅ |
| `source` | CharField(100) | How application was submitted | system | ✅ |
| `match_score` | Decimal(5,2) | AI/system match score | system | ✅ |
| `rejection_reason` | TextField | Why rejected | recruiter | ✅ |
| `rejection_category` | CharField(100) | Category of rejection | recruiter | ✅ |
| `withdrawn_reason` | TextField | Why withdrawn | candidate | ✅ |
| `offer_amount` | Decimal(15,2) | Offered salary amount | recruiter | ✅ |
| `offer_currency` | CharField(10) | Offer currency | recruiter | ✅ |
| `offer_date` | DateField | When offer was made | system | ✅ |
| `offer_accepted_at` | DateTimeField | When candidate accepted | system | ✅ |
| `offer_rejected_at` | DateTimeField | When candidate rejected | system | ✅ |
| `joining_date` | DateField | Expected joining date | recruiter | ✅ |
| `joined_at` | DateTimeField | Actual join timestamp | system | ✅ |
| `application_form_data` | JSONField | Raw form fields from apply link | candidate | ✅ |
| `is_agency_submission` | BooleanField | Whether submitted by agency | system | ✅ |
| `agency_id` | UUIDField | Submitting agency | system | ✅ |
| `submitted_by` | UUIDField | Recruiter/system user who submitted | system | ✅ |

---

### 1.5 Table: `interviews_interview`
Model: `apps/interviews/models.py → Interview`
Candidate-relevant fields only:

| Field | Type | Purpose | API Exposed |
|---|---|---|---|
| `candidate_id` | UUIDField | Link to Candidate | ✅ |
| `application_id` | UUIDField | Link to Application | ✅ |
| `interview_type` | CharField | ai_screening/one_way_video/live_video/panel/technical/etc | ✅ |
| `interview_round` | IntegerField | Round number | ✅ |
| `scheduled_at` | DateTimeField | Scheduled datetime | ✅ |
| `status` | CharField | scheduled/in_progress/completed/cancelled/no_show/rescheduled | ✅ |
| `overall_score` | Decimal(5,2) | Final combined score | ✅ |
| `ai_score` | Decimal(5,2) | AI-generated score | ✅ |
| `human_score` | Decimal(5,2) | Interviewer score | ✅ |
| `recommendation` | CharField | strongly_recommend/recommend/neutral/not_recommend/reject | ✅ |
| `feedback_summary` | TextField | Interviewer summary feedback | ✅ |
| `recording_url` | TextField | Interview recording link | ✅ |
| `anti_cheat_score` | Decimal(5,2) | Anti-cheat integrity score | ✅ |
| `anti_cheat_flags` | JSONField | Flags raised during interview | ✅ |

**Note on `InterviewQuestion`:** Individual Q&A responses stored in `interviews_question` table including `candidate_answer`, `candidate_video_url`, `ai_score`, `ai_feedback`, `human_score`, `human_feedback`. These are interview-detail level and not aggregated into candidate-level APIs currently.

---

### 1.6 Table: `documents_document`
Model: `apps/documents/models.py → Document`
Generic document store; candidate documents use `entity_type='candidate'`

| Field | Type | Purpose | API Exposed |
|---|---|---|---|
| `entity_type` | CharField | 'candidate' for candidate docs | ✅ |
| `entity_id` | UUIDField | candidate.id | ✅ |
| `document_type` | CharField | cv/cover_letter/offer_letter/contract/id_proof/education_certificate/experience_letter/background_check/other | ✅ |
| `title` | CharField(255) | Document display name | ✅ |
| `file_url` | TextField | Storage URL | ✅ |
| `filename` | CharField(255) | Original filename | ✅ |
| `file_size` | IntegerField | File size in bytes | ✅ |
| `mime_type` | CharField | MIME type | ✅ |
| `version` | IntegerField | Document version number | ✅ |
| `is_current` | BooleanField | Whether this is the active version | ✅ |
| `is_verified` | BooleanField | Whether document has been verified | ✅ |
| `verified_by` | UUIDField | Who verified | ✅ |
| `verified_at` | DateTimeField | When verified | ✅ |
| `expires_at` | DateField | Document expiry (e.g. visa, cert) | ✅ |
| `notes` | TextField | Recruiter notes about document | ✅ |

---

### 1.7 Lookup / Master Tables

| Table | Model | Used By | Purpose |
|---|---|---|---|
| `candidates_skill` | `Skill` | `Candidate.skills` (JSON), not FK | Canonical skill master with aliases and category |
| `field_schema.py` | — | Models, serializers, frontend | Single source of truth for all choice sets: WORK_AUTHORIZATION_CHOICES, AVAILABILITY_STATUS_CHOICES, EDUCATION_CHOICES, WORK_MODE_CHOICES, SOURCE_CHOICES, INITIAL_ENTRY_TYPE_CHOICES, ACCOUNT_STATUS_CHOICES |

---

### 1.8 Computed / Derived Candidate Fields Returned by APIs

| Field | Source | Where Returned |
|---|---|---|
| `full_name` | `@property` on Candidate | CandidateSerializer |
| `engagement_summary` | `SerializerMethodField` — counts active job engagements by stage | CandidateSerializer |
| `profile` (nested) | `SerializerMethodField` — fetches CandidateProfile | CandidateDetailSerializer |
| `notes_count` | `SerializerMethodField` — count of notes | CandidateDetailSerializer |
| `candidate_name` | `SerializerMethodField` | CandidateEngagementSerializer |
| `owner_name` | `SerializerMethodField` — resolves user FK | CandidateEngagementSerializer, CandidateWorkspaceSerializer |
| `job_title` | `SerializerMethodField` | CandidateEngagementSerializer |
| `is_follow_up_overdue` | `SerializerMethodField` | CandidateEngagementSerializer |
| `actor_name` | `SerializerMethodField` | CandidateTimelineEventSerializer |
| Smart row fields | `_candidate_smart_row()` helper | CandidateDatabaseView only |

---

## Section 2: Candidate API Field Inventory

### 2.1 `GET /candidates/` — CandidateListView
**Serializer:** `CandidateSerializer`
**Returns:** All fields in CandidateSerializer.Meta.fields (71 fields) including `engagement_summary`.
**Missing DB fields not exposed:**
- `phone_country_code`, `phone_number`
- `nationality`, `work_authorization`
- `highest_education`, `graduation_year`
- `relocation_willing`, `preferred_locations`
- `global_hash` (intentional)

---

### 2.2 `GET /candidates/<pk>/` — CandidateDetailView
**Serializer:** `CandidateDetailSerializer` (extends CandidateSerializer + `profile` + `notes_count`)
**Returns:** All CandidateSerializer fields + nested `CandidateProfile` (all profile fields) + `notes_count`.
**Missing:** Same as CandidateListView for Candidate-level fields. Profile returned but `tenant_id` and `created_by` are absent from profile data.

---

### 2.3 `PUT /candidates/<pk>/` — CandidateDetailView.put
**Serializer:** `CandidateSerializer` (partial=True)
**Accepts for update:** All writable CandidateSerializer fields. Note: `nationality`, `work_authorization`, `highest_education`, `graduation_year`, `relocation_willing`, `preferred_locations` are writable in the model but **absent from the serializer**, so they **cannot be updated via this endpoint**.

---

### 2.4 `GET /candidates/database/` — CandidateDatabaseView
**Returns:** `_candidate_smart_row()` shape — a reduced custom dict per candidate (NOT the full serializer).
**Fields returned per row:**
- `id`, `name`, `current_title`, `company`, `experience`, `location`
- `source`, `source_type`, `engagement_stage`
- `owner` (raw UUID), `owner_name`, `last_touch`, `last_activity`
- `signals`: `readiness_score`, `fit_score`, `warning_signals`
- `job_engagement_summary`, `skills` (first 6 only), `passport_linked`
- `is_duplicate`, `notice_period_days`, `availability_status`, `open_engagements`

**Missing from smart row (in DB, not in response):**
- `email`, `phone`, `whatsapp`
- `linkedin_url`
- `current_location_country`
- `lifecycle_state`, `priority_level`, `profile_status`
- `candidate_state`, `candidate_pool`
- `is_actively_looking`, `work_mode_preference`
- `last_working_day`, `availability_date`
- `expected_salary_min/max`, `salary_currency`
- `tags`, `languages`
- `nationality`, `work_authorization`
- `account_status`, `passport_id`

---

### 2.5 `GET /candidates/active/` — ActiveCandidatesView
**Serializer:** `CandidateEngagementSerializer`
**Returns:** CandidateEngagement records (not Candidate directly). Candidate data exposed:
- `candidate` (UUID FK), `candidate_name` (computed)
- Engagement fields: `stage`, `priority`, `is_active`, `follow_up_at`, `is_follow_up_overdue`, `last_activity_at`
- `job`, `job_title`

**Missing Candidate fields not exposed:**
- All Candidate profile fields (salary, availability, location, etc.) — only `candidate_name` is resolved.

---

### 2.6 `GET /candidates/<pk>/command-center/` — CandidateCommandCenterView
**Returns:**
- `candidate`: Full `CandidateDetailSerializer` (Candidate + Profile + notes_count)
- `tabs.overview`: `CandidateSerializer` (duplicate of `candidate`)
- `tabs.activity_timeline`: `CandidateTimelineEventSerializer` (last 50)
- `tabs.notes`: `CandidateNoteSerializer` (last 50)
- `tabs.jobs_matches`: `[{job_id, stage}]` for each engagement with a job
- `tabs.engagement`: `CandidateEngagementSerializer` (all engagements)
- `tabs.documents`: `{resume_url, profile_cv_url}` only — **not** the Document table
- `tabs.communication`: `{last_contact_at, next_follow_up_at}`
- `tabs.automations`: workflow settings

**Missing from documents tab:**
- `CandidateProfile.github_url`, `portfolio_url`, `stackoverflow_url`
- `Document` table records (cv, cover_letter, id_proof, etc.) — not queried at all
- `TalentPassport.current_cv_url`

---

### 2.7 `GET /passport/my-passport/` — MyPassportView
**Serializer:** `TalentPassportSerializer`
**Returns:** 52 passport fields (see Section 1.3). Missing: `share_link_token`, `featured_media`, `other_social_urls`, `identity_verified_at`, `interview_scores`, `assessment_results`, `metadata`.

---

### 2.8 `GET /passport/my-candidate/` — MyCandidateView (passport app)
**Returns:** `LinkedCandidateData` shape from `passport/api.ts` — flattened candidate fields used by onboarding prefill. Includes identity, professional, availability, compensation, and visa fields. This is a read-only prefill endpoint.

---

### 2.9 `GET /candidates/<pk>/engagements/` — CandidateEngagementListView
**Serializer:** `CandidateEngagementSerializer`
**Returns:** All engagement fields. No Candidate data beyond `candidate_name`.

---

### 2.10 `GET /candidates/<pk>/workspace/` — CandidateWorkspaceView
**Serializer:** `CandidateWorkspaceSerializer`
**Returns:** Workspace-level fields (`priority`, `relationship_status`, `tags`, `local_rating`, `custom_fields`). No Candidate fields returned.

---

## Section 3: Candidate Field Grouping

### 3.1 Identity
| Field | Table | Notes |
|---|---|---|
| `id` | candidates_candidate | UUID |
| `global_hash` | candidates_candidate | Cross-tenant dedup hash — not API exposed |
| `passport_id` | candidates_candidate | Link to passport |
| `passport_number` | passport_talent_passport | Human-readable |
| `user_id` | passport_talent_passport | Auth user link |
| `duplicate_of` | candidates_candidate | |
| `is_duplicate` | candidates_candidate | |
| `duplicate_review_status` | candidates_candidate | |
| `claim_token` | candidates_candidate | Not API exposed |
| `claimed_at` | candidates_candidate | |
| `account_status` | candidates_candidate | |
| `profile_status` | candidates_candidate | |

### 3.2 Contact
| Field | Table | Notes |
|---|---|---|
| `first_name` | candidates_candidate | |
| `last_name` | candidates_candidate | |
| `email` | candidates_candidate | |
| `phone` | candidates_candidate | Legacy raw string |
| `phone_country_code` | candidates_candidate | **Not API exposed** |
| `phone_number` | candidates_candidate | Normalized — **Not API exposed** |
| `whatsapp` | candidates_candidate | |
| `linkedin_url` | candidates_candidate | |

### 3.3 Location
| Field | Table | Notes |
|---|---|---|
| `current_location_city` | candidates_candidate | |
| `current_location_country` | candidates_candidate | |
| `relocation_willing` | candidates_candidate | **Not API exposed** |
| `preferred_locations` | candidates_candidate | **Not API exposed** |
| `current_location_city` | passport_talent_passport | Passport copy |
| `current_location_country` | passport_talent_passport | Passport copy |
| `preferred_locations` | passport_talent_passport | Passport preference |

### 3.4 Professional
| Field | Table | Notes |
|---|---|---|
| `current_title` | candidates_candidate | |
| `current_company` | candidates_candidate | |
| `experience_years` | candidates_candidate | |
| `relevant_experience_years` | candidates_candidate | |
| `designation` | candidates_candidate | Internal label |
| `highest_education` | candidates_candidate | **Not API exposed** |
| `graduation_year` | candidates_candidate | **Not API exposed** |
| `summary` | candidates_profile | Only via detail/command-center |
| `work_experience` | candidates_profile | Only via detail/command-center |
| `education` | candidates_profile | Only via detail/command-center |
| `certifications` | candidates_profile | Only via detail/command-center |
| `projects` | candidates_profile | Only via detail/command-center |
| `headline` | passport_talent_passport | Passport only |
| `summary` | passport_talent_passport | Passport only |
| `work_history` | passport_talent_passport | Passport only |
| `education` | passport_talent_passport | Passport only |
| `volunteer_work` | passport_talent_passport | Passport only |
| `publications` | candidates_profile | |
| `awards` | candidates_profile | |
| `references` | candidates_profile | |

### 3.5 Work Authorization / Visa / PR / Nationality
| Field | Table | Notes |
|---|---|---|
| `nationality` | candidates_candidate | In DB, **not in CandidateSerializer** |
| `work_authorization` | candidates_candidate | In DB, **not in CandidateSerializer** |
| `highest_education` | candidates_candidate | Tangentially relevant |

### 3.6 Compensation
| Field | Table | Notes |
|---|---|---|
| `current_ctc` | candidates_candidate | |
| `current_ctc_currency` | candidates_candidate | |
| `expected_salary_min` | candidates_candidate | |
| `expected_salary_max` | candidates_candidate | |
| `salary_currency` | candidates_candidate | |
| `offer_in_hand` | candidates_candidate | |
| `offer_in_hand_amount` | candidates_candidate | |
| `counter_offer` | candidates_candidate | |
| `expected_salary_min` | passport_talent_passport | Passport copy |
| `expected_salary_max` | passport_talent_passport | Passport copy |
| `offer_amount` | pipeline_application | Job-specific offer |

### 3.7 Availability
| Field | Table | Notes |
|---|---|---|
| `availability_status` | candidates_candidate | Choices from field_schema |
| `last_working_day` | candidates_candidate | |
| `notice_period_days` | candidates_candidate | |
| `availability_date` | candidates_candidate | |
| `is_actively_looking` | candidates_candidate | |
| `work_mode_preference` | candidates_candidate | |
| `notice_period_days` | passport_talent_passport | Passport copy |
| `availability_date` | passport_talent_passport | Passport copy |
| `is_actively_looking` | passport_talent_passport | Passport copy |
| `open_to_work` | passport_talent_passport | Passport-specific flag |
| `preferred_work_mode` | passport_talent_passport | Passport copy (field name differs) |

### 3.8 Source / Source Detail
| Field | Table | Notes |
|---|---|---|
| `source` | candidates_candidate | Self/agency/company/linkedin/etc |
| `source_detail` | candidates_candidate | Free text |
| `source_type` | candidates_candidate | Broader category |
| `source_subtype` | candidates_candidate | Sub-category |
| `initial_entry_type` | candidates_candidate | Immutable creation method |
| `source` | pipeline_application | Application-level source |

### 3.9 Tags
| Field | Table | Notes |
|---|---|---|
| `tags` | candidates_candidate | Flat JSON list |
| `tags` | candidate_workspaces | Workspace-level (tenant-private) |

### 3.10 Skills / Languages
| Field | Table | Notes |
|---|---|---|
| `skills` | candidates_candidate | Flat JSON list |
| `languages` | candidates_candidate | Flat JSON list |
| `skills` | passport_talent_passport | Passport skills (richer, structured) |
| `languages` | passport_talent_passport | Passport languages |
| `Skill` master | candidates_skill | Canonical list with categories and aliases |

### 3.11 Documents
| Field | Table | Notes |
|---|---|---|
| `resume_url` | candidates_candidate | Direct URL shortcut |
| `cv_url` | candidates_profile | Profile-level CV |
| `cv_parsed_data` | candidates_profile | Parsed CV JSON |
| `cv_uploaded_at` | candidates_profile | |
| `portfolio_url` | candidates_profile | **Only via detail, not list** |
| `github_url` | candidates_profile | **Only via detail, not list** |
| `stackoverflow_url` | candidates_profile | **Only via detail, not list** |
| `current_cv_url` | passport_talent_passport | Passport CV |
| `current_cv_filename` | passport_talent_passport | |
| `current_cv_uploaded_at` | passport_talent_passport | |
| Documents table | documents_document | Not fetched by CandidateCommandCenterView |
| `ResumeVersion` | passport_resume_version | Versioned history, not exposed |

### 3.12 Passport
| Field | Table | Notes |
|---|---|---|
| `passport_id` | candidates_candidate | Link |
| `passport_linked` | candidates_candidate | Boolean flag |
| `passport_visibility_mode` | candidates_candidate | internal_only/shared_with_client/private |
| Full TalentPassport | passport_talent_passport | Via separate passport endpoints |
| `identity_verified` | passport_talent_passport | |
| `background_verified` | passport_talent_passport | |
| `employment_verified` | passport_talent_passport | |
| `education_verified` | passport_talent_passport | |
| `heat_score` | passport_talent_passport | |
| `completeness_score` | passport_talent_passport | |
| `share_link_token` | passport_talent_passport | **Never exposed** |
| Access logs | passport_access_log | Via /passport/my-passport/access-log/ |
| Revocations | passport_revocation | Not API exposed |

### 3.13 Applications
| Field / Table | Notes |
|---|---|
| `pipeline_application` | Not embedded in candidate serializer at all — separate endpoint |
| `active_job_id` | On Candidate model — cached reference only |
| `engagement_summary` | Computed counts on CandidateSerializer |

### 3.14 Interviews
| Field / Table | Notes |
|---|---|
| `interviews_interview` | Not embedded in candidate serializer — separate endpoints |
| Interview scores summary | `passport_talent_passport.interview_scores` (JSON list) — **not in serializer** |
| `overall_score`, `recommendation` | Per interview, not surfaced on candidate-level API |

### 3.15 System / Meta
| Field | Table | Notes |
|---|---|---|
| `tenant_id` | candidates_candidate | |
| `owner_user_id` | candidates_candidate | Raw UUID — name not resolved in list API |
| `owner_tenant_id` | candidates_candidate | |
| `assigned_to` | candidates_candidate | |
| `created_at`, `updated_at` | candidates_candidate | |
| `created_by` | candidates_candidate | |
| `is_deleted`, `deleted_at` | candidates_candidate | Never exposed |
| `metadata` | candidates_candidate | |
| `lifecycle_state` | candidates_candidate | |
| `engagement_stage` | candidates_candidate | Synced from engagement layer |
| `priority_level` | candidates_candidate | |
| `workflow_mode` | candidates_candidate | |
| `is_in_active_work` | candidates_candidate | |
| `last_activity_at` | candidates_candidate | |
| `last_contact_at` | candidates_candidate | |
| `next_follow_up_at` | candidates_candidate | |
| `candidate_state` | candidates_candidate | NEW_LEAD/JOB_ASSOCIATED/REVIVED |
| `candidate_pool` | candidates_candidate | GENERAL/NONE |
| `is_general_pool_used` | candidates_candidate | |
| `profile_completeness` | candidates_candidate | |
| `readiness_score` | candidates_candidate | |
| `fit_score` | candidates_candidate | |
| `fitment_score` | candidates_candidate | |
| `automation_enabled` | candidates_candidate | |
| `auto_nurture_enabled` | candidates_candidate | |
| `auto_followup_enabled` | candidates_candidate | |
| `auto_stage_suggestions_enabled` | candidates_candidate | |

---

## Summary: Critical Mismatches Found

### A — Fields in DB but absent from CandidateSerializer (writable orphans)
These fields exist in the `Candidate` model but are not in `CandidateSerializer.Meta.fields`. They cannot be read or written via any candidate API endpoint:

| Field | DB Type | Impact |
|---|---|---|
| `phone_country_code` | CharField | Phone formatting broken — country code silently lost |
| `phone_number` | CharField | Normalized phone never returned |
| `nationality` | CharField | Visa/nationality filtering impossible via API |
| `work_authorization` | CharField | Compliance field invisible to API consumers |
| `highest_education` | CharField | Education filter on search impossible |
| `graduation_year` | IntegerField | Same |
| `relocation_willing` | CharField | Job matching signal invisible |
| `preferred_locations` | JSONField | Preferred location data invisible |

### B — CandidateProfile never returned from list endpoints
`CandidateProfile` (summary, work_experience, education, certifications, projects, portfolio_url, github_url, stackoverflow_url) is **only accessible** via:
- `GET /candidates/<pk>/` (detail)
- `GET /candidates/<pk>/command-center/`

It is **never returned** by:
- `GET /candidates/` (list)
- `GET /candidates/database/`
- `GET /candidates/active/`

This means recruiters viewing candidate lists see zero rich profile data.

### C — Documents tab in Command Center is a stub
`CandidateCommandCenterView` returns:
```json
"documents": {
  "resume_url": "...",
  "profile_cv_url": "..."
}
```
But it does NOT query the `documents_document` table, nor does it expose `github_url`, `portfolio_url`, or `stackoverflow_url` from `CandidateProfile`.

### D — owner_user_id returned as raw UUID in list/database views
`_candidate_smart_row()` resolves the name via a batch lookup map. `CandidateSerializer` returns `owner_user_id` as a raw UUID only. No name is available in the serializer response.

### E — TalentPassport has 7 fields not in TalentPassportSerializer
`featured_media`, `other_social_urls`, `identity_verified_at`, `interview_scores`, `assessment_results`, `metadata`, `share_link_token`. The first four are candidate-facing omissions; `share_link_token` is correctly withheld.

### F — Duplicate field names across tables (no canonical winner)
These same concepts exist in multiple tables with different field names, no sync logic, and no clear canonical winner visible to API consumers:

| Concept | candidates_candidate | candidates_profile | passport_talent_passport |
|---|---|---|---|
| Resume / CV | `resume_url` | `cv_url` | `current_cv_url` |
| Summary / Bio | _(absent)_ | `summary` | `summary` |
| Work history | _(absent)_ | `work_experience` | `work_history` |
| Education | `highest_education` (scalar) | `education` (JSON) | `education` (JSON) |
| Skills | `skills` (flat list) | _(absent)_ | `skills` (list) |
| Languages | `languages` | _(absent)_ | `languages` |
| Location | `current_location_city/country` | _(absent)_ | `current_location_city/country` |
| Availability | `availability_status` | _(absent)_ | _(absent — open_to_work / is_actively_looking only)_ |
| Work mode | `work_mode_preference` | _(absent)_ | `preferred_work_mode` _(different field name)_ |
| Salary | `expected_salary_min/max` | _(absent)_ | `expected_salary_min/max` |
| Notice period | `notice_period_days` | _(absent)_ | `notice_period_days` |

### G — Visa / work authorization invisible in Candidate API
`nationality` and `work_authorization` are stored in `candidates_candidate` but absent from `CandidateSerializer` — so no API consumer (frontend, search, filter) can read them through the standard candidate endpoints. They must be added to the serializer.
