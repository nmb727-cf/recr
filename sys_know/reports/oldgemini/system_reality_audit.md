# System Reality Audit

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
