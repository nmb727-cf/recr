# Candidate Portal — Cross-System Verification Report
**Audit Date:** 2026-04-02
**Scope:** Candidate Portal ↔ Company ATS ↔ Agency Side ↔ Jobs ↔ Applications ↔ Pipeline ↔ Interviews ↔ Passport
**Method:** Static code audit — models, views, serializers, URL configs, frontend API layer, page components

---

## 1. Executive Summary

**Overall Health: PARTIAL — CRITICAL BREAKS DETECTED**

The system has a strong foundational architecture with clear model relationships and role-based API separation. However, several critical broken flows exist where candidate-side and company-side systems are not properly synchronized:

| Issue | Severity |
|-------|----------|
| No documented candidate-facing apply endpoint | Critical |
| No `GET /candidate/applications/` backend route found | Critical |
| Passport-Candidate link is asymmetric (UUID, not FK) | Critical |
| Interview model FKs are UUIDs, not Django ForeignKeys | Critical |
| Application status enum mismatch (company uses statuses not in model) | Critical |
| Candidate serializer exposes recruiter-internal fields | High |
| No post-import candidate creation from passport | High |
| Candidate cannot self-access own profile via company endpoint | High |

---

## 2. Cross-System Flows Verified

### Flow 1: Candidate Direct Signup
**Status: PARTIAL**

| Sub-step | Status | Evidence |
|----------|--------|----------|
| Account creation endpoint | Built | `accounts/views.py` — `RegisterCandidateView` creates `CustomUser(role='candidate')`, OTP via `EmailOTP` model |
| OTP verification | Built | `accounts/models.py` — `EmailOTP` model, tokens returned via JWT `get_tokens_for_user` |
| Onboarding wizard (frontend) | Built | `pages/candidate/Onboarding.tsx` inferred from page structure |
| Passport setup | Built (isolated) | `passport/views.py` — `MyPassportView` at `/api/v1/passport/my-passport/` auto-creates `TalentPassport` on first PUT |
| Candidate apply to jobs | **Broken** | Frontend `candidate.ts:14` calls `/jobs/{jobId}/apply/` but route not found in `jobs/urls.py` or `pipeline/urls.py` |
| Application visible on company side | **Broken** | `GET /candidate/applications/` not found in `candidates/urls.py` or `pipeline/urls.py` |

### Flow 2: Company Adds Candidate
**Status: Built with Dedup Logic**

| Sub-step | Status | Evidence |
|----------|--------|----------|
| Quick add / detailed add | Built | `candidates/views.py` — `CandidateListView.post()` line 346+ |
| Deduplication | Built | Checks email, phone, passport_id, global_hash (lines 355–366); returns 409 CONFLICT with protection info |
| Create or reuse record | Built | Existing email → return existing (line 386–395); new → create with `tenant_id=request.user.tenant_id` |
| Candidate claim flow | Partial | `candidates/models.py` — `claim_token`, `claim_token_expires_at`, `claimed_at` fields (lines 177–179); claim logic not fully visible |

### Flow 3: Agency Adds / Submits Candidate
**Status: Built with Visibility Control**

| Sub-step | Status | Evidence |
|----------|--------|----------|
| Agency creates candidate | Built | Same `CandidateListView.post()`; sets `tenant_id=agency.tenant_id`, `source='agency'` |
| Agency submission to company | Built | `pipeline/models.py` line 32–33 — `is_agency_submission=True`, `agency_id=agency_id` |
| Company-side visibility | Built | `pipeline/views.py:287–290` filters by `tenant_id=request.user.tenant_id`; all submissions visible |
| Candidate claim after agency add | Partial | `account_status` field (candidates/models.py line 180): `none → invited → claimed → active` workflow present, full logic not audited |

### Flow 4: Public Passport / Share Link
**Status: Built with Privacy Controls**

| Sub-step | Status | Evidence |
|----------|--------|----------|
| Share link generation | Built | `TalentPassport.share_link_token` auto-generated on save (passport/models.py line 102–103) |
| Public endpoint | Built | `/api/v1/passport/public/<token>/` (passport/urls.py line 16); uses `TalentPassportPublicSerializer` |
| Access logging | Built | `PassportAccessLog` model (passport/models.py line 140–166) |
| Visibility settings | Built | `visibility_settings` JSONField (passport/models.py line 89); `_apply_visibility()` filters fields at line 285–296 |
| Candidate edit vs public view separation | Built | Authenticated edit: `/my-passport/` PUT; public view: `/public/<token>/` GET; different serializers |
| Passport import by company/agency | Partial | `PassportImportView` at `/api/v1/passport/import/` logs import; **no post-import candidate creation logic visible** |

### Flow 5: Candidate Apply Flow
**Status: Broken**

| Sub-step | Status | Evidence |
|----------|--------|----------|
| Candidate apply endpoint | **Broken** | Frontend calls `/jobs/{jobId}/apply/` (`candidate.ts:14`); not in `jobs/urls.py`; `config/urls.py` includes `candidates.apply_urls` but file not confirmed |
| My Applications list | **Broken** | Frontend calls `GET /candidate/applications/` (`candidate.ts:5`); no matching backend route in `candidates/urls.py` or `pipeline/urls.py` |
| Application on company ATS | Partial | Application model uses unique constraint `(tenant_id, candidate_id, requisition_id)` preventing duplicates; company reads from same `Application` table |
| Status consistency | **Issue** | See Section 8 — status enum mismatch |

### Flow 6: Interview Flow
**Status: Partial**

| Sub-step | Status | Evidence |
|----------|--------|----------|
| Company/agency schedules interview | Built | `interviews/views.py` — `InterviewListView.post()` creates Interview; company endpoint `/api/v1/interviews/` |
| Candidate-side interview endpoint | Partial | `interviews/candidate_urls.py` — `CandidateInterviewListView`, instructions, runtime, status, start, submit-answer, complete; registered at `config/urls.py:35` |
| Status sync | Partial | Single `Interview.status` field read by both sides; no explicit sync logic needed (single source); but view implementation not fully audited |
| Recruiter vs candidate field separation | Not Verified | Expected: recruiter sees feedback/scores; candidate sees instructions/link; separate serializers implied but not confirmed |

---

## 3. Candidate ↔ Company Verification

### Model Level

**Candidate Model** (`candidates/models.py`)
- Company-visible fields: `tenant_id`, `owner_user_id`, `assigned_to`, `created_by`, `workflow_mode`, `engagement_stage`, `readiness_score`, `fit_score`, `source`, `source_type`, `duplicate_of`, `is_duplicate`
- Candidate-facing fields: `email`, `phone`, `first_name`, `last_name`, `experience_years`, `current_title`, `current_company`, `location`, `passport_linked`
- `tenant_id` is nullable (line 96): NULL = self-registered; non-NULL = company/agency-owned

**Application Model** (`pipeline/models.py`)
- Single record read by both sides
- Unique constraint: `(tenant_id, candidate_id, requisition_id)` prevents duplicates
- No row-level permission enforcement visible at model layer

### API Level

| Layer | Status | Issue |
|-------|--------|-------|
| `CandidateSerializer` (`candidates/serializers.py:36–75`) | Issue | No candidate-facing variant — all fields including internal ones returned regardless of context |
| Application serializer | Not Verified | No separate `CandidateApplicationSerializer` confirmed |
| Tenant isolation (company side) | Built | `candidates/views.py` line 287–300: `Q(tenant_id=request.user.tenant_id)` |
| Tenant isolation (candidate self-access) | **Missing** | No code filters by `user_id` for candidate self-access in `CandidateListView.get()` |

### UI Level

- Company ATS: `pages/candidates/`, `pages/pipeline/` — full candidate profiles, all applications, pipeline stages
- Candidate Portal: `pages/candidate/` — own profile, own applications, own interviews
- **Gap**: Candidate cannot access own profile via company-facing endpoint; separate candidate profile endpoint needed

---

## 4. Candidate ↔ Agency Verification

### Model Level

**AgencyClientRelationship** (`agencies/models.py:6–178`)
- Links `agency_tenant_id` ↔ `company_tenant_id`
- Retention controls: `retention_scope` choices — `job_only, view_only, limited_company_access` (line 57–65)
- Post-expiry behavior: `retention_post_expiry` choices — `shared, company_use, consent_required` (line 66–74)

**AgencyJobAssignment** (`agencies/models.py:181–217`)
- Links agency to requisition; tracks max submissions, submission count

**Application Model** (`pipeline/models.py:32–33`)
- `agency_id` (nullable UUID)
- `is_agency_submission` (boolean, default False)

**CandidateTenantRight** (`candidates/models.py:572–599`)
- Tracks protection: `source_tenant_id` (agency) → `target_tenant_id` (company)
- `relationship_type`: protected or shared
- `protected_until`: expiration date
- Used at `candidates/views.py:360–383` to block candidate imports

### Gaps

| Issue | Severity |
|-------|----------|
| No direct Candidate ↔ Agency FK model — link only via Application.agency_id | Medium |
| `retention_scope` enforcement not visible in view code | Medium |
| Candidate does not know which agency submitted them | Low |

---

## 5. Candidate ↔ Passport Verification

### Model Relationship

```
CustomUser (id: UUID)
    ↓ user_id (FK in TalentPassport)
TalentPassport (id: UUID, user_id FK, candidate_id UUID-only)
    ↑ passport_id (UUID-only in Candidate)
Candidate (id: UUID, passport_id UUID-only)
```

**Critical Finding**: Both links are weak UUID references, not Django ForeignKeys. No ORM cascade, no `related_name`, no `select_related` possible.

Evidence:
- `passport/models.py:10` — `candidate_id = models.UUIDField(null=True, blank=True, db_index=True)`
- `candidates/models.py:265` — `passport_id = models.UUIDField(null=True, blank=True)`
- `passport/views.py:42–43` — Passport created with `TalentPassport(user_id=request.user.id)` — no `candidate_id` set!

### Field Duplication

Both models have: `current_title`, `current_company`, `current_location_city/country`, `experience_years`. No canonical source designated. No sync code visible.

### Visibility / Privacy

| Feature | Status | Evidence |
|---------|--------|----------|
| `visibility_settings` JSONField | Built | `passport/models.py:89` |
| `_apply_visibility()` filtering | Built | `passport/views.py:285–296` |
| Public vs authenticated serializer split | Built | `TalentPassportPublicSerializer` vs authenticated serializer |
| Post-import candidate link | **Missing** | `PassportImportView` logs but does not create/link candidate |

---

## 6. Candidate ↔ Jobs / Applications / Pipeline Verification

### Data Model Chain

```
Candidate (candidate_id)
    ↓ Application.candidate_id
Application
    ├─ requisition_id → JobRequisition
    ├─ current_stage_id → JobStage
    ├─ status (enum)
    └─ tenant_id (company tenant)
```

- Unique constraint prevents duplicate applications: `(tenant_id, candidate_id, requisition_id)` (`pipeline/models.py:64`)

### Candidate-Side Application Access

| Item | Status | Evidence |
|------|--------|----------|
| Frontend `listApplications()` | Built | `candidate.ts:5` — `GET /candidate/applications/` |
| Frontend `applyJob(jobId)` | Built (no backend) | `candidate.ts:14` — `POST /jobs/{jobId}/apply/` |
| Backend `GET /candidate/applications/` | **Not Found** | Not in `candidates/urls.py`, `pipeline/urls.py`. Config includes `candidates.apply_urls` (line 23) — unconfirmed |
| Backend `POST /jobs/{jobId}/apply/` | **Not Found** | Not in `jobs/urls.py` (not fully audited) |

### Status Consistency

- **Canonical source**: `Application.status` field (`pipeline/models.py:12–26`)
- Model choices: `applied, screening, shortlisted, interview, assessment, offer, joined, rejected, withdrawn, on_hold`
- Company view `COMPANY_VISIBLE_APP_STATUSES` (`pipeline/views.py:44–56`): `submitted, under_review, review, client_review, applied, screening, shortlisted, interview, offer, placement, joined`
- **Mismatch**: `submitted`, `under_review`, `review`, `client_review`, `placement` are NOT in model choices → potential validation errors

---

## 7. Candidate ↔ Interviews Verification

### Interview Model FKs (`interviews/models.py:361–407`)

```python
application_id = models.UUIDField(db_index=True)   # ← NOT a FK
candidate_id   = models.UUIDField(db_index=True)   # ← NOT a FK
requisition_id = models.UUIDField(db_index=True)   # ← NOT a FK
```

No cascade delete, no `select_related`, no `prefetch_related` possible without explicit joins.

### Candidate-Side Interview Endpoints (`interviews/candidate_urls.py`)

```
GET  /api/v1/candidate/interviews/
GET  /api/v1/candidate/interviews/<pk>/instructions/
GET  /api/v1/candidate/interviews/<pk>/runtime/
GET  /api/v1/candidate/interviews/<pk>/status/
POST /api/v1/candidate/interviews/<pk>/start/
POST /api/v1/candidate/interviews/<pk>/submit-answer/
POST /api/v1/candidate/interviews/<pk>/complete/
```

Registered in `config/urls.py:35`. View implementation (`CandidateInterviewListView`) not fully audited.

### Consistency Analysis

| Item | Status | Detail |
|------|--------|--------|
| Single record source | Built | Both recruiter and candidate read same `Interview` row |
| Company-side status write | Built | `/api/v1/interviews/` POST/PATCH |
| Candidate-side status read | Partial | Endpoint exists; view implementation not confirmed |
| Recruiter fields (feedback, scores) hidden from candidate | Not Verified | Separate serializer expected; not confirmed |
| No candidate write to Interview.status | Expected/Not Verified | Only submit-answer and complete actions available |

---

## 8. Data Mismatches

### #1 — Application Status Enum Mismatch (Critical)
- **File**: `pipeline/models.py:12–26` vs `pipeline/views.py:44–56`
- **Model choices**: `applied, screening, shortlisted, interview, assessment, offer, joined, rejected, withdrawn, on_hold`
- **Company view uses additionally**: `submitted, under_review, review, client_review, placement`
- **Risk**: Setting Application.status to `placement` or `submitted` will fail model validation or silently store invalid values

### #2 — Passport-Candidate Duplicate Fields (High)
- **Files**: `passport/models.py` vs `candidates/models.py`
- **Duplicated**: `current_title`, `current_company`, `location`, `experience_years`
- **No canonical source** designated; no sync code visible
- **Risk**: Recruiter updates candidate profile; candidate passport shows stale data (and vice versa)

### #3 — CandidateSerializer Exposes Recruiter-Internal Fields (High)
- **File**: `candidates/serializers.py:36–75`
- **Exposed**: `tenant_id`, `owner_user_id`, `assigned_to`, `created_by`, `workflow_mode`, `engagement_stage`, `readiness_score`, `fit_score`, `source_type`, `duplicate_of`, `is_duplicate`
- **Risk**: Candidate making API calls to their own profile would see internal classification data

### #4 — Interview Execution Mode Enum Mismatch (Medium)
- **File**: `interviews/models.py:381–385` defines `(native, third_party, external)`
- **Registry** `interviews/models.py:100–174` includes `manual` and `async` execution modes
- **Risk**: Interview type defaults might set `execution_mode` to values not in model choices

### #5 — Application Stage History Without Restriction (Medium)
- **File**: `pipeline/models.py:67–87` — `ApplicationStageHistory` tracks `from_stage, to_stage, from_status, to_status, moved_by, reason`
- No serializer audited for candidate-facing visibility
- **Risk**: If exposed, candidate would see every internal stage move with timestamps

---

## 9. UI Mismatches

### Recruiter-Only Fields Visible in Candidate Serializer

| Field | Risk | Recommended Action |
|-------|------|--------------------|
| `workflow_mode` | Candidate sees internal classification | Hide in candidate serializer |
| `engagement_stage` | Candidate sees funnel stage name (new_lead, contacted, etc.) | Hide in candidate serializer |
| `readiness_score`, `fit_score` | Candidate sees scoring data meant for recruiters | Hide in candidate serializer |
| `assigned_to`, `owner_user_id` | Candidate sees who internally owns their record | Hide in candidate serializer |
| `duplicate_of`, `is_duplicate` | Exposes dedup system | Hide in candidate serializer |
| `tenant_id` | Multi-tenancy implementation detail | Hide in candidate serializer |

### Missing Frontend Pages (Candidate Portal)

| Missing Page | Evidence of Need | Backend API Exists |
|-------------|-----------------|-------------------|
| Candidate job search / apply page | `candidate.ts:12` — `searchJobs()`, `candidate.ts:14` — `applyJob()` | Partially (to verify) |
| Candidate interview detail page | `interviews/candidate_urls.py` — full endpoint set | Yes |
| Candidate notification preferences | Profile section expected | Not audited |

### Company Side Missing Visibility

- Passport visibility controls (`visibility_settings`) not surfaced in company/agency candidate view UI — company sees all passport fields regardless of candidate's visibility preferences

---

## 10. Broken Flows

### CRITICAL BREAK #1 — Candidate Apply Endpoint Not Confirmed
- **Frontend**: `candidate.ts:14` — `POST /jobs/{jobId}/apply/`
- **Backend**: Not found in `jobs/urls.py`, `pipeline/urls.py`, or `candidates/urls.py`
- `config/urls.py:23` includes `candidates.apply_urls` — this file was not audited; may contain the route
- **Action Required**: Verify `candidates/apply_urls.py` exists and correctly wires the apply endpoint; if missing, create it

### CRITICAL BREAK #2 — Candidate Application List Endpoint Not Confirmed
- **Frontend**: `candidate.ts:5` — `GET /candidate/applications/`
- **Backend**: Not found in `candidates/urls.py` (lines 14–75), `pipeline/urls.py` (lines 1–23)
- Same unverified `candidates.apply_urls` include
- **Action Required**: Confirm or create backend route

### CRITICAL BREAK #3 — Interview Model Has No Django ForeignKeys
- **File**: `interviews/models.py:368–370`
- `application_id`, `candidate_id`, `requisition_id` are plain `UUIDField`s
- **Consequences**: No cascade delete, no ORM joins, no prefetch_related, manual joins in all queries
- **Action Required**: Convert to `ForeignKey` fields with appropriate `on_delete` behavior

### CRITICAL BREAK #4 — Passport-Candidate Link Is Asymmetric / Weak
- **Files**: `passport/models.py:10`, `candidates/models.py:265`
- Both sides use plain `UUIDField`; no Django FK in either direction
- `MyPassportView` creates passport at `passport/views.py:42–43` without setting `candidate_id`
- **Consequence**: No ORM relationship; sync is manual; passport can exist without candidate link
- **Action Required**: Add proper `ForeignKey` from TalentPassport to Candidate

### CRITICAL BREAK #5 — Candidate Cannot Self-Access Profile via Company Endpoint
- **File**: `candidates/views.py:287–300`
- `CandidateListView.get()` filters by `tenant_id=request.user.tenant_id`
- A candidate user (with `tenant_id=NULL` for self-registered) gets empty queryset
- **Consequence**: Candidate cannot retrieve their own profile via `/api/v1/candidates/{id}/`
- **Action Required**: Add dedicated `CandidateProfileView` at `/api/v1/candidate/profile/` filtered by `user_id`

### CRITICAL BREAK #6 — Application Status Values Inconsistency
- **Files**: `pipeline/models.py:12–26` vs `pipeline/views.py:44–56`
- Company code references statuses (`submitted`, `placement`, `under_review`, `client_review`) not in model choices
- **Consequence**: Writing these statuses may fail validation or store invalid strings silently
- **Action Required**: Reconcile enum; add missing choices to model or remove from view logic

### HIGH BREAK #7 — No Candidate Record Created After Passport Import
- **File**: `passport/urls.py:22` — `PassportImportView` logs import to `PassportAccessLog` but no candidate creation visible
- **Consequence**: Company imports passport → no `Candidate` record created → must manually add candidate afterwards
- **Action Required**: Implement post-import candidate creation with field merge

### MEDIUM BREAK #8 — Interview Execution Mode Enum Mismatch
- **File**: `interviews/models.py:381–385` vs interview type registry `lines:100–174`
- Registry includes `manual`, `async` modes not in Interview model choices
- **Action Required**: Reconcile execution mode enum values

---

## 11. Recommended Fix Order

### Critical (Fix Immediately)

**1. Verify and Document Candidate Apply + Applications Flow**
- Audit `candidates/apply_urls.py`
- Confirm `POST /api/v1/candidate/applications/` (apply to job) and `GET /api/v1/candidate/applications/` exist
- If missing: create `CandidateApplyView` and `CandidateApplicationListView`
- Files: `candidates/apply_urls.py`, `candidates/views.py`, `config/urls.py`
- Effort: Medium (1–2 days)

**2. Add Candidate Self-Access Permission Filter**
- Create `CandidateProfileView` → `/api/v1/candidate/profile/`
- Filter: `Candidate.objects.filter(user_id=request.user.id)`
- Files: `candidates/views.py`, `candidates/urls.py`
- Effort: Low (1 day)

**3. Reconcile Application Status Enum**
- Audit all code setting `Application.status` to values like `submitted`, `placement`
- Option A: Add missing choices to `Application.status` (`pipeline/models.py`)
- Option B: Remove mismatched values from company view code (`pipeline/views.py`)
- Generate migration if Option A
- Files: `pipeline/models.py`, `pipeline/views.py`
- Effort: Medium (1–2 days)

**4. Fix Passport-Candidate Link**
- Add `ForeignKey`: `TalentPassport.candidate = ForeignKey('candidates.Candidate', null=True, blank=True, on_delete=SET_NULL)`
- Remove weak `candidate_id` UUIDField
- Update `MyPassportView` to set `candidate` on creation
- Files: `passport/models.py`, `passport/views.py`
- Effort: High (2–3 days, requires migration)

**5. Fix Interview Model ForeignKeys**
- Convert `application_id`, `candidate_id`, `requisition_id` to proper `ForeignKey` fields
- Update serializers to use `select_related`/`prefetch_related`
- Files: `interviews/models.py`, `interviews/serializers.py`, `interviews/views.py`
- Effort: High (3–4 days, requires migration + serializer updates)

### High (Fix Within 1 Sprint)

**6. Hide Recruiter-Internal Fields from Candidate-Facing Serializer**
- Create `CandidateSelfSerializer` with only candidate-visible fields
- Fields to exclude: `workflow_mode`, `engagement_stage`, `readiness_score`, `fit_score`, `owner_user_id`, `assigned_to`, `created_by`, `source_type`, `duplicate_of`, `is_duplicate`, `tenant_id`
- Apply context-based serializer selection in views
- Files: `candidates/serializers.py`, `candidates/views.py`
- Effort: Medium (1–2 days)

**7. Implement Passport Import → Candidate Creation**
- After import, create or reuse `Candidate` record (dedup by email/phone)
- Merge fields: `current_title`, `current_company`, `location`, `experience_years`, `skills`, `languages`
- Set `source='passport'`, link via FK
- Files: `passport/views.py`, `candidates/models.py`
- Effort: High (2–3 days)

**8. Complete and Audit Candidate Interview List View**
- Fully audit `CandidateInterviewListView` implementation
- Confirm different serializer used (not recruiter serializer)
- Confirm feedback/scores/anti-cheat fields hidden from candidate view
- Files: `interviews/views.py`, `interviews/serializers.py`
- Effort: Medium (1–2 days)

**9. Create Candidate-Specific Application Serializer**
- Create `CandidateApplicationSerializer` — hide `ApplicationStageHistory`, internal notes, moved_by
- Apply to `/candidate/applications/` endpoint
- Files: `pipeline/serializers.py`
- Effort: Medium (1–2 days)

### Medium (Fix Within 2 Sprints)

**10. Implement Passport ↔ Candidate Field Sync**
- When passport updated, sync overlapping fields to `Candidate` (with consent model)
- Mark `Candidate` as stale when passport updated
- Files: `passport/views.py`, `candidates/models.py`
- Effort: High (2–3 days)

**11. Reconcile Interview Execution Mode Enum**
- Unify Interview model enum and interview type registry
- Add `manual`, `async` to Interview choices or remove from registry defaults
- Files: `interviews/models.py`
- Effort: Low (1 day)

**12. Enforce `retention_scope` in Agency Visibility Queries**
- Verify `retention_scope` choices (`job_only`, `view_only`, `limited_company_access`) are enforced in query layer
- Files: `agencies/views.py`, `candidates/views.py`
- Effort: Medium (1–2 days)

### Low (Fix Within 3 Sprints)

**13. Candidate Visibility Settings UI**
- Build React form for `TalentPassport.visibility_settings` toggles
- Files: `pages/candidate/`, `api/passport.ts`
- Effort: Medium (1–2 days)

**14. Add N+1 Prefetch Hints to Interview Queries**
- After FK fix (#5), add `prefetch_related('application', 'candidate', 'requisition')` to interview querysets
- Files: `interviews/views.py`
- Effort: Low (1 day)

**15. Candidate-Agency Link Model**
- Create explicit `CandidateAgencySubmission` model for traceability
- Enables retention enforcement and candidate-visible agency attribution
- Effort: Medium (1–2 days)

---

## Summary Table

| Flow | Status | Critical Issues |
|------|--------|-----------------|
| Candidate Direct Signup | Partial | Mostly built; apply endpoint unconfirmed |
| Company Adds Candidate | Built | Dedup works; claim flow partially visible |
| Agency Adds/Submits Candidate | Built | No explicit agency-candidate FK model |
| Public Passport / Share Link | Built | Privacy controls present |
| Candidate Apply to Job | **Broken** | No confirmed backend endpoint |
| Candidate My Applications | **Broken** | No confirmed `GET /candidate/applications/` route |
| Interview Scheduling (Recruiter) | Built | Recruiter side works |
| Candidate Interview View | Partial | Endpoint exists; view implementation not fully audited |
| Application Status Consistency | **Issue** | Enum mismatch: company uses status values not in model |
| Passport-Candidate Sync | Partial | Weak UUID link; no ORM FK; no auto-sync |
| Tenant Isolation (Company) | Built | Explicit filter in views.py |
| Tenant Isolation (Candidate Self) | **Missing** | No user_id-based filter in company endpoint |
| Recruiter Field Leakage | **Issue** | CandidateSerializer exposes internal fields |
| Interview FK Integrity | **Broken** | UUIDs not Django ForeignKeys |
| Passport Import Flow | Partial | Logs import; no candidate creation |
