# Agency Module — Phase 1 Verification Report

**Date:** 2026-04-07  
**Auditor:** Claude Code (Senior ATS Architect + QA Auditor)  
**Scope:** Backend models, APIs, services, signals, frontend screens, and business logic  
**Reference baseline:** Phase 1 requirements — Agency Auth & Structure / Agency ERP / Candidate Management / Job Execution / Pipeline & Tracking / Communication

---

## Table of Contents

1. [Implemented](#1-implemented)
2. [Partial](#2-partial)
3. [Missing](#3-missing)
4. [Logic Issues](#4-logic-issues)
5. [Architecture Issues](#5-architecture-issues)
6. [Phase 1 Blockers](#6-phase-1-blockers)

---

## 1. Implemented

### 1.1 Agency Auth & Structure

| Feature | Status | Evidence |
|---------|--------|----------|
| Agency user roles | ✅ | `accounts/models.py`: roles `agency_owner`, `agency_admin`, `agency_recruiter` in CustomUser.role choices |
| Agency registration | ✅ | `RegisterAgency.tsx` → `POST /auth/register-agency`; form with name, email, password |
| Agency onboarding wizard | ✅ | `AgencyOnboarding.tsx` — 4-field setup (name, country, timezone, industry); auto-redirects to `/agencies/my-jobs` on completion |
| RBAC permissions | ✅ | `rbac/registry.py:104` — `agency_recruiter` role fully registered with permission set |
| Role-gated routing | ✅ | App.tsx routes guard `/agencies/my-jobs`, `/agencies/my-submissions` to agency roles; `/agency-intelligence` to admin roles |

### 1.2 Agency ERP — Client Management

| Feature | Status | Evidence |
|---------|--------|----------|
| AgencyClientRelationship model | ✅ | Full model: 50+ fields covering status, tier, SLA, commission, guarantee, retention, payment terms |
| 5 connection types | ✅ | `connection_type` choices: `full_full`, `agency_guest`, `client_guest`, `email_tracking`, `offline` |
| Tenant lookup | ✅ | `GET /agencies/lookup/?q=` — 3-step: full tenant → guest portal → not found with slug suggestion |
| Relationship CRUD | ✅ | `GET/POST /agencies/relationships/`, `GET/PUT/DELETE /agencies/relationships/<pk>/` |
| Invite workflow | ✅ | `POST /agencies/relationships/<pk>/invite/` — sends email via EmailRoutingService |
| Accept workflow | ✅ | `POST /agencies/relationships/<pk>/accept/` — status pending → active |
| Suspend workflow | ✅ | `POST /agencies/relationships/<pk>/suspend/` — status update with optional reason |
| Guest portal creation | ✅ | `POST /agencies/guest-portals/` — generates slug, 7-day invite token, emails via EmailRoutingService, creates AgencyClientRelationship |
| Email tracking clients | ✅ | `POST /agencies/email-tracking/` — auto-extracts domain from email, creates EmailTrackingConfig + relationship |
| Offline clients | ✅ | `POST /agencies/offline-clients/` — creates relationship with connection_type='offline' |
| Guarantee terms | ✅ | Model fields: guarantee_period_days, guarantee_start_type, guarantee_resolution_type, refund_mode, refund_percentage, replacement_attempt_limit |
| Candidate retention rules | ✅ | Model fields: retention_enabled, retention_days, retention_start_type, retention_scope, retention_post_expiry |
| Payment terms | ✅ | payment_terms (JSONField), payment_schedule (JSONField); `PaymentTermsField.tsx` component |
| Company-side agency management UI | ✅ | `CompanyAgencies.tsx` + `AgenciesList.tsx` — both implement relationship management |
| Agency-side client management UI | ✅ | `AgencyClients.tsx` — full relationship creation + editing with guarantee/retention config |
| Quick view panels | ✅ | `AgencyQVPanel`, `AgencyClientQVPanel`, `AgencyJobQVPanel`, `AgencySubmissionQVPanel` |

### 1.3 Job Execution

| Feature | Status | Evidence |
|---------|--------|----------|
| AgencyJobAssignment model | ✅ | Fields: requisition_id, agency_tenant_id, status, deadline, max_submissions, submission_count; unique_together on (tenant_id, requisition_id, agency_tenant_id) |
| Manual job assignment | ✅ | `POST /agencies/assignments/` — with duplicate check; `AgencyAssignmentService.assign_job_to_agency()` |
| Assignment CRUD | ✅ | `GET/PUT/DELETE /agencies/assignments/<pk>/` |
| Intelligent auto-distribution | ✅ | `AgencyIntelligenceService.perform_intelligent_distribution()` — scoring: overall_score (60%) + similar job success (15%) + load balancing (15%) + job coverage (10%) + tier boost |
| Auto-distribute signal | ✅ | `signals.py`: `on_job_published_agency_distribution` fires on `events.job.published`; respects `requisition.auto_distribute_to_agencies` flag |
| Agency-side my-jobs | ✅ | `GET /agencies/my-jobs/` — `AgencyMyJobsView`; `MyJobs.tsx` page |
| Job intelligence endpoint | ✅ | `GET /agencies/jobs/<req_id>/intelligence/` — assignments, recommendations, contributions |
| Job-specific quick/full views | ✅ | `AgencyJobQVPanel.tsx`, `AgencyJobFVPanel.tsx` |

### 1.4 Candidate Management

| Feature | Status | Evidence |
|---------|--------|----------|
| Candidate submission endpoint | ✅ | `POST /agencies/submit-candidate/` — validates assignment, checks limits, deduplicates by global_hash |
| Deduplication | ✅ | `AgencySubmitCandidateView` creates company-side candidate if not exists; merges profile |
| Submission count tracking | ✅ | Increments `AgencyJobAssignment.submission_count` on each submission |
| Submission limit enforcement | ✅ | `max_submissions` check before creating application |
| Application creation | ✅ | Creates `Application` record with `is_agency_submission=True` and `ApplicationStageHistory` |
| Candidate protection | ✅ | `create_or_update_protection_on_submission()` called on each submission |
| Agency my-submissions | ✅ | `GET /agencies/my-submissions/?status=&requisition_id=` |
| CRM pipeline status | ✅ | `candidates/crm_models.py`: `CandidatePipelineStatus` (10 stages), `CandidateInteraction` (6 types); 4 CRM views |
| Submission UI | ✅ | `SubmitCandidate.tsx` page exists; `AgencySubmissionQVPanel.tsx` with status, protection, guarantee watch |

### 1.5 Pipeline & Tracking

| Feature | Status | Evidence |
|---------|--------|----------|
| Application model with agency flag | ✅ | `pipeline/models.py`: `Application.is_agency_submission = BooleanField(default=False)` |
| Placement model | ✅ | `pipeline/models.py`: `Placement` model (line 178) |
| PlacementGuarantee model | ✅ | `pipeline/models.py`: `PlacementGuarantee` model (line 137) |
| CommissionRecord model | ✅ | `pipeline/models.py`: `CommissionRecord` model (line 227) |
| Placement CRUD views | ✅ | `pipeline/commercial_views.py`: PlacementListView, PlacementDetailView, PlacementConfirmView |
| Commission management | ✅ | CommissionDetailView (GET/PUT), CommissionPaymentStatusView (POST), CommissionReminderListView (GET/POST) |
| Guarantee lifecycle | ✅ | `pipeline/guarantee.py`: start_guarantee_for_joined_placement(), expire_due_placement_guarantees(), mark_guarantee_breached() |
| Agency performance scoring | ✅ | `AgencyPerformanceScore` model; `refresh_agency_performance_scores()` with full metric calculation |
| Performance score refresh signals | ✅ | `signals.py`: fires on `agency.candidate_submitted` and `application.stage_changed` (agency submissions only) |
| Performance dashboard UI | ✅ | `AgencyIntelligenceDashboard.tsx` — overview, performance table, distribution, risk detection, comparison |
| Agency submission governance field | ✅ | `jobs/models.py`: `agency_submission_governance` CharField on JobRequisition |

### 1.6 Communication

| Feature | Status | Evidence |
|---------|--------|----------|
| Invite emails | ✅ | `AgencyRelationshipInviteView` and `GuestPortalCreateView` both call `EmailRoutingService` |
| Agency-event notification handlers | ✅ | `communications/event_handlers.py` includes `on_message_created`, `on_message_high_priority`, `on_offer_accepted` |
| Fallback + escalation pipeline | ✅ | Full orchestration layer (COMMS-NOTIFY-AUTOMATION-01) covers agency-triggered events |

---

## 2. Partial

### 2.1 Agency ERP — Recruiter Management

**Status: PARTIAL — Roles exist, management API does not.**

- ✅ Three agency roles defined: `agency_owner`, `agency_admin`, `agency_recruiter`
- ✅ Roles gated in RBAC registry with appropriate permission sets
- ✅ `accounts/views.py:603` maps `agency_recruiter` role → `agency` tenant type on registration
- ❌ No `GET /agencies/team/` endpoint to list agency team members
- ❌ No `POST /agencies/team/invite/` to invite a recruiter to the agency
- ❌ No `DELETE /agencies/team/<user_id>/` to remove a team member
- ❌ No internal recruiter assignment per job assignment (frontend calls `POST /agencies/assignments/<id>/assign-recruiter/` — **this endpoint does not exist in urls.py**)

Agency users share the same `tenant_id` but there is no explicit model linking team members to a specific agency account. All user lookup is by querying `CustomUser.objects.filter(tenant_id=..., role=...)`.

### 2.2 Guest Portal Resend Invite

**Status: PARTIAL — Token reset works, email is never sent.**

- ✅ `POST /agencies/guest-portals/<pk>/resend/` resets invite_token and invite_expires_at
- ❌ **TODO at `views.py:1290`** — "Send invite email again" comment with no implementation
- The `GuestPortalCreateView` correctly calls `EmailRoutingService`; `GuestPortalResendInviteView` does not

### 2.3 Relationship Reactivation

**Status: PARTIAL — Suspend works; reactivate does not exist on backend.**

- ✅ `POST /agencies/relationships/<pk>/suspend/` implemented
- ❌ Frontend `agenciesApi.reactivateRelationship(id)` calls `POST /agencies/relationships/<id>/reactivate/`
- ❌ **This route is not registered in `agencies/urls.py`** — the call will 404
- `AgencyRelationshipDetailView.put()` can be used as a workaround, but no dedicated reactivate view or validation exists

### 2.4 Submission Governance Workflow

**Status: PARTIAL — Field exists, enforcement endpoint missing.**

- ✅ `JobRequisition.agency_submission_governance` CharField on jobs model
- ✅ `Application.is_agency_submission` flag on pipeline model
- ❌ Frontend calls `agenciesApi.updateSubmissionGovernance(submissionId, status, note)` → `POST /agencies/submissions/<id>/governance/`
- ❌ **This endpoint does not exist in `agencies/urls.py` or any other urls.py**
- No service method exists to enforce governance decisions (approve/reject submission)

### 2.5 Agency Intelligence Dashboard — Filtering

**Status: PARTIAL — Data is complete, UX is limited.**

- ✅ Full metrics calculation in `AgencyIntelligenceService.build_dashboard()`
- ✅ Risk detection, load balancing, comparison data all returned
- ❌ No date range filters in `AgencyIntelligenceDashboardView`
- ❌ No agency-specific filter in the dashboard endpoint
- ❌ No export functionality in UI
- ❌ No time-series trend data

### 2.6 Document Management

**Status: PARTIAL — Fields modelled, no upload API.**

- ✅ `AgencyClientRelationship.contract_file_url` (TextField)
- ✅ `AgencyClientRelationship.recruitment_policy_url` (TextField)
- ❌ No file upload endpoint in agencies or documents module
- ❌ No upload UI in `CompanyAgencies.tsx` or `AgencyClients.tsx` — fields are invisible to users

### 2.7 Agency Dashboard (Frontend)

**Status: PARTIAL — Component built but not routed.**

- ✅ `AgencyDashboard.tsx` exists with stat cards, recent submissions, active assignments
- ❌ `/agency/dashboard` (or any path) is **not registered** in `App.tsx`
- The component makes live API calls but is unreachable via navigation

---

## 3. Missing

### 3.1 Agency Team Management API

No endpoints exist for agency-side team operations:

| Missing Endpoint | Required For |
|-----------------|--------------|
| `GET /agencies/team/` | List agency recruiters |
| `POST /agencies/team/invite/` | Add recruiter to agency |
| `DELETE /agencies/team/<user_id>/` | Remove recruiter |
| `PUT /agencies/team/<user_id>/role/` | Change recruiter role (recruiter → admin) |

Frontend `AgencyJobQuickView.tsx` attempts to load team members via an undocumented `/agencies/team/` call. Without this endpoint, internal recruiter assignment is broken end-to-end.

### 3.2 Internal Recruiter Assignment on Job

| Missing Endpoint | Called By |
|-----------------|-----------|
| `POST /agencies/assignments/<id>/assign-recruiter/` | `agenciesApi.assignInternalRecruiter()` in `AgencyJobQVPanel.tsx` |

No view, service method, or URL pattern exists for this. The `AgencyJobAssignment` model has no `internal_recruiter_id` field to store the assignment.

### 3.3 Relationship Reactivation Endpoint

| Missing Endpoint | Called By |
|-----------------|-----------|
| `POST /agencies/relationships/<id>/reactivate/` | `agenciesApi.reactivateRelationship()` in `CompanyAgencies.tsx` |

Once a relationship is suspended, there is no path back to active through the API.

### 3.4 Submission Governance Endpoint

| Missing Endpoint | Called By |
|-----------------|-----------|
| `POST /agencies/submissions/<id>/governance/` | `agenciesApi.updateSubmissionGovernance()` |

The `agency_submission_governance` field on `JobRequisition` sets the policy (e.g., requires_approval) but there is no mechanism to action a submission through an approval workflow.

### 3.5 Guarantee Claims & Refund Workflow UI

`pipeline/guarantee.py` implements `mark_guarantee_breached()` and `expire_due_placement_guarantees()` on the backend. However:
- No UI exists to initiate a guarantee claim
- No UI exists to track refund status
- `PlacementGuarantee` model records are not surfaced in any agency-side screen

### 3.6 Agency Performance Trends (Time-Series)

- No historical performance data endpoint
- `AgencyPerformanceScore` stores period_start/period_end but the API returns only the latest snapshot
- No GET endpoint to retrieve historical scores for an agency across time periods

---

## 4. Logic Issues

### 4.1 `perform_intelligent_distribution` — No Limit on Selected Agencies

`AgencyIntelligenceService.perform_intelligent_distribution()` assigns a job to multiple agencies based on scoring. There is no configurable cap on how many agencies are selected per job. All agencies above a threshold score receive the assignment. This can lead to excessive parallel assignments when an agency pool is large.

**Risk:** High — May create SLA tracking and commission tracking complexity at scale.

### 4.2 Submission Count Not Decremented on Application Withdrawal

`AgencySubmitCandidateView` increments `AgencyJobAssignment.submission_count` on each submission. There is no signal or service method to decrement this counter if an application is later withdrawn or deleted. Over time, the count diverges from actual active submissions, causing max_submissions limits to be enforced against stale data.

**Risk:** Medium — Agencies hit submission limits incorrectly after application withdrawals.

### 4.3 `GuestPortalResendInviteView` — Token Reset Without Email (Bug)

`GuestPortalResendInviteView.post()` resets the invite token and expiry date but has a `# TODO: Send invite email again` comment (line 1290 of views.py) with no implementation. The external party receives no notification that a new invite was issued.

**Risk:** High — Feature is broken. Resend button in UI does nothing visible to recipient.

### 4.4 Agency-Company Relationship Scoping in `AgencyRelationshipListView`

The GET handler filters relationships by checking both `agency_tenant_id` and `company_tenant_id` against `request.user.tenant_id`. An agency user with the same `tenant_id` as a company would see both sides of all relationships. In a shared-schema multi-tenant system, this relies entirely on `tenant_id` being unique per account type, which is not enforced at the database level.

**Risk:** Low — Practically safe, but lacks an explicit `is_agency` / `is_company` discriminator on the tenant record.

### 4.5 `AgencyPerformanceListView` — Unauthenticated Score Exposure

`AgencyPerformanceListView` allows `agency_recruiter` role access (via `include_recruiter=True`). An agency recruiter can query `GET /agencies/performance/?agency_id=<any_uuid>` and receive competitor performance data if they guess a valid agency UUID. There is no scope check that the queried `agency_id` belongs to the requesting user's tenant.

**Risk:** Medium — Performance scores (shortlist rate, hire rate, overall score) are commercially sensitive.

### 4.6 `auto_distribute_to_agencies` — No Re-distribution Guard

`on_job_published_agency_distribution` runs every time `events.job.published` fires. If a job is unpublished and republished, the signal re-runs `perform_intelligent_distribution()`. Because `assign_job_to_agency` uses `get_or_create`, existing assignments are not duplicated — but scores are recalculated and new assignments may be added without notifying agencies already holding existing ones.

**Risk:** Low — Idempotent for existing assignments; new agencies may be added silently.

---

## 5. Architecture Issues

### 5.1 No Dedicated Agency Team Member Model

Agency users are `CustomUser` records sharing the same `tenant_id` and distinguished only by `role`. There is no `AgencyTeamMember` or `AgencyMembership` model. Consequences:

- Cannot associate a recruiter with a specific job assignment (`AgencyJobAssignment` has no `assigned_recruiter_id` field)
- Cannot restrict an agency recruiter's view to only their assigned jobs
- Cannot track per-recruiter submission history within an agency
- The frontend's `assignInternalRecruiter` API call has no data model to write to

### 5.2 Duplicate Company-Side Agency Management UI

Both `CompanyAgencies.tsx` and `AgenciesList.tsx` implement company-side agency relationship management with different UX and API call patterns. This creates:

- Inconsistent behavior (e.g., one handles guarantee terms, the other does not)
- Dual maintenance burden
- No single source of truth for the company-side experience

One should be deprecated. `CompanyAgencies.tsx` is more complete (handles all connection types, guarantee config, retention rules).

### 5.3 Frontend API Calls to Undeclared Endpoints

The frontend `api/agencies.ts` defines two API methods that call endpoints with no backend implementation:

| Frontend Method | Backend URL | Status |
|----------------|-------------|--------|
| `assignInternalRecruiter(id, recruiterId)` | `POST /agencies/assignments/<id>/assign-recruiter/` | 404 |
| `updateSubmissionGovernance(id, status, note)` | `POST /agencies/submissions/<id>/governance/` | 404 |

These will silently fail in production. No error handling in the UI surfaces these as broken features.

### 5.4 `AgencyJobAssignment` Missing `internal_recruiter_id` Field

The assignment model has no field for tracking which internal agency recruiter is working a job. This is a model-level gap blocking the recruiter assignment feature (Section 3.2).

### 5.5 `PlacementGuarantee` Lifecycle Not Connected to Agency UI

The guarantee model and helper functions exist in `pipeline/guarantee.py` but are completely disconnected from agency-facing screens:
- `start_guarantee_for_joined_placement()` is likely called from a placement confirm flow
- No agency screen shows active guarantees, their status, or breach notifications
- No signal connects placement guarantee state to `AgencyClientRelationship.guarantee_*` configuration fields

---

## 6. Phase 1 Blockers

These are features that must be present for Phase 1 to be functionally complete. Each represents a gap where a user cannot complete a core workflow.

| # | Blocker | Severity | Impact |
|---|---------|----------|--------|
| B-1 | **Relationship Reactivation endpoint missing** — Suspended relationships cannot be reactivated via API. The `reactivateRelationship()` frontend call returns 404. | HIGH | Company cannot restore a suspended agency partnership without a DB update |
| B-2 | **GuestPortalResendInviteView sends no email** — Token is reset but recipient is never notified. Guest portal invite resend is non-functional. | HIGH | External agencies/clients with expired invites are permanently locked out without backend intervention |
| B-3 | **Agency team management API absent** — Cannot list, invite, or remove agency recruiters. `AgencyJobQuickView` fails to load team for internal assignment. | HIGH | Agency admins cannot manage their team; recruiter assignment flow is broken |
| B-4 | **Internal recruiter assignment endpoint missing** — `POST /agencies/assignments/<id>/assign-recruiter/` returns 404. | MEDIUM | Agencies cannot assign specific recruiters to jobs through the UI |
| B-5 | **Submission governance endpoint missing** — `POST /agencies/submissions/<id>/governance/` returns 404. Companies with `agency_submission_governance` requiring approval have no way to action submissions. | MEDIUM | Governance policy is configured but unenforced; any agency submission bypasses review |
| B-6 | **`AgencyDashboard.tsx` not routed** — Agency users have no dashboard landing page. Navigation dead-ends after onboarding. | MEDIUM | Agency users see no overview screen; they must know exact URLs for each feature |

---

## Summary Matrix

| Phase 1 Area | Models | APIs | Services | UI | Business Logic |
|---|---|---|---|---|---|
| Agency Auth & Structure | ✅ | ✅ | ✅ | ✅ | ✅ |
| Agency ERP — Client Management | ✅ | ✅ (−reactivate) | ✅ | ✅ (−doc upload) | ⚠️ (governance gap) |
| Agency ERP — Recruiter Management | ❌ (no team model) | ❌ (no team APIs) | ❌ | ⚠️ (UI calls missing APIs) | ❌ |
| Candidate Management | ✅ | ✅ (−governance) | ✅ | ✅ | ⚠️ (count not decremented) |
| Job Execution | ✅ | ✅ | ✅ | ✅ | ⚠️ (no agency cap) |
| Pipeline & Tracking | ✅ | ✅ | ✅ | ⚠️ (guarantee UI missing) | ✅ |
| Communication | ✅ | ✅ | ✅ | N/A | ⚠️ (resend broken) |

**Overall Phase 1 Readiness: 6 blockers, 5 partial areas, 2 logic risks requiring immediate attention.**
