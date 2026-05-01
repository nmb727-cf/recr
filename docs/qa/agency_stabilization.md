# Agency Stabilization QA (AGENCY-STABILIZATION-063A)

## Scope
Stabilization-only backend changes for Agency security and broken workflows.
No UI redesigns. Backward-compatible API additions.

## Security Fixed
1. `AgencyPerformanceListView` no longer honors arbitrary `agency_id` query filtering.
2. Added `AgencyPerformancePermission` to enforce role-based access guard.
3. Response scoping now enforces:
   - company users: only linked agencies,
   - agency users: only own agency performance,
   - platform admins: broader access.

## Endpoints Added
1. Reactivate relationship
- `POST /api/v1/agencies/relationships/{id}/reactivate/`
- alias: `POST /api/v1/agencies/company-agency/{id}/reactivate/`
- exact-format alias: `POST /api/company-agency/{id}/reactivate/`

2. Assign internal recruiter
- `POST /api/v1/agencies/assignments/{id}/assign-recruiter/`
- alias: `POST /api/v1/agencies/agency-jobs/{id}/assign-recruiter/`
- exact-format alias: `POST /api/agency-jobs/{id}/assign-recruiter/`

3. Submission governance
- `POST /api/v1/agencies/agency-jobs/{id}/submission-governance/`
- exact-format alias: `POST /api/agency-jobs/{id}/submission-governance/`

## Behavior Changes
- Reactivate sets relationship status to `active`, writes audit log, emits agency event.
- Assign recruiter validates recruiter belongs to assigned agency, writes assignment, logs audit, emits event.
- Submission governance updates job `agency_submission_governance`, logs audit, emits event.

## Invite Resend Fix
- `GuestPortalResendInviteView` now:
  - regenerates token,
  - sends invite email via `send_agency_invite_email()`,
  - writes audit log.

## Data Model Additions
1. `AgencyMembership`
- fields: `agency_tenant_id`, `user`, `role`, `is_active`, `created_at`
- roles: `admin`, `recruiter`, `sourcer`

2. `AgencyJobAssignment.internal_recruiter_id`
- stores assigned internal recruiter (UUID)

## Test Coverage Added
- `backend/apps/agencies/tests/test_agency_security.py`
  - company cannot access unrelated agency performance,
  - cannot assign recruiter outside agency,
  - cannot reactivate relationship without authorization.

## Impact
- Closes critical data exposure path in agency performance endpoint.
- Restores broken backend contracts used by existing frontend flows.
- Preserves old routes while adding backward-compatible aliases.
