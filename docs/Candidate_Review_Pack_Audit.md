# Candidate Review Pack — Audit & Strategy

This document consolidates the audit of Candidate Database fields, Frontend Forms, and UI Visibility. It serves as the foundation for the upcoming Candidate Field Refactor.

---

## 1. Master Candidate Field Dictionary (Ref: `src/constants/candidateFields.ts`)

| Category | Field Name | Type | Required | Backend | Form Coverage (Q=Quick, D=Detailed, A=Apply, O=Onboarding, P=Passport, R=Register) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Identity** | `first_name` | text | Yes | C+P+U | Q, D, A, O, P, R |
| | `last_name` | text | Yes | C+P+U | Q, D, A, O, P, R |
| | `email` | email | No | C+U | Q, D, A, R |
| | `phone` | phone | No | C+U | Q, D, A, O, R |
| | `whatsapp` | text | No | C | D, P (Indirectly) |
| **Professional** | `current_title` | text | No | C+P | Q, D, A, O, P |
| | `current_company` | text | No | C+P | D, A, O, P |
| | `linkedin_url` | url | No | C+P | D, A, O, P |
| | `github_url` | url | No | CP+P | D, P |
| | `portfolio_url` | url | No | CP+P | D, P |
| | `headline` | text | No | P | P |
| | `summary` | textarea | No | CP+P | D, P |
| **Location** | `current_location_city` | text | No | C+P | D, A, O, P |
| | `current_location_country` | select | No | C+P | D, O, P |
| **Experience** | `experience_years` | number | No | C+P | D, A, O, P |
| | `relevant_experience_years` | number | No | C | A |
| **Education** | `highest_education` | select | No | C | A, D (Custom) |
| | `graduation_year` | number | No | C | A, D (Custom) |
| **Skills/Tags** | `skills` | tags | No | C+P | D, A, O, P |
| | `languages` | tags | No | C+P | D, O, P |
| | `tags` | tags | No | C | D |
| **Availability** | `availability_status` | select | No | C | A, O, P |
| | `notice_period_days` | number | No | C+P | D, A, O, P |
| | `last_working_day` | date | No | C | D |
| | `availability_date` | date | No | C+P | D, P |
| | `is_actively_looking` | boolean | No | C+P | D, O, P |
| | `work_mode_preference` | select | No | C | A, O, P |
| **Compensation** | `current_ctc` | number | No | C | D, P |
| | `expected_salary_min` | number | No | C+P | D, O, P |
| | `expected_salary_max` | number | No | C+P | D, O, P |
| | `salary_currency` | select | No | C+P | D, O, P |
| **Offer** | `offer_in_hand` | boolean | No | C | D, P |
| | `offer_in_hand_amount` | number | No | C | D, P |
| | `offer_currency` | select | No | C.M | D |
| **Legal** | `nationality` | select | No | C | D, A |
| | `work_authorization` | select | No | C | D, A |
| | `visa_status` | text | No | C.M | D |
| | `pr_status` | text | No | C.M | D |
| **Documents** | `resume_url` | url | No | C | Q, D, A, O, P |

*Backend: C=Candidate, CP=CandidateProfile, P=TalentPassport, U=CustomUser, M=Metadata*

---

## 2. Candidate Entry Source Map

### Flow A: Company/Agency Added Candidate (Internal)
1. **Trigger**: Recruiter clicks "Add Candidate".
2. **Form**: `AddCandidateWorkflowModal` (Quick or Detailed).
3. **Data Path**: Submits to `POST /candidates/`.
4. **Records**: Creates `Candidate` record. If email provided and account exists, links to `User`.
5. **After Submit**: Recruiter can share "Claim Profile" link.

### Flow B: Company/Agency Shared Link (Self-Service)
1. **Trigger**: Candidate visits `/apply/:token`.
2. **Form**: `ApplyForm` (Public).
3. **Data Path**: Submits to `POST /apply/:token/submit/`.
4. **Records**: Creates `Candidate` record + `Application`. If `wants_account=true`, creates `User` + `TalentPassport`.
5. **After Submit**: Candidate lands on `Onboarding` if account created.

### Flow C: Direct Candidate Signup (Independent)
1. **Trigger**: Candidate visits `/register/candidate`.
2. **Form**: `RegisterCandidate`.
3. **Data Path**: Submits to `POST /auth/register/candidate/`.
4. **Records**: Creates `User` + `TalentPassport`.
5. **After Submit**: Candidate lands on `Onboarding`.

---

## 3. Candidate Form Audit

### A. Quick Add Form (`AddCandidateWorkflowModal`)
- **Who uses**: Recruiters/Agencies.
- **Fields**: first_name, last_name, email, phone, current_title, source, resume_url.
- **Validation**: Required (First, Last), Either (Email, Phone).
- **Writes to**: `Candidate` model via `POST /candidates/`.
- **Prefill**: None.
- **Outcome**: `Candidate` record created; user can then send invite link.

### B. Detailed Add Form (`AddCandidateWorkflowModal`)
- **Who uses**: Recruiters/Agencies.
- **Fields**: Full set (Basic, Professional, Compensation, Documents, Notes).
- **Validation**: Strict (Last working day required if notice period applicable, etc).
- **Writes to**: `Candidate` model + `Metadata`.
- **Prefill**: If `mode=edit`, prefills from `Candidate` API.

### C. Public Apply Form (`ApplyForm`)
- **Who uses**: Candidates.
- **Fields**: first_name, last_name, email, phone, linkedin_url, current_title, current_company, exp_years, relevant_exp_years, highest_education, graduation_year, skills, location, nationality, work_auth, availability_status, notice_period, work_mode, resume_url, password.
- **Validation**: Required (First, Last, Email, Phone, Resume).
- **Writes to**: `Candidate` + `Application`. Optionally `User` + `Passport`.
- **Prefill**: None (public).

### D. Candidate Onboarding Form (`Onboarding`)
- **Who uses**: Candidates (post-signup/claim).
- **Steps**: Basic Info → Skills/Prefs → Resume.
- **Prefill**: High (User → LinkedCandidate → Passport). Uses "From passport" etc tags.
- **Writes to**: `User`, `Passport`, `Candidate` (linked).
- **Sync Logic**: Unions skills/languages; append-safe merge for text.

### E. Passport/Profile Form (`Passport`)
- **Who uses**: Candidates.
- **Structure**: Tabs (Profile, Experience, Education, Skills, Preferences).
- **Writes to**: `TalentPassport` model via `PUT /passport/my-passport/`.
- **Sync Logic**: Complex; includes sub-models for Work History and Education.

---

## 4. Frontend Visibility Audit

| Page/Component | Route/Location | Visibility | Primary Data Source | Notable Fields Shown | Missing/Broken/Inconsistent |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Candidate Database** | `/candidates/database` | Recruiter | `GET /candidates/database` | Smart Row (Name, Title, Location, AI Scores, Stage) | `relevant_experience` not in columns; `graduation_year` uses profile data fallback. |
| **Candidate Quick View** | Drawer | Recruiter | `GET /candidates/:id` | Full identity, Comp (min/max), Notice, Work Auth, Skills, Resume, Last Note. | Inconsistent salary unit display (Config dependent); Resume uses demo fallback if empty. |
| **Candidate Full View** | `/candidates/:id` | Recruiter | `GET /candidates/:id` | Hero (Identity), Quick Stats, Contact, Summary, Skills, Notes, Activity. | `expected_salary` range missing in stats; `work_history` missing in Profile tab. |
| **Candidate Passport** | `/passport` | Candidate | `GET /passport/my-passport` | Profile, History, Edu, Skills, Preferences. | Video intro URL shown but rarely filled; Share link generation visible. |
| **Candidate Dashboard** | `/dashboard` | Candidate | `GET /auth/me` | User basic info. | No candidate-specific profile completion widget (moved to Onboarding). |
| **Agency Submission** | `/agency/submit` | Agency | `GET /candidates` | List (Name, Title). | Only shows basic candidate info; no detailed profile check before submission. |

---

## 5. Audit Findings & Refactor Priority

### A. Duplicate/Overlap/Conflict Findings
- **Notice Period**: Tracked as `notice_period_days` (number) in DB but often shown as select (0, 15, 30, etc) in UI. Discrepancy in "Serving notice" vs "Notice period days".
- **Work Mode**: `work_mode_preference` (Candidate) vs `preferred_work_mode` (Passport). Standardized in `candidateFields.ts` but code uses both.
- **Salary**: Multiplier logic (e.g. 100k for IN) is handled in `AddCandidateWorkflowModal` but not consistently in other forms like `ApplyForm`.

### B. Missing/Inconsistent Fields
- **Highest Education**: Present in `ApplyForm` and `Passport` (Education sub-model) but missing in `Detailed Add` (standard fields).
- **Relevant Experience**: Only collected in `ApplyForm`; not present in Recruiter add/edit flows.
- **Work History**: Detailed in `Passport` but shown as a flattened `current_title/company` in Recruiter views.

### C. Inconsistent Naming/Validation
- `availability_status` vs `availability_date` vs `last_working_day`. The relationship between these is fuzzy in some forms.
- `phone` is sometimes a string, sometimes a `PhoneValue` object with `country_code`.

---

## 6. Questions for Founder Review

1. **Salary Normalization**: Should all internal forms (Detailed Add) enforce the 100k/1k multiplier, or should we store absolute numbers and format on display?
2. **Education Storage**: Should we move `highest_education` and `graduation_year` from top-level `Candidate` columns to the `CandidateProfile.education` array exclusively?
3. **Relevant Experience**: Should we add `relevant_experience_years` to the `Detailed Add` and `Quick View` edit forms? It's currently only in `ApplyForm`.
4. **Work Authorization**: The options in `Detailed Add` (Edit Mode) vs `AddCandidateWorkflowModal` (Add Mode) have slight naming mismatches (e.g. `sponsorship_required` vs `need_sponsorship`). Which is the source of truth?

---

## 7. Recommended Implementation Order

1. **Step 1: Standardize `candidateFields.ts`**: Update the coverage matrix and option sets to match the final decisions.
2. **Step 2: Refactor `AddCandidateWorkflowModal`**: Align "Quick" and "Detailed" with the master dictionary.
3. **Step 3: Refactor `ApplyForm` & `Onboarding`**: Ensure they use the same canonical fields and validation.
4. **Step 4: Update `CandidateQuickView` Edit Flow**: Ensure it supports all fields including the ones currently missing (education, relevant exp).
5. **Step 5: Unified Sync Logic**: Ensure `Candidate` ↔ `Passport` sync handles all fields correctly in the backend (verification required).
