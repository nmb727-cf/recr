# V1 Audit: Auth + Signup + Onboarding

## Scope
This audit covers V1 auth, signup, OTP/email verification, onboarding (candidate + company/agency wizard), tenant/workspace bootstrap, and related route guards.

---

## 1) Folder/File Structure (Exact Files + Responsibility)

### Backend (auth module core)
- `backend/apps/accounts/urls.py`
  - Auth/signup/onboarding endpoint registry.
- `backend/apps/accounts/views.py`
  - API behavior for registration, OTP, onboarding completion, login/session, profile endpoints.
- `backend/apps/accounts/serializers.py`
  - Request validation rules and API-level schema constraints.
- `backend/apps/accounts/models.py`
  - `CustomUser` and `EmailOTP` persistence model.
- `backend/apps/accounts/tests/test_onboarding.py`
  - Onboarding completion behavior tests (success and tenant-missing guard).
- `backend/apps/core/responses.py`
  - Unified API response envelope (`success`, `data`, `message`, optional `errors`).
- `backend/apps/tenants/models.py`
  - Tenant entities (`Client`, `Domain`) used during signup tenant creation.
- `backend/apps/organisations/models.py`
  - Organisation record model used during company/agency signup and onboarding metadata persistence.
- `backend/apps/core/events.py`
  - Event signal definitions including `events.onboarding.completed`.
- `backend/apps/communications/email_events/consumers.py`
  - Onboarding completion email consumer and event-driven email dispatch.
- `backend/config/urls.py`
  - Prefix mapping exposing accounts URLs under both `/api/v1/auth/` and `/api/v1/accounts/`.

### Frontend (auth/onboarding UX core)
- `frontend/src/App.tsx`
  - Public auth routes, onboarding routes, and protected route wrappers.
- `frontend/src/store/authStore.ts`
  - Auth state persistence (tokens/user), login/logout/fetchMe behaviors, pending verification email state.
- `frontend/src/hooks/useAuth.ts`
  - Hook facade over auth store state/actions.
- `frontend/src/api/auth.ts`
  - Frontend API contracts for auth endpoints and onboarding completion.
- `frontend/src/pages/auth/Login.tsx`
  - Login form, error branching (`email_not_verified`), post-login route resolution.
- `frontend/src/pages/auth/RegisterCompany.tsx`
  - Company signup form, client-side validation, verify-email redirect.
- `frontend/src/pages/auth/RegisterAgency.tsx`
  - Agency signup form, local agency prefill caching, verify-email redirect.
- `frontend/src/pages/auth/RegisterCandidate.tsx`
  - Candidate signup form and direct dashboard redirect (not verify-email flow).
- `frontend/src/pages/auth/VerifyEmail.tsx`
  - OTP input UX, resend cooldown, verification flow, role-based post-verify redirect.
- `frontend/src/components/common/OnboardingGuard.tsx`
  - Runtime gate that forces email verification + onboarding completion before app access.
- `frontend/src/pages/onboarding/OnboardingWizard.tsx`
  - Company/agency onboarding wizard; submits preference payload and optional email-provider connect handoff.
- `frontend/src/pages/candidate/Onboarding.tsx`
  - Multi-step candidate profile onboarding with merge/prefill logic and step-local save behavior.
- `frontend/src/pages/onboarding/CompanyOnboarding.tsx`
  - Organisation setup/edit flow for company roles.
- `frontend/src/pages/onboarding/AgencyOnboarding.tsx`
  - Organisation setup/edit flow for agency roles.
- `frontend/src/utils/companyOnboarding.ts`
  - LocalStorage prefill cache utilities and setup-incomplete heuristic.

---

## 2) API Audit

### Route exposure and endpoint families
- Prefixes:
  - `/api/v1/auth/*`
  - `/api/v1/accounts/*`
- Both prefixes mount the same `accounts/urls.py`; behavior duplicates by alias.

### Auth + signup endpoints (observed)
- `POST /register/company/`
- `POST /register/agency/`
- `POST /register/candidate/`
- `POST /login/`
- `POST /refresh/`
- `POST /send-otp/`
- `POST /verify-otp/`
- `POST /verify-email/` (legacy, token-only placeholder)
- `POST /onboarding/complete/`
- `POST /logout/`
- `GET /me/`
- `PUT /me/`
- `POST /change-password/`

### Request payloads (effective)
- Company/Agency register:
  - `name`, `first_name`, `last_name`, `email`, `password`, `password_confirm`, optional `country_code`, `timezone`.
- Candidate register:
  - Backend serializer expects `first_name`, `last_name`, `email`, `password`, `password_confirm`.
  - Frontend sends extra `phone`, `timezone`; backend ignores because serializer does not include those fields.
- Login:
  - `email`, `password` (optional `tenant_slug` accepted but not used in login logic).
- OTP send:
  - `email`.
- OTP verify:
  - `email`, `code`.
- Onboarding complete:
  - `hiring_style`, `team_size`, `automation_preference`, optional `user_type` (server derives from role if absent).

### Response payloads (effective)
- Envelope pattern:
  - Success: `{ success: true, data, message, meta? }`
  - Error: `{ success: false, data: null, message, errors? }`
- Register/login/verify-otp success:
  - `data.user`, `data.access_token`, `data.refresh_token`.
  - Dev mode may include `otp_code`, `is_development_mode`.
- Candidate register duplicate identity case:
  - Returns `200` success with `data.needs_login=true` instead of hard error.

### Validation behavior
- Password:
  - Min length + Django validators + custom “must contain at least one letter”.
- Password confirmation:
  - Enforced server-side for all signup serializers.
- Email uniqueness:
  - Server-side check in signup serializers.
- Onboarding enums:
  - `hiring_style`, `team_size`, `automation_preference` constrained by serializer choices.

### Error handling patterns
- Most serializer failures map to `Validation failed` + field error map.
- Login invalid credentials -> `401`.
- Inactive or unverified email -> `403`.
- OTP wrong/expired/attempt-exceeded has explicit messages.
- Send OTP for unknown email intentionally returns success-style generic message (anti-enumeration).

### Auth/session behavior
- JWT via SimpleJWT (`access_token`, `refresh_token`).
- Login and verification both mint fresh token pairs.
- Logout blacklists refresh token when possible.
- Frontend stores tokens in both Zustand persist and direct `localStorage` keys.

---

## 3) Business Logic Audit

### Signup flow
- Company/Agency:
  1. Validate payload.
  2. Create tenant (`Client`) + local domain (`<slug>.localhost`).
  3. Create tenant admin user (`tenant_admin`) or agency owner (`agency_owner`).
  4. Create `Organisation` record.
  5. Issue OTP, issue JWT tokens, return user session immediately (pre-verification).
- Candidate:
  1. Validate payload.
  2. Identity dedupe via `match_user(email, phone)`.
  3. If existing account: return `needs_login` response.
  4. Else create candidate user in `public` tenant.
  5. Resolve/link candidate identity record.
  6. Issue OTP + tokens.

### Login flow
- Authenticate by email/password.
- Blocks inactive users.
- Blocks unverified users and re-issues OTP.
- Updates last login timestamp/IP and returns JWT/user.

### Tenant/workspace creation
- Slug/schema derived from company/agency name, uniqueness loop with numeric suffix.
- Domain fixed to localhost form at tenant creation.
- Organisation created with minimal seed data.

### User role setup defaults
- Company signup role: `tenant_admin`.
- Agency signup role: `agency_owner`.
- Candidate signup role: `candidate`.

### Onboarding flow
- Company/Agency wizard sends hiring preference triplet.
- Server derives `user_type` from role mapping; rejects unsupported role or missing tenant.
- Persists onboarding data in `user.metadata.onboarding` + `Organisation.metadata.onboarding` and `onboarding_completed`.
- Calls `_auto_configure` to create default automation rules depending on preference.
- Emits onboarding-completed signal using `send_robust`; receiver failures logged but do not fail request.

### Redirect/default behavior
- Company/agency signup -> `/verify-email`.
- Candidate signup -> `/dashboard` (not `/verify-email`) while still possibly unverified.
- Verify email success:
  - Candidate -> `/onboarding`
  - Non-candidate -> `/onboarding/wizard`
- Guarded app pages enforce onboarding completion and can redirect into onboarding routes.

---

## 4) UI/UX Audit

### Screens and key forms
- Login: email, password, forgot-password link, three signup CTAs.
- Register company/agency: first/last name, org name, email, password + confirm.
- Register candidate: first/last, email, timezone, password + confirm (phone optional).
- Verify email: 6-cell OTP UI, resend with cooldown, dev autofill behavior.
- Onboarding wizard (company/agency): welcome + 3 preference steps + optional email connect step.
- Candidate onboarding: 3-step profile enrichment with prefills from passport/candidate/user.

### Validation and state behavior
- Strong client validation for password complexity (uppercase/lowercase/number).
- Field-level errors collapsed into single alert line on register forms.
- VerifyEmail auto-submits when OTP digits complete.
- Candidate onboarding preserves step on failure and shows flattened backend field errors.

### Layout behavior
- Auth pages share `AuthLayout`.
- Candidate/company/agency onboarding can run outside main app shell (`OnboardingLayout` or full-screen wizard).

### What works better than V2 (based on V1 evidence)
- Explicit anti-enumeration behavior in OTP send.
- Role-driven onboarding branching is practical and deterministic.
- Candidate onboarding prefill merge strategy is deep and user-friendly.
- Onboarding signal failures are isolated via `send_robust` to avoid user-facing breakage.

---

## 5) Security Audit

### Positive controls
- Password policy uses Django validators + custom numeric-only guard.
- Unknown-email OTP requests return neutral message (enumeration resistance).
- OTP attempts, expiry, cooldown present.
- Protected endpoints use `IsAuthenticated`.

### Risks/unsafe logic
- Dev OTP bypass (`123456`) is accepted when `DEBUG` or development environment is set; also exposed in frontend UX. Risk if env config leaks into non-dev.
- Register endpoints return active JWT before email verification. App guard and login checks mitigate, but token issuance pre-verify is still elevated risk.
- Token storage in `localStorage` increases XSS blast radius.
- `RegisterCandidateSerializer` omits `phone`/`timezone` while view/frontend still use/send them: schema drift risk and potentially inconsistent dedupe quality.
- `authApi.refreshToken` sends `{refresh}` while backend serializer expects `{refresh_token}` (contract mismatch risk).
- `authApi.changePassword` sends `{old_password,new_password}` while backend expects `{current_password,new_password}`.
- Frontend allows candidate register success path to `/dashboard` before verification; relies on guard redirect, creating a transient inconsistent state.

### RBAC and tenant isolation observations
- Role gating enforced mostly in frontend routing and onboarding guard.
- Backend onboarding role mapping includes known tenant/agency roles and rejects unsupported roles.
- Candidate signup deliberately allows cross-tenant identity resolution path in service call (`allow_cross_tenant=True`) which needs strong service-level safeguards (not fully verifiable in this audit scope).

### Hardcoded values
- Tenant domain hardcoded to `.localhost` at creation.
- Defaults hardcoded (`country_code='IN'`, `timezone='UTC'`, dev OTP `123456`).

---

## 6) Data Model Audit

### Core tables/models used
- `accounts_user` (`CustomUser`): identity, role, tenant binding, verification flags, metadata.
- `accounts_email_otp` (`EmailOTP`): OTP code, expiry, attempts, used/verified flags.
- `Client` (tenant model): tenant schema/slug/type/status and region metadata.
- `Domain`: tenant domain mapping.
- `organisations_organisation`: org profile and onboarding metadata.

### Key relationships (logical)
- User -> Tenant via `tenant_id` UUID (not FK).
- Organisation -> Tenant via `tenant_id` UUID (not FK).
- OTP -> Email string (not user FK).

### Risks
- Widespread UUID linkage without FK constraints increases orphan/integrity risk.
- OTP bound to email string only; if email ownership shifts, historical OTP rows are detached from user lifecycle.
- Metadata-heavy onboarding persistence in JSON fields reduces schema rigidity and query ergonomics.

---

## 7) Workflow Audit

### State transitions
- Signup => user+tenant/org creation (for company/agency) => OTP issued => user has tokens but unverified.
- OTP verify success => user `email_verified=true` and tokens reissued.
- Onboarding complete => user/org metadata updated, automation rules potentially created, onboarding event emitted.

### Events
- `events.company.created` fired on company signup.
- `events.onboarding.completed.send_robust` fired on onboarding completion.
- Email consumer listens and queues “Welcome to TalentOS” notification.

### Onboarding completion logic
- Requires authenticated user + tenant + supported role.
- Role determines `user_type`; frontend does not submit that field.
- Completion does not fail when event receiver errors occur.

### Failure handling
- Serializer errors return structured field maps.
- Candidate onboarding uses step-local failure handling and no forced progression.
- Onboarding signal failures are logged only (non-blocking).

---

## 8) Strengths
- Clear role-specific signup and onboarding split (company/agency/candidate).
- Good practical anti-enumeration behavior for OTP send.
- Candidate prefill + merge logic is sophisticated and conversion-friendly.
- Onboarding completion flow is resilient to downstream async/email infra failures.
- Consistent API envelope simplifies frontend error handling.

---

## 9) Weaknesses
- Contract drift between frontend API client and backend serializers (`refresh`, `change-password`, candidate payload mismatch).
- Dev-mode OTP logic and UI affordance are tightly embedded; risky if environment boundaries blur.
- Token issuance before email verification broadens session attack surface.
- Some critical auth/session decisions rely on frontend redirect guard behavior, not purely backend authorization gates.
- Tenant and organisation linkage via UUID fields without DB-level FK constraints complicates integrity/scalability.
- Onboarding/business state spread across JSON metadata in multiple entities can drift without strict versioning.

---

## 10) V2 Upgrade Recommendations (Conceptual Only)

### Logic to preserve/inspire
- Role-derived onboarding branching (avoid asking user redundant questions).
- Non-blocking event dispatch on onboarding completion.
- Candidate prefill merge hierarchy and step-local error resilience.
- OTP enumeration-safe messaging.

### Must not be copied as-is
- Dev OTP bypass pattern (`123456`) and frontend auto-prefill of that code.
- Frontend-backend contract mismatches and silent extra payload fields.
- Pre-verification full session issuance without stronger scope constraints.
- Heavy reliance on localStorage token persistence without hardened XSS posture.

### Must be redesigned
- Auth contracts as typed single source of truth (shared schema/OpenAPI-generated clients).
- Verification/session model (pre-verify token scope or staged token type).
- Data integrity: migrate UUID references to explicit FKs where feasible.
- Onboarding state model with explicit versioned schema (instead of scattered JSON blobs).
- Tenant domain/bootstrap strategy (remove localhost assumptions).

---

## Top Findings (Priority)
1. **API contract drift exists in production paths** (`refresh`, `change-password`, candidate register payload shape mismatch), risking broken flows and hidden bugs.
2. **Dev OTP bypass is deeply integrated** (backend + UI), which is operationally risky if environment config is mismanaged.
3. **Session tokens are issued before email verification**, requiring strict downstream controls to avoid privilege leakage.
4. **Onboarding logic is strong but metadata-centric**, making long-term consistency and analytics harder.
5. **Candidate onboarding UX/merge logic is a standout strength** and should be preserved conceptually.

## Exact Files Reviewed
- `backend/apps/accounts/urls.py`
- `backend/apps/accounts/views.py`
- `backend/apps/accounts/serializers.py`
- `backend/apps/accounts/models.py`
- `backend/apps/accounts/tests/test_onboarding.py`
- `backend/apps/accounts/services.py` (context check)
- `backend/apps/core/responses.py`
- `backend/apps/core/events.py`
- `backend/apps/communications/email_events/consumers.py`
- `backend/apps/tenants/models.py`
- `backend/apps/organisations/models.py`
- `backend/config/urls.py`
- `frontend/src/App.tsx`
- `frontend/src/api/auth.ts`
- `frontend/src/store/authStore.ts`
- `frontend/src/hooks/useAuth.ts`
- `frontend/src/components/common/OnboardingGuard.tsx`
- `frontend/src/pages/auth/Login.tsx`
- `frontend/src/pages/auth/RegisterCompany.tsx`
- `frontend/src/pages/auth/RegisterAgency.tsx`
- `frontend/src/pages/auth/RegisterCandidate.tsx`
- `frontend/src/pages/auth/VerifyEmail.tsx`
- `frontend/src/pages/onboarding/OnboardingWizard.tsx`
- `frontend/src/pages/onboarding/CompanyOnboarding.tsx`
- `frontend/src/pages/onboarding/AgencyOnboarding.tsx`
- `frontend/src/pages/candidate/Onboarding.tsx`
- `frontend/src/utils/companyOnboarding.ts`

## Missing Information
- Candidate identity-service internals (`match_user`, `resolve_candidate_identity`) were not fully audited in this module pass, so cross-tenant dedupe safety is partially inferred.
- No runtime config audit of environment separation (dev vs staging/prod) was included; therefore OTP bypass deployment risk is assessed from code only.
- No DB migration history was inspected; integrity and schema-evolution risks are based on current models.

## Risks Summary
- High: auth contract drift, environment-sensitive OTP bypass.
- Medium: pre-verification token issuance, localStorage token exposure, metadata drift.
- Medium: referential integrity gaps due to UUID-without-FK patterns.

## Recommended Next Audit Module
- **Candidate Identity + Passport + Claim Flow** (`/candidate/claim`, passport APIs, identity resolution service), because it directly intersects signup dedupe, onboarding prefill correctness, and tenant isolation risk.
