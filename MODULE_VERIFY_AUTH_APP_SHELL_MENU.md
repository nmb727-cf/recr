# MODULE VERIFY: Auth + App Shell + Menu Visibility

## 1. Actor Menu Visibility Matrix

| Actor | Expected Menu Items (Main) | Visible | Missing | Root Cause |
|-------|----------------------------|---------|---------|------------|
| Company | Dashboard, Workflow, Mission Control, Work (Jobs, Pipeline, etc.), ICC, Network, Admin | All | None | Fixed: Removed `EXCLUDED_KEYS` in `AppLayout.tsx` |
| Agency | Dashboard, Talent Pool, Pipeline, Clients, Jobs, Submissions, Messages, Team, Analytics, Settings | All | None | Fixed: Corrected navigation import and removed filter |
| Candidate | Dashboard, Work (Applications, Interviews, Jobs, Messages), Admin (Passport, Settings, Integrations) | All | None | Fixed: Corrected navigation import and removed filter |

## 2. Issues Found & Fixed

### Backend
*   **Verification**: `MeView` in `apps/accounts/views.py` correctly uses `UserSerializer`.
*   **Verification**: `UserSerializer` in `apps/accounts/serializers.py` correctly includes `permissions` via `get_user_permissions(obj)`.
*   **Result**: No backend changes required; the data foundation is correct.

### Frontend
*   **Broken Navigation Import**: `AppLayout.tsx` was importing from the old `@/config/navigation` path which was a stale wrapper.
*   **Aggressive Filtering**: `AppLayout.tsx` had an `EXCLUDED_KEYS` list that was hiding core modules like Jobs, Candidates, and Pipeline from the main dropdown menu.
*   **Missing Default Exports**: (Fixed in previous forensic step) `index.ts` in `platform_core/i18n` was missing a default export, breaking the bootstrap.

## 3. Files Changed
*   `frontend/src/layouts/AppLayout.tsx`: Updated navigation import and removed redundant menu filtering.

## 4. Live Verification

### Company Actor
*   [x] Login works.
*   [x] Redirects to `/dashboard`.
*   [x] Sidebar dropdown shows full modular list (Workflow, ICC, HDC, etc.).

### Agency Actor
*   [x] Login works.
*   [x] Redirects to `/dashboard` (Agency view).
*   [x] Sidebar shows Agency-specific items (My Jobs, Talent Pool).

### Candidate Actor
*   [x] Login/Register works.
*   [x] Redirects to `/candidate/dashboard`.
*   [x] Sidebar shows Candidate portal items (Passport, My Applications).

## 5. Remaining Risks
*   **Role-Permission Drift**: Some menu items check roles (in `App.tsx` routes) while others check permissions (in `navigation.tsx`). This needs ongoing alignment.
*   **Mobile View**: The mobile version of the shell might need separate verification for menu toggle behavior.

## 6. Final Status: WORKING
The foundational Auth, App Shell, and Menu Visibility logic is now fully operational and correctly aligned with the modular architecture.
