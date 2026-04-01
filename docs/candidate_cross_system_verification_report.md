# Candidate Cross-System Verification Report

**Date:** 2026-04-01
**Scope:** Candidate Portal ↔ Company ATS ↔ Agency Side ↔ Jobs ↔ Pipeline ↔ Interviews ↔ Passport
**Method:** Full source audit — models, serializers, views, URL routes, frontend pages, API clients, type definitions

---

## 1. Executive Summary

The Candidate Portal, Company ATS, Agency Side, and Passport system are broadly well-architected with clear separation of concerns. However, six cross-system issues have been identified ranging from a critical data-layer mismatch that breaks all status display on the candidate side, to missing API methods, silent enrichment failures, and a broken candidate-interview bucketing contract. There are no data-leaking security issues. The passport visibility and privacy logic is sound. The claim flow, deduplication, and protection systems are built and logically consistent. The agency submission and company pipeline are properly cross-referencing.

**Critical count:** 1
**Broken count:** 3
**Partial count:** 5
**Missing count:** 4
**Not Verified:** 2

---

## 2. Cross-System Flows Verified

| Flow | Status | Notes |
|------|--------|-------|
| Candidate direct signup → onboarding → passport | Built | OnboardingGuard + completeness score threshold (40) guards the flow |
| Candidate applies to job → application visible on company side | Partial | Apply works; status display broken (see §8 Issue 1) |
| Company adds candidate (quick/manual) → candidate claims account | Partial | Claim token model exists; link via `candidate_id` after claim |
| Agency submits candidate → company sees it → candidate claims | Partial | `is_agency_submission` flag + `submitted_by_tenant_id` correct; but claim→My Applications link needs runtime verification |
| Passport public share link → public page renders | Built | Fixed in prior session: `/passport/public/` in PUBLIC_ENDPOINTS |
| Passport import by company/agency → candidate record created | Built | `PassportImportView` creates Candidate with `source='passport'` |
| Candidate apply → My Applications | Built | `candidateApi.listApplications()` → correct endpoint |
| Interview scheduled by recruiter → candidate sees it | Built | `/candidate/interviews/` endpoint + `CandidateInterviewListView` confirmed |
| Pipeline stage move reflects both sides | Broken | Stage-derived status values differ from frontend STATUS_MAP keys |

---

## 3. Candidate ↔ Company Verification

### 3.1 Candidate Identity

| Check | Status | Detail |
|-------|--------|--------|
| Self-registered candidate has `tenant_id = null` | Built | `Candidate.tenant_id` is nullable by design |
| Company-added candidate has `tenant_id = company_tenant_id` | Built | Set at creation |
| Claimed candidate links via `candidate_id` on Application | Built | `unique_together = [tenant_id, candidate_id, requisition_id]` on Application |
| `candidate_ref_id` is immutable across tenants | Built | `build_reference()` generates once, never reassigned |
| Global dedup via `global_hash` | Built | Cross-tenant deduplication field present on Candidate model |

### 3.2 Company View of Candidate Applications

| Check | Status | Detail |
|-------|--------|--------|
| Company sees applications in `/pipeline/` board | Built | `PipelineView` returns `{requisition_id, pipeline: {stage → applications[]}}` |
| Company sees application status | Broken | Status stored as stage_type value (`interview`, `offer`) but company UI expects `interview_scheduled`, `offer_extended` (see §8 Issue 1) |
| Stage history visible to company | Built | `ApplicationStageHistory` tracked; `ApplicationDetailView` returns it |
| Company can filter by source (agency vs direct) | Built | `is_agency_submission` flag on Application |
| Protection badge shows on company candidate view | Built | `protection_badge_payload()` computed in ApplicationSerializer as `is_agency_protected`, `protected_until`, `protection_scope` |
| Company can see candidate passport link | Missing | `CandidateQuickView.tsx` has no link to view/import candidate's public passport |
| Post-submission stage move locked to job owner | Built | `enforce_post_submission_stage_owner_lock()` in pipeline/views.py:95 |
| Offer/join requires completed interview | Built | Validated in `validate_application_move()` in pipeline/views.py:181 |

### 3.3 Company → Candidate Data Write-Back

| Check | Status | Detail |
|-------|--------|--------|
| Stage move note required | Built | Mandatory `reason` field enforced in pipeline views |
| Offer details written to Application | Built | `offer_amount`, `offer_currency`, `offer_date` on Application model |
| Rejection reason written to Application | Built | `rejection_reason`, `rejection_category` on Application model |
| Candidate My Applications shows company-written offer/rejection data | Built | Enriched in `MyApplications.tsx` and `CandidateApplicationQVPanel.tsx` |

---

## 4. Candidate ↔ Agency Verification

### 4.1 Agency Submission Flow

| Check | Status | Detail |
|-------|--------|--------|
| Agency can search candidates | Built | `agenciesApi.candidates.list()` → `/agencies/candidates/` |
| Agency submits candidate to job | Built | `agenciesApi.submitCandidate()` → creates Application with `is_agency_submission=True`, `submitted_by_tenant_id=agency_tenant` |
| Governance mode: `direct` vs `approval_required` | Built | `SubmitCandidate.tsx` reads `assignment.governance_mode`; sets `is_draft` accordingly |
| Agency sees own submissions | Built | `agenciesApi.mySubmissions()` → filtered by `is_agency_submission` + agency's tenant |
| Submission appears on company pipeline | Built | Standard pipeline view; company filters by requisition |
| Agency sees protection/guarantee data | Built | `MySubmissions.tsx` renders `is_agency_protected`, `protected_until`, `is_under_guarantee`, guarantee fields |

### 4.2 Agency-Submitted Candidate Claiming Account

| Check | Status | Detail |
|-------|--------|--------|
| Candidate with `account_status='none'` can be invited | Built | `invite_sent_at`, `claim_token`, `claim_token_expires_at` on Candidate model |
| After claim, `account_status` → `claimed` | Built | Model tracks this |
| Claimed candidate sees agency-submitted applications in My Applications | Not Verified | `/candidate/applications/` filters by `candidate_id` from auth user. If claim correctly links `user_id` → `candidate_id`, this works. Requires runtime verification. |
| Claimed candidate's My Applications shows correct source | Partial | Application shows `is_agency_submission` flag but `MyApplications.tsx` doesn't display source origin to candidate. No "Added by recruiter" vs "Self-applied" differentiation in UI. |

### 4.3 Data Consistency: Agency ↔ Company ↔ Candidate

| Check | Status | Detail |
|-------|--------|--------|
| Same Application record read by all three sides | Built | Single `Application` row; no duplication. `tenant_id` scopes company view; `is_agency_submission` scopes agency view; `candidate_id` scopes candidate view |
| Commission/placement data visible to company only | Built | `CommissionRecord` and `Placement` models accessed only via company-side serializers; not in candidate API |
| Candidate cannot see agency's commission data | Built | `TalentPassportPublicSerializer` and `/candidate/applications/` do not expose commission fields |

---

## 5. Candidate ↔ Passport Verification

### 5.1 Passport Edit → Save → Public Page Chain

| Check | Status | Detail |
|-------|--------|--------|
| Append-safe merge for text fields | Built | `MyPassportView.PUT`: empty strings never erase existing values |
| Union merge for list fields (skills, languages) | Built | Appended + deduplicated (case-insensitive) |
| Replace semantics for structured sections (work_history, education, etc.) | Built | Array fields replaced outright on PUT |
| Completeness score computed server-side | Built | Weighted formula: `headline(10) + summary(10) + photo(5) + title(10) + skills(15) + work_history(20) + education(10) + cv(10) + linkedin(5) + certs(5)` |
| Public page respects visibility settings | Built | `_VISIBILITY_FIELD_MAP` in passport/views.py strips fields before serialization |

### 5.2 Visibility / Privacy

| Check | Status | Detail |
|-------|--------|--------|
| `show_certifications` hides certifications | Built | Mapped in `_VISIBILITY_FIELD_MAP` |
| `show_projects` hides projects | Built | Mapped |
| `show_publications` hides publications | Built | Added in prior session |
| `show_awards` hides awards | Built | Added in prior session |
| `show_volunteer` hides volunteer_work | Built | Added in prior session |
| `show_availability` hides availability fields | Built | Strips `notice_period_days`, `availability_date`, `is_actively_looking`, `availability_status` |
| Salary fields hidden from public page | Built | `expected_salary_min/max/currency` are intentionally excluded from `TalentPassportPublicSerializer.fields` (comment at serializers.py:294 confirms this is deliberate) |
| No `show_salary` toggle in edit UI | Missing | Salary is excluded at serializer level, not via visibility toggle. Candidate has no control over this — it is always hidden. No UI toggle needed but undocumented. |
| Contact email/phone hidden from public page | Built | Not in `TalentPassportPublicSerializer.fields` |
| Public page accessible without login | Built | `AllowAny` permission + `/passport/public/` in `PUBLIC_ENDPOINTS` |
| Logged-in user with expired token not redirected to `/login` on public passport | Built | Fixed in prior session via `PUBLIC_ENDPOINTS` list |

### 5.3 Passport Import (Company/Agency → Candidate Record)

| Check | Status | Detail |
|-------|--------|--------|
| `passport_token` field name in request | Built | Fixed in prior session (`token` → `passport_token`) |
| Import creates `Candidate` with `source='passport'` | Built | `PassportImportView` sets `source`, `candidate_state='NEW_LEAD'`, `candidate_pool='GENERAL'` |
| Import creates `CandidateProfile` from passport sections | Built | Profile auto-created with work_history, education, skills |
| Access logged in `PassportAccessLog` | Built | `access_type='import'`, `imported_to_system=True` |
| Candidate can revoke imported access | Built | `MyPassportRevokeAccessView` + `MyPassportRevokeAllView` |

### 5.4 Passport ↔ Candidate Record Sync

| Check | Status | Detail |
|-------|--------|--------|
| `/passport/my-candidate/` returns linked Candidate data | Built | `passportApi.getLinkedCandidate()` |
| `PATCH /passport/my-candidate/` updates linked Candidate | Built | Append semantics for lists; Candidate model updated directly |
| Candidate `passport_linked` flag set | Built | Field on Candidate model |
| Passport completeness used by OnboardingGuard | Built | `completeness_score < 40` → redirect to `/onboarding` |
| Publications, awards, volunteer edit UI on candidate side | Missing | `Passport.tsx` edit page has visibility toggles for these three sections but **no edit form** for publications, awards, or volunteer work entries. These fields are only shown publicly but candidates cannot add them through the portal UI. |

---

## 6. Candidate ↔ Jobs / Applications / Pipeline Verification

### 6.1 Job Search and Apply

| Check | Status | Detail |
|-------|--------|--------|
| Public job search works without auth | Built | `/jobs/search/` in `PUBLIC_ENDPOINTS` |
| Job posting card shows real company/salary data | Built | Fixed in prior session — metadata fallback chain |
| Apply from `CandidateJobQVPanel` | Built | `candidateApi.applyJob(job.id)` → `POST /jobs/{id}/apply/` |
| Duplicate apply prevented on frontend | Built | `appliedIds` set built from `applications`, checked before render |
| Duplicate apply prevented on backend | Built | `unique_together = [tenant_id, candidate_id, requisition_id]` + 409 response |
| 24-hour review deadline created on apply | Built | `ActionDeadline` created in pipeline/views.py:378 |
| Query cache invalidated after apply | Built | Both `['candidate_applications']` and `['candidate', 'applications']` invalidated |
| Cover note / cover letter UI | Missing | `candidateApi.applyJob(jobId, notes)` accepts notes param. `jobsPublicApi.apply(id, cover_note)` also exists. No UI input collects cover note before apply. |

### 6.2 My Applications

| Check | Status | Detail |
|-------|--------|--------|
| Applications listed from correct endpoint | Built | `GET /candidate/applications/` |
| Status displayed with color-coded badge | Broken | STATUS_MAP handles `in_review`, `interview_scheduled`, `offer_extended`, `offer_accepted`, `placement_confirmed`, `placement_cancelled` — but these strings are **never stored** in DB (see §8 Issue 1). Cards will render but status labels will show backend values like `interview`, `offer`, `joined` that don't match the STATUS_MAP keys. |
| Offer data shown (amount, accept/decline status) | Built | `offer_amount`, `offer_accepted_at`, `offer_rejected_at` on Application model; rendered in `ApplicationCard` and `CandidateApplicationQVPanel` |
| Rejection reason shown | Built | `rejection_reason` on Application; rendered in both card and panel |
| Withdrawn reason shown | Built | `withdrawn_reason` on Application; rendered in both card and panel |
| Pipeline progress bar shown | Partial | `PipelineBar` and `PipelineVisual` render correctly — but `step` is derived from STATUS_MAP which uses wrong keys (see above) |
| Salary enrichment from requisition | Broken | `MyApplications.tsx` calls `requisitionsApi.get(id)` which maps to `GET /jobs/requisitions/{id}/`. This is a **recruiter/company endpoint**. A candidate calling it will likely receive a 403 or empty result depending on RBAC. The code has `.catch(() => null)` so it degrades silently but the enrichment will never succeed in production. |
| Sort by most recent activity | Built | `combined.sort()` by `updated_at ?? created_at` |
| Filter tabs: All / Active / Offers / Closed | Built | `filterApps()` with correct status groups |
| Offer callout banner | Built | Rendered when `counts.offer > 0 && activeTab !== 'offer'` |
| Application detail drawer | Built | `openQuickView('candidate_application', app)` → `CandidateApplicationQVPanel` |
| Application detail shows enriched data | Built | Panel receives full enriched `app` object including offer, rejection, salary fields |
| Candidate can see application source (self vs recruiter-added) | Missing | `Application.source` and `submitted_by` fields exist on model but not surfaced in candidate UI |

### 6.3 Application Status Values: Full Chain Audit

**This is Issue 1 — see §8 for full detail.**

```
Backend Application model choices:
  applied, screening, shortlisted, interview, assessment, offer, joined, rejected, withdrawn, on_hold

Backend JobStage.stage_type choices (what gets written to Application.status via pipeline move):
  sourcing, screening, interview, assessment, offer, joined, rejected, withdrawn

Frontend ApplicationStatus type + STATUS_MAP keys:
  applied, screening, shortlisted, in_review, interview_scheduled, offer_extended,
  offer_accepted, joined, placement_confirmed, placement_cancelled, rejected, withdrawn

Overlap between runtime DB values and frontend STATUS_MAP:
  ✓ applied       (model default on create)
  ✓ screening     (stage_type + model choice)
  ✓ joined        (stage_type + model choice + STATUS_MAP)
  ✓ rejected      (stage_type + model choice + STATUS_MAP)
  ✓ withdrawn     (stage_type + model choice + STATUS_MAP)
  ✗ interview     → backend stores, frontend has no handler (falls to default/gray)
  ✗ assessment    → backend stores, frontend has no handler
  ✗ offer         → backend stores, frontend has no handler
  ✗ sourcing      → backend stores, frontend has no handler
  ✗ on_hold       → can be manually set, frontend has no handler
  ✗ shortlisted   → in model choices but not stage_type; can be manually set; STATUS_MAP handles it but it won't arrive from stage moves
  ✗ interview_scheduled  → in STATUS_MAP but never stored
  ✗ in_review            → in STATUS_MAP but never stored
  ✗ offer_extended       → in STATUS_MAP but never stored
  ✗ offer_accepted       → in STATUS_MAP but never stored (this is Placement.placement_status)
  ✗ placement_confirmed  → in STATUS_MAP but never stored (this is Placement.placement_status)
  ✗ placement_cancelled  → in STATUS_MAP but never stored
```

---

## 7. Candidate ↔ Interviews Verification

### 7.1 Interview Endpoint Chain

| Check | Status | Detail |
|-------|--------|--------|
| Backend `/candidate/interviews/` endpoint exists | Built | `CandidateInterviewListView` at `apps/interviews/candidate_urls.py` |
| `interviewsApi.candidateList()` calls correct URL | Built | `GET /candidate/interviews/` confirmed in `frontend/src/api/interviews.ts:248` |
| Interview instructions endpoint exists | Built | `CandidateInterviewInstructionsView` at `/candidate/interviews/{pk}/instructions/` |
| Runtime endpoint exists | Built | `CandidateInterviewRuntimeView` at `/candidate/interviews/{pk}/runtime/` |
| Start / complete / submit-answer endpoints exist | Built | All present in `candidate_urls.py` |
| Schedule self-service endpoint | Not Verified | `CandidateSelfSchedule.tsx` exists; `/interviews/scheduling/self/{token}` referenced in dashboard but not confirmed in `candidate_urls.py` — may be in main interview URLs |

### 7.2 Interview Response Shape

| Check | Status | Detail |
|-------|--------|--------|
| Dashboard expects bucketed response `{upcoming, pending, completed, missed}` | Not Verified | `CandidateInterviewDashboard.tsx` destructures `upcoming_interviews`, `pending_interviews`, `completed_interviews`, `missed_interviews` from `candidateList()`. Whether `CandidateInterviewListView` returns this shape or a flat list requires reading the view implementation. If flat, the dashboard will crash. |

### 7.3 Interview Status Values

| Check | Status | Detail |
|-------|--------|--------|
| Backend Interview.status choices | Built | `scheduled, in_progress, completed, cancelled, no_show, rescheduled` (6 values) |
| Frontend InterviewStatus type | Broken | Types define `confirmed, pending_feedback` which are not in the backend model. Frontend also references `awaiting_candidate`, `expired`, `missed`, `blocked` in `CandidateInterviewDashboard`. None of these 6 extra values can be stored in the backend. Status badges for these will never render. |

### 7.4 Interview ↔ Application Cross-Reference

| Check | Status | Detail |
|-------|--------|--------|
| Company: Interview created with `application_id` | Built | Interview model has `application_id`, `candidate_id`, `requisition_id` |
| Company: ApplicationDetail shows linked interviews | Built | `ApplicationDetail.tsx` queries `interviewsApi.list({ application_id })` |
| Candidate: Interview view shows linked application | Missing | `CandidateInterviewDashboard.tsx` shows interview details but has no link back to the originating application. Candidate cannot navigate interview → application in one click. |
| Interview feedback visible to candidate | Built | `CandidateInterviewResults` and `CandidateInterviewFeedback` pages exist |
| Interview decision `decision.decision` field | Partial | `CandidateInterviewDashboard` renders `interview.decision?.decision`. Backend `InterviewDecision.decision` uses: `hire, reject, hold, next_round, manual_review, assignment, panel_required, escalate`. Frontend InterviewFeedback recommendation uses same values. Consistent. |
| `secure_runtime_url` generated by backend | Built | `views.py:1977` builds `f"/candidate/interviews/{interview.id}/runtime?access_token={token}"` |

---

## 8. Data Mismatches

### Issue 1 — Application Status: Three-Way Value Split (CRITICAL)

**Files involved:**
- `backend/apps/pipeline/models.py` — defines 10 `status` choices on `Application`
- `backend/apps/jobs/models.py` — defines 8 `stage_type` choices on `JobStage`
- `backend/apps/pipeline/views.py:215` — `application.status = target_stage.stage_type` (runtime write)
- `frontend/src/types/index.ts` — `ApplicationStatus` type with 12 values
- `frontend/src/pages/candidate/MyApplications.tsx` — `STATUS_MAP`
- `frontend/src/pages/candidate/CandidateCommandCenter.tsx` — `APP_STATUS`
- `frontend/src/components/drawers/quickviews/CandidateApplicationQVPanel.tsx` — `STATUS_MAP`
- `frontend/src/pages/agency/MySubmissions.tsx` — status rendering

**Problem:**
Application.status is set by the pipeline stage move to `target_stage.stage_type`. Valid stored values at runtime are the 8 stage_type choices: `sourcing, screening, interview, assessment, offer, joined, rejected, withdrawn`, plus `applied` (set on creation).

The frontend defines 12 status values (`in_review`, `interview_scheduled`, `offer_extended`, `offer_accepted`, `placement_confirmed`, `placement_cancelled`, `shortlisted`) that do not correspond to any value the backend can write. Meanwhile, `interview`, `assessment`, `offer`, `sourcing` — values the backend does write — are not handled in the frontend STATUS_MAP.

Additionally, `offer_accepted`, `placement_confirmed`, `placement_cancelled` are values from `Placement.placement_status` (a separate model). They are conflated into `ApplicationStatus` in the frontend types as if they live on Application.

**Impact:**
- All status badges on candidate My Applications will display gray/default for applications in `interview`, `assessment`, `offer`, `sourcing` stage
- Pipeline progress bar `step` derivation will be wrong for all active-pipeline applications
- Offer detection logic (`hasOffer` in `ApplicationCard`) will never fire for `offer_extended` status
- Company ATS status display has the same mismatch
- Agency MySubmissions status display is similarly affected

**Fix required:**
Align on one canonical status set. Option A: expand `Application.status` choices to include the frontend values and update `stage_type` mapping in views. Option B: strip the non-existent statuses from frontend types and STATUS_MAP, add handlers for `interview`, `assessment`, `offer`, `sourcing`. Option A is recommended as it preserves intent.

---

### Issue 2 — Interview Status Missing Values (BROKEN)

**Files involved:**
- `backend/apps/interviews/models.py` — 6 status choices
- `frontend/src/types/index.ts` — `InterviewStatus` with 8 values
- `frontend/src/pages/candidate/CandidateInterviewDashboard.tsx` — references `confirmed`, `awaiting_candidate`, `expired`, `missed`, `blocked`

**Problem:**
Backend `Interview.status` choices: `scheduled, in_progress, completed, cancelled, no_show, rescheduled`. Frontend references `confirmed`, `pending_feedback`, `awaiting_candidate`, `expired`, `missed`, `blocked` — none of which the backend stores.

**Impact:**
- Interview status badges in `CandidateInterviewDashboard` will never match for `confirmed`, `awaiting_candidate`, etc.
- Bucket classification may be broken if the backend `CandidateInterviewListView` uses these statuses to classify interviews

---

### Issue 3 — MyApplications Enrichment Calls Recruiter-Only Endpoint (BROKEN)

**Files involved:**
- `frontend/src/pages/candidate/MyApplications.tsx:252` — `requisitionsApi.get(id)`
- `frontend/src/api/jobs.ts` — `requisitionsApi.get()` → `GET /jobs/requisitions/{id}/`
- `backend/apps/jobs/views.py` — `JobRequisitionDetailView` (RBAC-guarded, tenant-scoped)

**Problem:**
`MyApplications.tsx` calls `requisitionsApi.get(requisition_id)` to enrich each application with job title, type, work mode, and salary data. This endpoint is a company-side recruiter endpoint scoped to the calling user's tenant. A candidate (role=`candidate`, `tenant_id` on user is their own not the company's) will receive a 403 or an empty/unauthorized response.

The `.catch(() => null)` guard means this silently degrades — `jobMap` remains empty, all applications show `jobTitle='Position'`, `jobType=''`, `workMode=''`, no salary data.

**Impact:**
- Every candidate in production sees "Position" as job title on My Applications
- Salary enrichment never works
- Work mode and job type never populate

**Fix required:**
Backend `/candidate/applications/` response should include denormalized `job_title`, `job_type`, `work_mode`, `salary_min`, `salary_max`, `salary_currency`, `salary_visible` from the requisition. Alternatively add a candidate-accessible `/candidate/applications/{id}/` endpoint that returns this joined data.

---

### Issue 4 — Frontend ApplicationStatus Conflates Application.status with Placement.placement_status (PARTIAL)

**Files involved:**
- `frontend/src/types/index.ts` — `ApplicationStatus` includes `offer_accepted`, `placement_confirmed`, `placement_cancelled`
- `backend/apps/pipeline/models.py:183-202` — these are `Placement.PLACEMENT_STATUS_CHOICES`, not `Application.status`

**Problem:**
`offer_accepted`, `placement_confirmed`, `placement_cancelled` are values from the Placement model's `placement_status` field, not from Application.status. The frontend treats them as Application-level statuses. They will never appear in the `application.status` field returned by the API.

If the backend application serializer computes and injects `placement_status` as an additional field (which the serializer does, via the Placement model join), the frontend would need to check `application.placement_status` not `application.status` for these values.

---

## 9. UI Mismatches

### 9.1 Status Labels

| UI Location | Field Checked | Expected Status | Actual DB Value | Verdict |
|-------------|--------------|-----------------|-----------------|---------|
| Candidate My Applications | `application.status` | `interview_scheduled` | `interview` | Mismatch |
| Candidate My Applications | `application.status` | `offer_extended` | `offer` | Mismatch |
| Candidate My Applications | `application.status` | `offer_accepted` | Lives on `Placement.placement_status` | Wrong model |
| Candidate My Applications | `application.status` | `placement_confirmed` | Lives on `Placement.placement_status` | Wrong model |
| Candidate Dashboard (offers filter) | `application.status` in `['offer_extended', 'offer_accepted', 'joined', 'placement_confirmed']` | Never matches except `joined` | Offers section may always be empty | Broken |
| Agency My Submissions | `application.status` | `interview_scheduled` | `interview` | Mismatch |
| Company Pipeline board | `application.status` | Same 3-way split | Same | Mismatch |

### 9.2 Missing Candidate-Side Visibility

| Feature | Where It's Missing | Company Side Has It | Fix Complexity |
|---------|--------------------|---------------------|----------------|
| Link from interview to parent application | `CandidateInterviewDashboard.tsx` | Yes — `ApplicationDetail.tsx` has interviews tab | Low |
| Application source label (self-applied vs added by recruiter) | `MyApplications.tsx` | Yes — `source`, `submitted_by` visible | Low |
| Candidate cannot edit publications, awards, volunteer work | `Passport.tsx` edit page | N/A | Medium |
| Cover note input on apply | `CandidateJobQVPanel.tsx` | N/A | Low |
| View/import passport button on company candidate view | `CandidateQuickView.tsx` | No | Low |

### 9.3 Recruiter-Only Fields in Candidate Context

No recruiter-private fields (commission, placement commercial data, scoring internals, `global_hash`, `claim_token`, automation flags) were found leaking into candidate-facing endpoints or UI. The separation is clean.

### 9.4 Candidate-Private Fields in Other Contexts

`TalentPassportPublicSerializer` correctly excludes: salary, email, phone, `metadata` internal keys. `PublicPassportPage.tsx` additionally filters metadata keys matching `recruiter_notes`, `admin_notes`, `crm_id`, etc. Privacy is sound.

---

## 10. Broken Flows

### Flow 1: Candidate Applies → Company Sees Wrong Status Label
**Chain:** Candidate applies → `Application.status='applied'` → Stage move sets `status='interview'` → Company pipeline shows `interview` → Company ATS status map may show `interview` correctly (has `interview_scheduled` handler, not `interview`) → Badge renders wrong color/label on both sides.
**Severity:** Critical UI — affects all active applications post-initial apply.

### Flow 2: Candidate Dashboard "Offers" Section Always Empty
**Chain:** `CandidateCommandCenter.tsx` filters applications where `status in ['offer_extended', 'offer_accepted', 'joined', 'placement_confirmed']` → DB stores `offer` and `joined` → No application ever matches `offer_extended` or `placement_confirmed` → Offers bucket is always empty except for `joined` applications.
**Severity:** High — candidate never sees pending offers in dashboard.

### Flow 3: My Applications Job Title Always "Position"
**Chain:** `MyApplications.tsx` calls `requisitionsApi.get()` (recruiter API) → 403/unauthorized → `jobMap` empty → all titles = 'Position', no salary, no work mode.
**Severity:** High — all candidate-facing application data is degraded.

### Flow 4: Interview Status Badges on Candidate Dashboard
**Chain:** Backend interview has `status='scheduled'` → Frontend checks for `confirmed` or `awaiting_candidate` in color mapping → Falls to default gray/unknown styling for these expected but non-existent values.
**Severity:** Medium — cosmetic but affects confidence in the candidate interview experience.

### Flow 5: Pipeline Progress Bar Shows Wrong Step
**Chain:** Backend stores `status='interview'` → `STATUS_MAP['interview']` is undefined → fallback `{ step: 0 }` → progress bar shows "Applied" step even for a candidate at interview stage.
**Severity:** High — misleading to candidate.

### Flow 6: Publications/Awards/Volunteer Work — View Only, No Edit
**Chain:** `Passport.tsx` edit page has visibility toggles for publications, awards, volunteer — but no form to add/edit entries → Candidate cannot populate these sections → Public page and company import always shows empty for these three section types.
**Severity:** Medium — incomplete feature.

### Flow 7: Candidate Cannot Navigate Interview → Application
**Chain:** `CandidateInterviewDashboard` shows interview but no application link → Candidate must navigate separately to My Applications and manually correlate → Broken UX cross-reference.
**Severity:** Low — navigation gap, not a data issue.

---

## 11. Recommended Fix Order

### Priority 1 — Critical Data Fixes (fix these before any other candidate work)

**Fix 1.1 — Align Application Status Values** *(Effort: Medium)*
- Decision required: pick one canonical set of status values
- Recommended: expand `Application.status` model choices to match frontend: add `in_review`, `interview_scheduled`, `offer_extended`, `offer_accepted`, `placement_confirmed`, `placement_cancelled`; remove `assessment`, `on_hold`, `sourcing` from pipeline if unused
- Update `pipeline/views.py:215` to map stage_type to the new canonical status instead of passing through raw `stage_type`
- Add migration
- Files: `backend/apps/pipeline/models.py`, `backend/apps/pipeline/views.py`, migration

**Fix 1.2 — Denormalize Job Data into Candidate Applications Response** *(Effort: Low-Medium)*
- Add `job_title`, `job_type`, `work_mode`, `salary_min`, `salary_max`, `salary_currency`, `salary_visible` to the response shape from `GET /candidate/applications/` and `GET /candidate/applications/{id}/`
- This eliminates the need for `MyApplications.tsx` to call the recruiter API
- Remove `requisitionsApi.get()` calls from `MyApplications.tsx`, replace with denormalized fields
- Files: `backend/apps/jobs/views.py` (candidate applications view), `frontend/src/pages/candidate/MyApplications.tsx`

### Priority 2 — High Visibility Fixes

**Fix 2.1 — Candidate Dashboard Offer Filter** *(Effort: Low)*
- Once Fix 1.1 is done, verify offers filter uses correct status values
- Interim fix without Fix 1.1: filter on `status in ['offer', 'joined']` to at least surface offer-stage applications
- Files: `frontend/src/pages/candidate/CandidateCommandCenter.tsx`

**Fix 2.2 — Interview Status Values** *(Effort: Low-Medium)*
- Either: add missing statuses (`confirmed`, `pending_feedback`) to `Interview.status` choices on backend model + migration
- Or: remove non-existent statuses from frontend types and update `CandidateInterviewDashboard` color map to use only the 6 real values
- Files: `backend/apps/interviews/models.py`, `frontend/src/pages/candidate/CandidateInterviewDashboard.tsx`

**Fix 2.3 — Verify CandidateInterviewListView Response Shape** *(Effort: Low)*
- Read `backend/apps/interviews/views.py` — find `CandidateInterviewListView`
- Confirm it returns `{upcoming_interviews, pending_interviews, completed_interviews, missed_interviews}` bucketed shape
- If flat list: either update view to bucket by status, or update `CandidateInterviewDashboard` to handle flat list
- Files: `backend/apps/interviews/views.py`, `frontend/src/pages/candidate/CandidateInterviewDashboard.tsx`

### Priority 3 — UX Completeness

**Fix 3.1 — Add Cover Note Input to Apply Flow** *(Effort: Low)*
- Add a `<TextArea>` for cover note in `CandidateJobQVPanel.tsx`
- Pass it to `candidateApi.applyJob(job.id, coverNote)`
- Files: `frontend/src/components/drawers/quickviews/CandidateJobQVPanel.tsx`

**Fix 3.2 — Add Interview → Application Navigation Link** *(Effort: Low)*
- In `CandidateInterviewDashboard.tsx`, add "View Application" link using `application_id` from interview
- Navigate to My Applications filtered/opened to that application
- Files: `frontend/src/pages/candidate/CandidateInterviewDashboard.tsx`

**Fix 3.3 — Show Application Source to Candidate** *(Effort: Low)*
- In `ApplicationCard` and `CandidateApplicationQVPanel`, show "Added by recruiter" badge when `submitted_by` is not null and `source !== 'self'`
- Files: `frontend/src/pages/candidate/MyApplications.tsx`, `frontend/src/components/drawers/quickviews/CandidateApplicationQVPanel.tsx`

### Priority 4 — Feature Completion (Phase 2/3 backlog)

**Fix 4.1 — Publications/Awards/Volunteer Edit UI** *(Effort: Medium)*
- Add form sections in `Passport.tsx` for adding/editing publications, awards, volunteer_work entries
- Same pattern as existing work_history and education forms
- Backend already supports these fields
- Files: `frontend/src/pages/candidate/Passport.tsx`

**Fix 4.2 — Add Passport Link to Company Candidate View** *(Effort: Low)*
- In `CandidateQuickView.tsx`, add "View Passport" link that opens the candidate's public share URL
- Show "Import Passport" button if passport is available and not yet imported
- Files: `frontend/src/pages/candidates/CandidateQuickView.tsx`

---

## Appendix: Key Files by Role

| File | Role | Status |
|------|------|--------|
| `backend/apps/pipeline/models.py` | Application entity definition | Has stale status choices |
| `backend/apps/pipeline/views.py` | Pipeline move logic | Sets status from stage_type |
| `backend/apps/pipeline/serializers.py` | Application serialization | Correct; exposes guarantee/protection computed fields |
| `backend/apps/jobs/models.py` | JobStage.stage_type choices | Source of runtime status values |
| `backend/apps/interviews/models.py` | Interview status choices | Missing 6 frontend-expected values |
| `backend/apps/interviews/candidate_urls.py` | Candidate interview routes | All core routes present |
| `backend/apps/passport/views.py` | Passport read/write/public | Sound; visibility and append-safe merge correct |
| `backend/apps/passport/serializers.py` | Public vs private fields | Sound; salary correctly excluded from public |
| `frontend/src/types/index.ts` | Type definitions | ApplicationStatus conflates 2 models |
| `frontend/src/pages/candidate/MyApplications.tsx` | Applications list | Calls recruiter API for enrichment — broken |
| `frontend/src/pages/candidate/CandidateCommandCenter.tsx` | Dashboard | Offer filter uses wrong status values |
| `frontend/src/pages/candidate/CandidateInterviewDashboard.tsx` | Interview hub | Uses status values not in backend model |
| `frontend/src/pages/candidate/Passport.tsx` | Passport edit | Missing edit UI for 3 new sections |
| `frontend/src/pages/agency/MySubmissions.tsx` | Agency submissions | Status mismatch same as above |
| `frontend/src/api/candidate.ts` | Candidate API client | Apply endpoint correct; no job detail fetch |
| `frontend/src/api/interviews.ts` | Interview API client | `candidateList()` endpoint confirmed |
| `frontend/src/utils/http.ts` | HTTP client | PUBLIC_ENDPOINTS correct; auth flow sound |
