# Candidate Portal Verification Report

**Date:** 2026-03-29
**Type:** Factual audit — no assumptions, no design proposals
**Scope:** Full candidate portal — backend, frontend, flows, guards, integrations

---

## 1. Executive Summary

The candidate portal is **substantially built** with most core flows functional. The interview runtime, onboarding wizard, claim flow, and public apply form are the most complete areas. The main gaps are:

- **Job apply has no UI entry point** — the backend endpoint and API client exist, but no Apply button is wired anywhere the candidate can see
- **Job detail / drawer is broken** — clicking a job card calls a drawer type (`candidate_job`) with no implementation
- **Passport regenerate share link is a hard 404** — URL mismatch between frontend and backend
- **Forgot password / reset password are non-functional stubs** — backend endpoints exist but do nothing
- **Post-registration flow has a navigation gap** — redirects to `/dashboard` instead of `/verify-email`, recoverable only via guard bounce
- **Phone field on registration is silently dropped** — collected by form, ignored by serializer
- **`needs_login` response from public apply is never checked** in the frontend

| Area | Overall Status |
|------|---------------|
| Auth (register/login/OTP) | Functional with gaps |
| Onboarding | Complete |
| Claim profile | Complete |
| Public apply form | Functional with gap |
| Job search | Partial — no apply UI |
| My Applications | Complete |
| Candidate interviews | Complete |
| Talent Passport | Partial — regenerate broken |
| Route guards | Complete |
| Forgot/reset password | Broken (stubs) |

---

## 2. Backend Verification

### 2.1 Auth — `/api/v1/auth/`

| Method | URL | View | Status | Notes |
|--------|-----|------|--------|-------|
| POST | `/auth/register/candidate/` | `RegisterCandidateView` | **Complete** | Dedup via identity_service; creates user role='candidate'; links existing candidate record; issues OTP; returns JWT |
| POST | `/auth/login/` | `LoginView` | **Complete** | Checks `email_verified`; updates `last_login_at`; returns JWT |
| POST | `/auth/send-otp/` | `SendOTPView` | **Complete** | Resend cooldown; user enumeration guard |
| POST | `/auth/verify-otp/` | `VerifyOTPView` | **Complete** | Max attempts; expiry; dev bypass `code=123456`; marks `email_verified`; returns fresh JWT |
| POST | `/auth/onboarding/complete/` | `CompleteOnboardingView` | **Broken for candidate role** | `_ROLE_TO_USER_TYPE` map excludes `candidate` — returns "Unsupported user role" if a candidate calls this endpoint. Candidate onboarding bypasses this endpoint entirely, so functionally not blocking, but it means candidate completion is not tracked via the same mechanism as company/agency. |
| POST | `/auth/logout/` | `LogoutView` | **Complete** | Blacklists refresh token |
| GET/PUT | `/auth/me/` | `MeView` | **Complete** | Returns and updates user profile |
| POST | `/auth/forgot-password/` | `ForgotPasswordView` | **Stub** | Returns generic success message. No token generated, no email sent. Non-functional. |
| POST | `/auth/reset-password/` | `ResetPasswordView` | **Stub** | Always returns `"Password reset successfully."` with no actual logic. Does not validate any token or change any password. |
| POST | `/auth/verify-email/` | `VerifyEmailView` | **Stub** | Legacy endpoint. Accepts any string token and returns success unconditionally. |
| POST | `/auth/refresh/` | `RefreshTokenView` | **Complete** | |
| POST | `/auth/change-password/` | `ChangePasswordView` | **Complete** | |
| POST | `/auth/mfa/enable/` | `MFAEnableView` | **Complete** | |
| POST | `/auth/mfa/verify/` | `MFAVerifyView` | **Complete** | |

**Note on OTP email delivery:** `_send_otp_email` only sends real email when `settings.ENVIRONMENT == 'production'`. In development it only logs to stdout. Must be verified at deployment time.

---

### 2.2 Candidates — `/api/v1/candidates/`

| Method | URL | View | Status | Notes |
|--------|-----|------|--------|-------|
| GET | `/candidates/check-identity/` | `CandidateIdentityCheckView` | **Complete** | Public endpoint; checks if user/candidate exists by email or phone |
| GET | `/candidates/claim/<token>/` | `CandidateClaimVerifyView` | **Complete** | Validates token, returns prefilled data, checks expiry |
| POST | `/candidates/claim/<token>/` | `CandidateClaimVerifyView` | **Complete** | Links authenticated user to candidate; email/phone identity safety check; handles already-claimed case |
| GET | `/apply/<token>/` | `PublicApplyFormView` | **Complete** | Returns `company_name`, `job_title`, `form_config` |
| POST | `/apply/<token>/submit/` | `PublicApplyFormView` | **Complete** | Full dedup: checks user/candidate; merges or creates; optional account creation; returns `access_token`. NOTE: returns `needs_login: true` if existing user found — frontend ignores this field |
| GET | `/candidates/` | `CandidateListView` | **Complete** | Recruiter-facing, permission-checked |
| GET | `/candidates/database/` | `CandidateDatabaseView` | **Complete** | Recruiter-facing |
| GET | `/candidates/<uuid>/` | `CandidateDetailView` | **Complete** | Recruiter-facing |
| GET/POST | `/candidates/invite-links/` | `InviteLinkListView` | **Complete** | Creates shareable apply links |
| POST | `/candidates/invite-links/<uuid>/deactivate/` | `InviteLinkDeactivateView` | **Complete** | |

---

### 2.3 Passport — `/api/v1/passport/`

| Method | URL | View | Status | Notes |
|--------|-----|------|--------|-------|
| GET | `/passport/my-passport/` | `MyPassportView` | **Complete** | Returns 404 if no passport yet (correctly handled) |
| PUT | `/passport/my-passport/` | `MyPassportView` | **Complete** | Append-safe merge; recalculates `completeness_score` |
| GET | `/passport/my-passport/share-link/` | `MyPassportShareLinkView` | **Complete** | |
| POST | `/passport/my-passport/regenerate-link/` | `MyPassportRegenerateLinkView` | **URL MISMATCH — BROKEN** | Backend registers at `/passport/my-passport/regenerate-link/`. Frontend calls `/passport/my-passport/share-link/regenerate/`. Hard 404. |
| GET | `/passport/my-candidate/` | `MyCandidateView` | **Complete** | Returns linked candidate for onboarding prefill |
| PATCH | `/passport/my-candidate/` | `MyCandidateView` | **Complete** | Append-safe availability field update |
| GET | `/passport/public/<token>/` | `PublicPassportView` | **Complete** | Logs access, increments `view_count` |
| POST | `/passport/import/` | `PassportImportView` | **Complete** | |
| POST | `/passport/my-passport/revoke-access/` | `MyPassportRevokeAccessView` | **Complete** | |
| POST | `/passport/my-passport/revoke-all/` | `MyPassportRevokeAllView` | **Complete** | |
| POST | `/passport/my-passport/access-log/` | `MyPassportAccessLogView` | **Complete** | |

---

### 2.4 Jobs (Candidate-facing) — `/api/v1/jobs/` and `/api/v1/candidate/`

| Method | URL | View | Status | Notes |
|--------|-----|------|--------|-------|
| GET | `/jobs/search/` | `JobSearchView` | **Complete** | Public (`AllowAny`); filters by `q`, `work_mode`, `location` |
| GET | `/jobs/<uuid>/` | `JobPublicDetailView` | **Complete** | Public job detail |
| POST | `/jobs/<uuid>/apply/` | `JobApplyView` | **Complete** | `IsAuthenticated`; dedup check; creates Application; emits event. Uses `request.user.id` as `candidate_id` — works only when user IS a candidate |
| POST | `/jobs/<uuid>/save/` | `JobSaveView` | **Stub** | Always returns success. Comment: `# TODO: Implement saved jobs with a SavedJob model`. No save logic exists. |
| GET | `/candidate/applications/` | `CandidateApplicationListView` | **Complete** | Scoped to `candidate_id=request.user.id` |
| GET | `/candidate/applications/<uuid>/` | `CandidateApplicationDetailView` | **Complete** | Includes stage history |
| GET | `/candidate/recommended-jobs/` | `RecommendedJobsView` | **Complete** | Uses passport skills to match active postings |

---

### 2.5 Interviews (Candidate-facing) — `/api/v1/candidate/interviews/`

| Method | URL | View | Status | Notes |
|--------|-----|------|--------|-------|
| GET | `/candidate/interviews/` | `CandidateInterviewListView` | **Complete** | Scoped to `candidate_id=request.user.id`; bucketed into upcoming/pending/completed/missed |
| GET | `/candidate/interviews/<uuid>/instructions/` | `CandidateInterviewInstructionsView` | **Complete** | Returns instructions, runtime shell, `secure_runtime_url` |
| GET | `/candidate/interviews/<uuid>/runtime/` | `CandidateInterviewRuntimeView` | **Complete** | Token/session validation; single-attempt enforcement; returns questions |
| GET | `/candidate/interviews/<uuid>/status/` | `CandidateInterviewStatusView` | **Complete** | Returns status, scores, decision |
| POST | `/candidate/interviews/<uuid>/start/` | `CandidateInterviewStartView` | **Complete** | Changes status to `in_progress`; tracks attempts |
| POST | `/candidate/interviews/<uuid>/submit-answer/` | `CandidateSubmitAnswerView` | **Complete** | Saves `answer_text` / `video_url` |
| POST | `/candidate/interviews/<uuid>/complete/` | `CandidateCompleteInterviewView` | **Complete** | |
| POST | `/candidate/interviews/<uuid>/security-event/` | `CandidateInterviewSecurityEventView` | **Complete** | |

---

## 3. Frontend Verification

### 3.1 Auth Pages

| Route | Component | File | Status | API Bound | Notes |
|-------|-----------|------|--------|-----------|-------|
| `/register/candidate` | `RegisterCandidate` | `pages/auth/RegisterCandidate.tsx` | **Partial** | Yes | Calls `authApi.registerCandidate`. Navigates to `/dashboard` after success instead of `/verify-email`. Email verification reached only via `OnboardingGuard` bounce. Phone field collected but ignored by backend serializer. |
| `/verify-email` | `VerifyEmail` | `pages/auth/VerifyEmail.tsx` | **Complete** | Yes | Calls `verifyOTP` + `sendOTP`. Auto-submit on 6 digits. Resend cooldown. Redirects candidate to `/onboarding`, others to `/onboarding/wizard`. |
| `/login` | `Login` | `pages/auth/Login.tsx` | Not audited | — | Route exists in App.tsx |
| `/register/company` | `RegisterCompany` | `pages/auth/RegisterCompany.tsx` | Not audited | — | Route exists |
| `/register/agency` | `RegisterAgency` | `pages/auth/RegisterAgency.tsx` | Not audited | — | Route exists |
| `/forgot-password` | — | — | **Missing** | — | Route does NOT exist in `App.tsx`. `ClaimProfile.tsx` links to this URL — dead link |

---

### 3.2 Candidate Pages

| Route | Component | File | Status | API Bound | Notes |
|-------|-----------|------|--------|-----------|-------|
| `/onboarding` | `Onboarding` | `pages/candidate/Onboarding.tsx` | **Complete** | Yes | 3-step wizard. Prefills from `passportApi.get()` + `passportApi.getLinkedCandidate()`. Step 1: `authApi.updateMe` + `passportApi.update`. Step 2: `passportApi.update` + `passportApi.updateLinkedCandidate` (fire-and-forget). Step 3: `passportApi.update`. Sets sessionStorage flag to prevent guard re-loop. Redirects to `/dashboard`. |
| `/candidate/claim/:token` | `ClaimProfile` | `pages/candidate/ClaimProfile.tsx` | **Complete** | Yes | `getClaimInfo` → `checkIdentity` → login or signup → `doLink(token)`. Handles: already claimed, matching session, login mode, signup mode. Redirects to `/onboarding` after 1.8s. No OTP step after signup — `OnboardingGuard` will bounce to `/verify-email` afterward. |
| `/apply/:token` | `ApplyForm` | `pages/public/ApplyForm.tsx` | **Partial** | Yes | `getPublicForm` on load; `submitPublicForm` on submit. Full form renders. Shows success state. Does NOT check `needs_login: true` in response — returning users see "submitted" instead of a login prompt. |
| `/candidate/jobs` | `JobSearch` | `pages/candidate/JobSearch.tsx` (assumed) | **Partial** | Partial | Fetches jobs from `jobsPublicApi.search`. Fetches applications from `candidateApi.listApplications` to show "Applied" badges. Clicking a job card calls `openQuickView('candidate_job', job)` — this drawer type has no implementation. No Apply button visible anywhere. |
| `/candidate/applications` | `MyApplications` | `pages/candidate/MyApplications.tsx` (assumed) | **Complete** | Yes | Fetches applications + parallel job detail calls. Status stepper rendered. Empty state handled. "View Details" opens `candidate_application` quick-view (content not verified). |
| `/candidate/interviews` | `CandidateInterviewDashboard` | `pages/candidate/CandidateInterviewDashboard.tsx` | **Complete** | Yes | Calls `interviewsApi.candidateList()`. Bucketed rendering. Navigate to instructions and runtime. |
| `/candidate/interviews/:id/instructions` | `CandidateInterviewInstructions` | `pages/candidate/CandidateInterviewInstructions.tsx` | **Complete** | Yes | `candidateInstructions(id)`. Interview detail, security info, Join button. |
| `/candidate/interviews/:id/runtime` | `CandidateInterviewRuntime` | `pages/candidate/CandidateInterviewRuntime.tsx` | **Complete** | Yes | Full runtime: runtime API, start, submit-answer, complete. Security events wired (tab-switch, copy, multi-window). Timer active. Error routing to `/expired` and `/blocked`. |
| `/candidate/interviews/:id/status` | `CandidateInterviewStatus` | `pages/candidate/CandidateInterviewStatus.tsx` | **Complete** | Yes | `candidateStatus(id)`. Shows status, decision, scores. |
| `/candidate/interviews/blocked` | `CandidateInterviewBlocked` | `pages/candidate/CandidateInterviewBlocked.tsx` | **Complete** | No (static) | Anti-cheat block screen, back nav. |
| `/candidate/interviews/expired` | `CandidateInterviewExpired` | `pages/candidate/CandidateInterviewExpired.tsx` | **Complete** (static, not audited in depth) | No | Static expired screen. |
| `/passport` | `PassportPage` | `pages/candidate/Passport.tsx` | **Partial** | Partial | Reads passport data. Share link fetched. "Regenerate" button calls `passportApi.regenerateShareLink()` which maps to `/passport/my-passport/share-link/regenerate/` — backend is at `/passport/my-passport/regenerate-link/`. Hard 404. Resume upload is a URL-only field; file upload marked "coming soon" in UI. |
| `/dashboard` | `Dashboard` | `pages/dashboard/Dashboard.tsx` | Not audited | — | Shared across all roles. No candidate-specific summary page. |

---

### 3.3 Onboarding Pages

| Route | Component | Status | Notes |
|-------|-----------|--------|-------|
| `/onboarding` | `Onboarding.tsx` | **Complete** | Candidate-specific onboarding wizard |
| `/onboarding/wizard` | `OnboardingWizard.tsx` | Not audited | Company/agency onboarding |
| `/company-onboarding` | `CompanyOnboarding.tsx` | Not audited | |
| `/agency-onboarding` | `AgencyOnboarding.tsx` | Not audited | |

---

### 3.4 Guards and Auth State

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| `ProtectedRoute` | `components/common/ProtectedRoute.tsx` | **Complete** | Checks `isAuthenticated` → `/login`; checks `allowedRoles` → `/unauthorized` |
| `OnboardingGuard` | `components/common/OnboardingGuard.tsx` | **Complete** | Candidate: calls `passportApi.get()`, redirects to `/onboarding` if `completeness_score < 40` or 404. Uses `sessionStorage` to prevent infinite redirect loop after onboarding completes. |
| `authStore` | `store/authStore.ts` | **Complete** | Persists tokens to localStorage. Loads user on app bootstrap. Clears all state on 401. `isAuthenticated` derived from token presence. |

---

### 3.5 API Clients

| File | Endpoints Covered | Notes |
|------|------------------|-------|
| `api/auth.ts` | register (all 3), login, logout, refresh, me, otp, verify-email, forgot-password, reset-password, mfa, change-password | All endpoints mapped including the broken forgot/reset stubs |
| `api/candidates.ts` | check-identity, claim, public apply form, invite links | |
| `api/passport.ts` | my-passport GET/PUT, share-link, regenerate (wrong URL), my-candidate GET/PATCH, public view, import, revoke | `regenerateShareLink()` calls wrong URL |
| `api/jobs.ts` | search, apply, save (stub), public detail | `apply()` defined but no frontend UI calls it |
| `api/candidates.ts` (candidate-facing) | `listApplications`, `getApplication`, `recommendedJobs` | |
| `api/interviews.ts` | `candidateList`, `candidateInstructions`, `candidateRuntime`, `candidateStart`, `candidateSubmitAnswer`, `candidateComplete`, `candidateStatus`, `candidateSecurityEvent` | All present |

---

## 4. Flow-by-Flow Verification

### Flow A: Direct Candidate Signup

| Step | Status | Detail |
|------|--------|--------|
| Navigate to `/register/candidate` | **Working** | Page renders |
| Submit registration form | **Working** | `POST /auth/register/candidate/` — dedup, user creation, OTP issued |
| Backend returns JWT | **Working** | Tokens stored in authStore |
| Frontend redirects to `/dashboard` | **Navigation gap** | Should redirect to `/verify-email`. User has `email_verified=false` at this point. |
| `OnboardingGuard` detects unverified, bounces to `/verify-email` | **Working** | Guard catches the gap |
| OTP entry and verification | **Working** | `POST /auth/verify-otp/`, fresh tokens returned |
| Redirect to `/onboarding` | **Working** | `VerifyEmail.tsx` navigates to `/onboarding` for candidate role |
| Onboarding wizard renders with prefill | **Working** | Passport 404 → blank form; linked candidate prefill if record exists |
| 3-step completion | **Working** | Each step calls the correct API |
| Redirect to `/dashboard` | **Working** | sessionStorage flag set to prevent re-loop |
| **Phone field** | **Broken** | `RegisterCandidate.tsx` collects phone; `RegisterCandidateSerializer` does not include it; silently dropped |

---

### Flow B: Claim Account (Company/Agency Added Candidate)

| Step | Status | Detail |
|------|--------|--------|
| Candidate opens `/candidate/claim/<token>` | **Working** | `ClaimProfile.tsx` renders |
| `GET /candidates/claim/<token>/` — token validation + prefill | **Working** | Expiry checked, name/email/phone returned |
| Identity check via `POST /candidates/check-identity/` | **Working** | Determines login vs signup mode |
| Login mode: credentials + `POST /candidates/claim/<token>/` | **Working** | Backend links user to candidate, sets `account_status='claimed'` |
| Signup mode: register + claim | **Working** | New user created, then linked |
| Success → redirect to `/onboarding` | **Working** | 1.8s delay, then navigate |
| OTP verification after signup mode | **Not verified / Gap** | No OTP step in claim flow after signup. `OnboardingGuard` bounces to `/verify-email`. Functional but not explicit in the flow. |

---

### Flow C: Public Apply Link

| Step | Status | Detail |
|------|--------|--------|
| Candidate opens `/apply/<token>` | **Working** | `ApplyForm.tsx` renders |
| `GET /apply/<token>/` — form config loaded | **Working** | `company_name`, `job_title`, form fields returned |
| Form renders with skills/education/work-auth fields | **Working** | Full form renders |
| Submit: `POST /apply/<token>/submit/` | **Working** | Backend dedup, candidate create/merge, optional account creation |
| Backend returns `needs_login: true` for existing users | **Frontend ignores** | `ApplyForm.tsx` does not check this field. Returning user sees success message instead of a login prompt. |
| Success state shown | **Working** | For new candidates |
| `save / return later` | **Missing** | Not implemented frontend or backend |

---

### Flow D: Existing Candidate Login

| Step | Status | Detail |
|------|--------|--------|
| Login with credentials | **Working** | `POST /auth/login/` |
| Backend re-issues OTP if `email_verified=false` | **Working** | Returns 403 with `error_code: 'email_not_verified'` |
| JWT stored, user set | **Working** | |
| Redirect to `/dashboard` | **Working** | |
| `OnboardingGuard` fires: `passportApi.get()` | **Working** | |
| If `completeness_score >= 40` → dashboard loads | **Working** | |
| If `completeness_score < 40` → `/onboarding` | **Working** | |
| Dashboard content for candidate | **Not audited** | Generic dashboard, not candidate-specific |

---

### Flow E: Job Apply Flow

| Step | Status | Detail |
|------|--------|--------|
| Navigate to `/candidate/jobs` | **Working** | Page renders |
| Jobs fetched from `GET /jobs/search/` | **Working** | Results displayed |
| "Applied" badges on previously applied jobs | **Working** | `GET /candidate/applications/` cross-referenced |
| Click a job card | **Broken** | Calls `openQuickView('candidate_job', job)` — drawer type has no implementation. Nothing appears. |
| View job description | **Missing** | No UI surface renders job detail for candidates |
| Apply button | **Missing** | No Apply button exists on any candidate-facing rendered UI. `jobsPublicApi.apply()` is defined but never called. |
| Application visible in `/candidate/applications` | **Working** | IF an application is created via another path (e.g., public apply form), it shows here |

---

### Flow F: Candidate Interview Flow

| Step | Status | Detail |
|------|--------|--------|
| Navigate to `/candidate/interviews` | **Working** | Dashboard renders |
| `GET /candidate/interviews/` | **Working** | Bucketed interviews returned |
| Click "Instructions" | **Working** | Navigates to `/candidate/interviews/:id/instructions?access_token=...` |
| `GET /candidate/interviews/:id/instructions/` | **Working** | Instructions rendered |
| Click "Join Interview" | **Working** | Navigates to runtime with access token |
| Runtime loads and validates token | **Working** | |
| Start interview | **Working** | `POST .../start/` |
| Submit answers | **Working** | `POST .../submit-answer/` per question |
| Complete interview | **Working** | `POST .../complete/` |
| Navigate to status page | **Working** | `/candidate/interviews/:id/status` |
| Status page loads with decision/scores | **Working** | |
| Error routing (expired/blocked) | **Working** | Routes to correct static error pages |

---

## 5. Built Items (Fully Working)

- Candidate registration with identity dedup (`RegisterCandidateView`)
- Email OTP verification (`VerifyEmail.tsx` + `VerifyOTPView`)
- Candidate onboarding wizard — 3 steps, prefill from passport and linked candidate (`Onboarding.tsx`)
- `OnboardingGuard` — completeness check, redirect logic, loop-prevention
- `ProtectedRoute` — auth and role enforcement
- `authStore` — persist, bootstrap, clear on 401
- Claim profile flow — token validation, login+signup modes, linking (`ClaimProfile.tsx` + `CandidateClaimVerifyView`)
- Public apply form — full form, dedup, candidate create/merge, optional account creation (`ApplyForm.tsx` + `PublicApplyFormView`)
- Identity service — `match_candidate`, `match_user`, `link_user_to_candidate`, `check_identity_status`
- Invite link creation and deactivation
- Candidate interview list dashboard — bucketed view
- Interview instructions page
- Interview runtime — start, answer submission, complete, security events, error routing
- Interview status page
- My Applications page — real data, status stepper, empty state
- Job search listing — loads and displays real data, applied badges
- Recommended jobs endpoint
- Passport GET/PUT — append-safe merge, completeness score
- Passport share link generation
- Passport access log, revoke, revoke-all
- My candidate prefill (GET + PATCH) for onboarding
- JWT: login, logout, refresh, change-password, MFA

---

## 6. Partial Items (Exists but Incomplete)

| Item | File / Endpoint | What's Missing |
|------|----------------|----------------|
| `RegisterCandidate.tsx` post-registration redirect | `pages/auth/RegisterCandidate.tsx` | Navigates to `/dashboard` instead of `/verify-email`. Phone field collected but silently ignored. |
| `ApplyForm.tsx` `needs_login` handling | `pages/public/ApplyForm.tsx` | `needs_login: true` returned by backend when a user account exists, but frontend never inspects this field |
| `Passport.tsx` regenerate share link | `pages/candidate/Passport.tsx` + `api/passport.ts` | Frontend calls wrong URL — see Broken section |
| `JobSearch.tsx` job detail / apply | `pages/candidate/JobSearch.tsx` | Job cards render, data loads, applied badges work. But clicking a card opens an unimplemented drawer. No apply button. |
| Candidate onboarding resume step | Step 3 of `Onboarding.tsx` | Resume upload is URL-only. Page explicitly says file upload "coming soon." |
| `ClaimProfile.tsx` — OTP after signup | `pages/candidate/ClaimProfile.tsx` | Claim succeeds after signup without OTP step. Guard bounces user to `/verify-email` afterward — functional but not an explicit flow. |
| Dashboard for candidate | `pages/dashboard/Dashboard.tsx` | Generic dashboard, no candidate-specific summary of profile / applications / upcoming interviews |

---

## 7. Broken Items (Exists but Will Error)

| Item | File / Endpoint | Error Type | Detail |
|------|----------------|------------|--------|
| Passport regenerate share link | `api/passport.ts` → `/passport/my-passport/share-link/regenerate/` | **Hard 404** | Backend is at `/passport/my-passport/regenerate-link/`. Frontend calls wrong URL. |
| Forgot password route | `App.tsx` | **Dead link** | `/forgot-password` is linked from `ClaimProfile.tsx` but the route does not exist in `App.tsx`. Navigation results in 404/blank. |
| `POST /auth/forgot-password/` | `ForgotPasswordView` | **Non-functional stub** | Returns success with no action. No token, no email. |
| `POST /auth/reset-password/` | `ResetPasswordView` | **Non-functional stub** | Always returns `"Password reset successfully."` without validating any token or changing any password. |
| `POST /auth/verify-email/` (legacy) | `VerifyEmailView` | **Security stub** | Accepts any string and returns success unconditionally. |
| `POST /jobs/<uuid>/save/` | `JobSaveView` | **Non-functional stub** | Always returns success. No `SavedJob` model or logic. Explicit `# TODO` comment in backend code. |
| Job apply UI | `pages/candidate/JobSearch.tsx` | **No UI entry point** | `jobsPublicApi.apply()` defined in `api/jobs.ts`; backend `JobApplyView` works; but no frontend button calls it for candidates. |
| `candidate_job` quick-view drawer | Drawer system | **No implementation** | `openQuickView('candidate_job', job)` called on card click; no drawer component handles this type. Clicking opens nothing. |

---

## 8. Missing Items (Expected but Absent)

| Item | Expected Location | Notes |
|------|------------------|-------|
| `/forgot-password` route | `App.tsx` | Linked from ClaimProfile but not defined |
| Job detail view for candidates | `/candidate/jobs` or drawer | No component exists to show job description and apply button to a logged-in candidate |
| Apply button for candidates | `JobSearch.tsx` | Backend ready, API client ready, no UI |
| `needs_login` handling in `ApplyForm` | `pages/public/ApplyForm.tsx` | Backend returns this, frontend ignores it |
| Candidate-specific dashboard | `/dashboard` or `/candidate/dashboard` | No summary page combining profile status, recent applications, upcoming interviews |
| Save/return-later for public apply | `/apply/:token` | Backend has no partial save model; frontend has no save state |
| Phone field in `RegisterCandidateSerializer` | `accounts/serializers.py` | Form collects phone; backend drops it |
| `CompleteOnboardingView` support for candidate role | `accounts/views.py` | `_ROLE_TO_USER_TYPE` map excludes `candidate`. Blocked if candidate ever calls this endpoint. |
| Email delivery for OTP in non-production | `accounts/services.py` | Only logs to stdout unless `ENVIRONMENT=production`. Must be configured for staging. |
| File upload in passport onboarding (Step 3) | `pages/candidate/Onboarding.tsx` | Acknowledged as "coming soon" in the component itself |

---

## 9. Recommended Next Fix Order

Ordered by user-facing impact and dependency:

| Priority | Item | Type | Blocker |
|----------|------|------|---------|
| 1 | **Fix passport regenerate share link URL** | Broken — 1-line fix | `passportApi.regenerateShareLink()` uses wrong URL path |
| 2 | **Add `/forgot-password` route + real forgot/reset password flow** | Missing + Broken | Password recovery is completely non-functional |
| 3 | **Implement candidate job detail drawer + Apply button** | Missing | Candidates cannot apply to jobs from the UI |
| 4 | **Fix `RegisterCandidate.tsx` post-registration redirect** | Partial | Navigate to `/verify-email` after registration, not `/dashboard` |
| 5 | **Handle `needs_login: true` in `ApplyForm.tsx`** | Partial | Returning users see false success; no login prompt shown |
| 6 | **Add phone field to `RegisterCandidateSerializer`** | Partial | Phone collected by form but silently dropped |
| 7 | **Candidate-specific dashboard** | Missing | Generic dashboard provides no value for candidates |
| 8 | **Implement `CompleteOnboardingView` for candidate role** | Broken | Low urgency — candidate onboarding bypasses this endpoint |
| 9 | **Resume file upload in onboarding Step 3** | Partial | Currently URL-only; acknowledged as "coming soon" |
| 10 | **Save/return-later for public apply form** | Missing | Nice-to-have for long forms |

---

*End of report. All findings based on reading actual source files. Items marked "Not audited" were not read during this audit pass.*
