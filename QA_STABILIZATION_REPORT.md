# QA & Stabilization Report: Tenant Isolation (TOS-PLATFORM-TENANT-SEPARATION-HARDENING-001)

## 1. Root Cause Summary
The agency environment was exposing company-side data and UI elements due to a breakdown in both frontend state management and backend role isolation:
*   **Frontend Routing Leakage:** The `isAgency` boolean check in `Dashboard.tsx` failed to account for all agency roles (e.g., `agency_manager`, `agency_admin`, `agency_sourcer`), defaulting these users to the `CompanyDashboard`. 
*   **Frontend Config Overlap:** The `agencySidebarConfig` shared almost exact structural copies of the `companySidebarConfig`, loading company-specific pipeline and record views blindly.
*   **Cache Persistence:** The `authStore.ts` cleared local storage on logout but left the React Query cache intact. A subsequent agency login in the same browser hydrated the UI with stale company data.
*   **Backend Endpoint Isolation:** While `TenantAccessMixin` scoped queries to `tenant_id`, agency roles were previously granted company-level permissions (e.g., `jobs.job.view`). Without an explicit endpoint-level block, agency users could interact with core company modules if they accessed the direct API paths.

## 2. Files Changed
*   `frontend/src/pages/dashboard/Dashboard.tsx` (Fixed `isAgency` role check)
*   `frontend/src/config/navigation.tsx` (Rewrote `agencySidebarConfig` to native Staffing CRM structure)
*   `frontend/src/App.tsx` (Added `queryClient.clear()` to `AuthBootstrap` on logout)
*   `backend/apps/core/middleware.py` (Injected DRF dispatch patch for cross-tenant API isolation)
*   `AGENCY_ARCHITECTURE_RESET.md` (Defined strict boundaries for Agency-native modules)

## 3. Backend Fixes
*   **Enforced Strict API Routing Guard:** Implemented a robust interceptor within DRF's `dispatch()` method in `backend/apps/core/middleware.py`.
*   **Isolation Logic:**
    *   Identifies if the `request.user` is an agency user vs. a company user via `is_agency_user`.
    *   Strictly blocks agency users from accessing company-specific domains (`/api/v1/jobs/`, `/api/v1/candidates/`, `/api/v1/pipeline/`, `/api/v1/analytics/`) before any data fetching or query evaluation occurs (returning 403 Forbidden).
    *   Allows public endpoints (e.g., `/api/v1/jobs/public/`) so candidate-facing behavior is unaffected.
    *   Blocks company users from accessing the isolated `/api/v1/agency-candidates/` endpoints.

## 4. Frontend Fixes
*   **Role Routing Fixed:** Expanded the `isAgency` check in `Dashboard.tsx` to match the complete `['agency_owner', 'agency_admin', 'agency_manager', 'agency_recruiter', 'agency_sourcer']` array.
*   **Navigation Re-Architecture:** Purged all company modules from the agency sidebar and replaced them with the newly defined Agency IA: `Talent Pool`, `Pipeline`, `Hotlists`, `Followups`, `Clients`, `Jobs`, `Submissions`, `Team`, `Analytics`, `Settings`.
*   **React Query Cache Purging:** Implemented `queryClient.clear()` inside the `AuthBootstrap` lifecycle in `App.tsx`. Whenever `isAuthenticated` evaluates to `false` (e.g., upon logout), all stale data is immediately evicted from memory.

## 5. Isolation Test Matrix

| Scenario | Expected Result | Status |
| :--- | :--- | :--- |
| **New Agency Login** | Sees clean agency dashboard and sidebar | PASS |
| **Existing Agency Login** | Sees existing agency data, no company UI | PASS |
| **Empty Agency State** | Blank tables/widgets (no stale company data) | PASS |
| **Company Login** | Unaffected; sees full ATS and company modules | PASS |
| **Switch Tenant/Role** | Query cache cleared; data strictly separated | PASS |
| **Deep-link routing** | Agency forced to `/dashboard` or 403s on company routes | PASS |
| **API Direct Access** | Agency hitting `/api/v1/jobs/` receives 403 Forbidden | PASS |

## 6. Remaining Risks
*   **Shared Modules:** Modules like `/api/v1/interviews/` and `/api/v1/agencies/` are shared. While `tenant_id` scoping protects the data, careful attention must be paid when extending these modules to ensure agency logic doesn't leak into company views.
*   **Sourcing Logic:** Implementation of resume parsing and quick-add requires validation to ensure created core candidates don't accidentally expose the `tenant_id` of the agency to other companies outside of a direct submission.

## 7. Status
**PASS.** Tenant isolation is now strictly enforced across both the API gateway and the frontend state engine. The architecture reset is complete. Safe to proceed with Agency feature development.
