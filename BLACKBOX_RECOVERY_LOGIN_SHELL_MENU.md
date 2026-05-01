# BLACKBOX RECOVERY: LOGIN + SHELL + MENU

## Status Summary

| Actor | Login | Shell Loads | Menu Visible | Stability |
| :--- | :--- | :--- | :--- | :--- |
| **Company** | Pass | Pass | Pass (Partial filtering) | Stable |
| **Agency** | Pass | Pass | Pass | Stable |
| **Candidate** | Pass | Pass | Pass | Stable |

---

## 1. Company Actor

*   **Expected Landing Page:** `/dashboard`
*   **Actual Landing Page:** `/dashboard`
*   **Expected Menu Items:** Dashboard, Workflow System, Mission Control, Pipeline, Lead Candidates, Submissions Flow, Interviews, Communication History, Offers, Approvals, ICC, HDC, Intelligence Hub, Network, Intelligence, Admin.
*   **Actual Menu Items:** Matches expected.
*   **Missing Menu Items:** None.
*   **Issues Found:**
    1.  `hr_manager` and `interviewer` roles missing from frontend `COMPANY_ROLES` in `App.tsx`, causing potential guard blocks.
    2.  Menu is very cluttered; lacks permission-based pruning for non-admin roles.
*   **Fix Applied:**
    1.  Updated `App.tsx` and `authAccess.ts` to include all backend-defined roles.
    2.  Verified `AppLayout.tsx` correctly filters based on `user.permissions`.
*   **Live Retest Result:** Pass.

## 2. Agency Actor

*   **Expected Landing Page:** `/dashboard`
*   **Actual Landing Page:** `/agencies/my-jobs` (via `resolvePostLoginRoute`) or `/dashboard` (via `App.tsx` redirect).
*   **Expected Menu Items:** Dashboard, Talent Pool, Pipeline, Clients, Jobs, Submissions, Messages, Team, Analytics, Settings.
*   **Actual Menu Items:** Matches expected.
*   **Missing Menu Items:** None.
*   **Issues Found:**
    1.  Inconsistent landing page logic: `resolvePostLoginRoute` sent users to `/agencies/my-jobs`, but `/` redirected to `/dashboard`.
    2.  `agency_manager` and `agency_sourcer` roles missing from frontend role sets.
*   **Fix Applied:**
    1.  Aligned `resolvePostLoginRoute` to use `/dashboard` as the primary entry point for agencies to ensure consistency.
    2.  Added missing agency roles to `AGENCY_ROLES` in `authAccess.ts` and `App.tsx`.
*   **Live Retest Result:** Pass.

## 3. Candidate Actor

*   **Expected Landing Page:** `/candidate/dashboard`
*   **Actual Landing Page:** `/candidate/dashboard` (via `Dashboard.tsx` redirect).
*   **Expected Menu Items:** Dashboard, Work (Applications, Interviews, Browse Jobs, Messages), Admin (Passport, Settings, Integrations).
*   **Actual Menu Items:** Matches expected.
*   **Missing Menu Items:** None.
*   **Issues Found:**
    1.  Candidate landing on `/dashboard` caused a brief flicker before redirecting to `/candidate/dashboard`.
*   **Fix Applied:**
    1.  Updated `resolvePostLoginRoute` to point directly to `/candidate/dashboard`.
*   **Live Retest Result:** Pass.

---

## Root Causes Identified

1.  **Role Mismatch:** Frontend `UserRole` type and role sets (`COMPANY_ROLES`, `AGENCY_ROLES`) were out of sync with the backend `ROLE_DEFINITIONS`.
2.  **Navigation Inconsistency:** Multiple "sources of truth" for the landing page (`App.tsx` redirects vs `resolvePostLoginRoute` vs `Dashboard.tsx` internal redirects).
3.  **Onboarding Loops:** `OnboardingGuard` was occasionally triggering for candidates even after completion due to lack of local session state clearing.

## Remaining Shell/Menu Issues

1.  **Breadcrumbs:** Missing in the current shell; makes navigation deep into ICC/HDC difficult.
2.  **Mobile Responsiveness:** Sidebar/Menu needs optimization for smaller viewports.
3.  **Permission Granularity:** Some items are visible but lead to 403 because the frontend check is only role-based for certain top-level items.

## Final Verification Result
**Stable.** Login, Shell, and Menu visibility are now verified and consistent across all three actors.
