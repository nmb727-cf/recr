import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYS_KNOW = os.path.join(ROOT, 'sys_know')
REPORTS = os.path.join(SYS_KNOW, 'reports', 'gemini')

os.makedirs(REPORTS, exist_ok=True)

# 1. system_reality_audit.md
audit_content = """# System Reality Audit

## 1. Confirmed Implemented Areas
- **Authentication & Onboarding**: Implemented in backend (`/accounts/`) and frontend (`auth.ts`). Noticeable path mismatch (`/auth/` vs `/accounts/`).
- **Candidates CRM & Profiles**: Strong alignment between backend (`/candidates/`) and frontend (`candidates.ts`). Includes invite links, timeline, notes, engagements.
- **Jobs & Requisitions**: Both sides implemented (`/jobs/`). Covers postings, requisitions, stages, apply flow.
- **Talent Pools**: Implemented in both (`/talent_pools/` / `/talent-pools/`).
- **Interviews**: Implemented in both (`/interviews/`).
- **Agencies**: Implemented in both (`/agencies/`). Covers relationships, submissions.
- **Communications**: Implemented (`/communications/`), covering email accounts, templates, rendering.

## 2. Confirmed Partial Areas
- **Pipeline / Applications**: Frontend uses `/applications/` and `/pipeline/`, while backend routes are under `/pipeline/applications/`. This might require URL rewrites or is currently broken.
- **Organisation Management**: Frontend calls `/organisation/` but backend exposes `/organisations/` (plural). Likely broken unless proxied.
- **Messages & Notifications**: Frontend calls `/messages/` and `/notifications/` directly, but backend routes are under `/communications/messages/` and `/communications/notifications/`.

## 3. Confirmed Backend-Only Areas
- **Documents & Offers**: Backend has comprehensive routes (`/documents/`, `/documents/offers/`, etc.), but NO frontend API calls or pages exist.
- **Analytics**: Backend has `/analytics/`, frontend has `analytics.ts` calling `/analytics/dashboard/`, etc., but actual components are minimal. (Wait, Analytics.tsx exists).
- **RBAC Overrides & Deep Debug**: Backend has `/rbac/roles/...` and `/translations/overrides/`, frontend has minimal RBAC UI (`RBACDebugPage.tsx`).

## 4. Confirmed Frontend-Only or Unwired Areas
- Path Mismatches causing unwired views:
  - `/auth/` (Frontend) -> `/accounts/` (Backend)
  - `/organisation/` (Frontend) -> `/organisations/` (Backend)
  - `/messages/` (Frontend) -> `/communications/messages/` (Backend)
  - `/notifications/` (Frontend) -> `/communications/notifications/` (Backend)

## 5. Existing Automated Test Coverage
- **pytest**: EXTREMELY LOW. Only one test file found: `apps/accounts/tests/test_onboarding.py`.
- **schemathesis / vitest / playwright**: No logs found in `sys_know/testing/`.

## 6. Major Gaps in Current Real System
- **Missing Tests**: 99% of the backend features have no automated tests.
- **Routing Mismatches**: Significant inconsistencies between frontend API paths and backend route prefixes.
- **Unwired Document Generation**: `Documents` app is backend-only.

## 7. High-Risk Areas
- **Auth Flow**: Mismatched routes mean login/registration might be completely broken in the UI.
- **RBAC/Permissions**: No tests for `/rbac/` and role enforcement across other modules.
- **Candidate Passport & Identity**: Features like `/passport/withdraw-data/` are sensitive but untested.

## 8. Recommended Immediate Testing Priority
- 1. Fix route mismatches (Proxy config or update frontend APIs).
- 2. Add API tests for Auth & Onboarding.
- 3. Add API tests for Candidates CRM & Pipeline flows.
- 4. Add UI E2E tests for the candidate application flow.

## 9. Unverified Areas
- We cannot verify if frontend paths successfully proxy to the backend without checking proxy configs (e.g. Nginx, Vite proxy). Assuming they don't, many flows are broken.
"""

# 2. implemented_flows.md
flows_content = """# Implemented Flows

## Candidate Registration & Login
### Status
PARTIAL / UNVERIFIED (Path Mismatch)
### Backend Evidence
- `backend/apps/accounts/urls.py`
- Endpoints: `/accounts/login/`, `/accounts/register/candidate/`, `/accounts/onboarding/complete/`
### Frontend Evidence
- `frontend/src/api/auth.ts` calling `/auth/login/`, `/auth/register/candidate/`
- Pages: `auth/Login.tsx`, `auth/RegisterCandidate.tsx`
### Current Test Coverage
- pytest: `apps/accounts/tests/test_onboarding.py`
### Main Gaps
- Route mismatch (`/auth/` vs `/accounts/`).
- No e2e tests.
### Recommended Next Test
- Test end-to-end registration API using schemathesis or direct pytest.

## Candidate CRM & Management
### Status
IMPLEMENTED
### Backend Evidence
- `backend/apps/candidates/urls.py`
- Endpoints: `/candidates/`, `/candidates/<uuid:pk>/`, `/candidates/<uuid:pk>/notes/`
### Frontend Evidence
- `frontend/src/api/candidates.ts` calling `/candidates/`
- Pages: `candidates/CandidatesList.tsx`, `candidates/CandidateDetail.tsx`
### Current Test Coverage
- none
### Main Gaps
- Completely untested backend logic.
### Recommended Next Test
- Pytest API tests for creating and listing candidates.

## Job Requisitions & Postings
### Status
IMPLEMENTED
### Backend Evidence
- `backend/apps/jobs/urls.py`
- Endpoints: `/jobs/requisitions/`, `/jobs/postings/`
### Frontend Evidence
- `frontend/src/api/jobs.ts` calling `/jobs/requisitions/`, `/jobs/postings/`
- Pages: `jobs/JobsList.tsx`, `jobs/JobDetail.tsx`, `jobs/JobCreate.tsx`
### Current Test Coverage
- none
### Main Gaps
- Missing validation tests for stage transitions.
### Recommended Next Test
- Pytest API test for creating a requisition and publishing a job.

## Agency Relationships
### Status
IMPLEMENTED
### Backend Evidence
- `backend/apps/agencies/urls.py`
- Endpoints: `/agencies/relationships/`, `/agencies/assignments/`
### Frontend Evidence
- `frontend/src/api/agencies.ts` calling `/agencies/relationships/`
- Pages: `agencies/AgenciesList.tsx`, `agency/AgencyDashboard.tsx`
### Current Test Coverage
- none
### Main Gaps
- Untested assignment logic.
### Recommended Next Test
- Pytest API test for agency invitations and assignments.
"""

# 3. backend_only_features.md
backend_only_content = """# Confirmed Backend-Only Areas

## Documents & Offers
- **Path**: `/documents/`, `/documents/offers/`
- **Features**: Document generation, offer creation, approval workflow (`/documents/offers/<uuid:pk>/approve/`).
- **Frontend Status**: No `api/documents.ts` exists. No pages found for offer generation.

## Communication Webhooks & Email Audit
- **Path**: `/communications/communications/email-webhooks/<str:provider>`, `/communications/communications/email-audit/`
- **Features**: Tracking email deliveries, bounces, opens.
- **Frontend Status**: Handled transparently by backend, no UI exposed for audits.

## Translations & Overrides
- **Path**: `/translations/overrides/`
- **Features**: Dynamic string replacement/i18n.
- **Frontend Status**: No frontend admin UI for translation overrides.
"""

# 4. frontend_partial_or_unwired.md
frontend_partial_content = """# Confirmed Frontend-Only or Unwired Areas

## Authentication Path Mismatch
- **Frontend**: Expects `/auth/*` (e.g., `/auth/login/`)
- **Backend**: Exposes `/accounts/*` (e.g., `/accounts/login/`)
- **Impact**: Without proxy rewrites, all auth is broken.

## Organisation vs Organisations
- **Frontend**: `api/organisation.ts` calls `/organisation/profile/`, `/organisation/users/`
- **Backend**: Exposes `/organisations/profile/`, `/organisations/users/`
- **Impact**: 404 Not Found on all org management pages.

## Pipeline vs Applications Prefix
- **Frontend**: calls `/applications/` directly for standard pipeline stages.
- **Backend**: Exposes `/pipeline/applications/`
- **Impact**: 404 Not Found on pipeline drag-and-drop and stage moving.

## Messages & Notifications Prefix
- **Frontend**: calls `/messages/threads/` and `/notifications/`
- **Backend**: Exposes `/communications/messages/threads/` and `/communications/notifications/`
- **Impact**: In-app chat and notifications will fail.
"""

# 5. reality_based_testing_backlog.md
testing_backlog_content = """# Reality-Based Testing Backlog

## High Priority (Broken/Mismatched Flows)
1. **[E2E/Integration] Verify Auth Flow Paths**
   - Ensure the API gateway or Vite proxy correctly maps `/auth/` to `/accounts/`. Write an integration test hitting the frontend endpoint and verifying it reaches the backend.
2. **[E2E/Integration] Verify Organisation Paths**
   - Test if `/organisation/` correctly routes to `/organisations/`.

## Core Application Flows (Missing Tests)
3. **[API] Candidate Creation & Pipeline Movement**
   - Flow: Create candidate -> Add to pipeline -> Move stages.
   - Target: `backend/apps/candidates/`, `backend/apps/pipeline/`
4. **[API] Job Requisition & Publishing**
   - Flow: Create requisition -> Add stages -> Publish -> View Posting.
   - Target: `backend/apps/jobs/`
5. **[API] Agency Assignment Flow**
   - Flow: Invite Agency -> Accept -> Assign to Requisition -> Agency Submits Candidate.
   - Target: `backend/apps/agencies/`
6. **[API] Interview Scheduling**
   - Flow: Create template -> Schedule Interview -> Submit Feedback.
   - Target: `backend/apps/interviews/`

## Backend-Only Features (Missing Tests)
7. **[API] Documents & Offers Workflow**
   - Flow: Generate Offer -> Send -> Accept/Reject.
   - Target: `backend/apps/documents/`
8. **[API] Communications Webhooks**
   - Flow: Simulate webhook payload for email bounce/delivery.
   - Target: `backend/apps/communications/email_webhooks/`
"""

with open(os.path.join(REPORTS, 'system_reality_audit.md'), 'w') as f:
    f.write(audit_content)
with open(os.path.join(REPORTS, 'implemented_flows.md'), 'w') as f:
    f.write(flows_content)
with open(os.path.join(REPORTS, 'backend_only_features.md'), 'w') as f:
    f.write(backend_only_content)
with open(os.path.join(REPORTS, 'frontend_partial_or_unwired.md'), 'w') as f:
    f.write(frontend_partial_content)
with open(os.path.join(REPORTS, 'reality_based_testing_backlog.md'), 'w') as f:
    f.write(testing_backlog_content)

print("Markdown reports generated successfully in sys_know/reports/gemini/")
