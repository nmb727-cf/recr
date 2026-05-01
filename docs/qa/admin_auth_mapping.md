# Admin Auth Mapping QA

## Root Cause
- Valid platform-admin users were being redirected to `/unauthorized` because frontend and backend master-admin checks were not fully aligned.
- Backend shared rule (`can_access_master_admin`) supports elevated identity flags and a permission-based path (`master_admin.access`).
- Frontend shared rule (`canAccessMasterAdmin`) did not include permission-based access, so users represented by permission grant could fail frontend admin checks even when backend intended to allow them.
- This impacted:
  - post-login admin redirect decision
  - protected `/admin*` route access
  - admin sidebar visibility

## Backend Fields Returned (Login + `/auth/me`)
From `backend/apps/accounts/serializers.py` (`UserSerializer`), backend returns:
- `role`
- `is_super_admin` (derived)
- `is_superuser`
- `is_staff`
- `permissions`

## Frontend Fields Expected
Frontend master-admin evaluation now uses:
- `role`
- `is_super_admin`
- `is_superuser`
- `is_staff`
- `permissions` (checks `master_admin.access`)

## Final Shared Master-Admin Rule
- Frontend: `frontend/src/utils/authAccess.ts` -> `canAccessMasterAdmin(user)`
- Backend: `backend/shared/tenant_access.py` -> `can_access_master_admin(user)`

Decision rule:
1. user must be authenticated (backend) / present (frontend)
2. allow if any true:
   - `role === 'super_admin'`
   - `is_super_admin === true`
   - `is_superuser === true`
   - `is_staff === true`
   - `permissions` contains `master_admin.access`
3. backend fallback: if `user.permissions` attribute is not present on request user, resolve permissions through RBAC (`get_user_permissions(user)`)

## Final Redirect Rule
From `resolvePostLoginRoute(user)` in `frontend/src/utils/authAccess.ts`:
- master admin -> `/admin`
- candidate -> `/candidate/dashboard`
- agency admin roles (`agency_owner`, `agency_admin`, `agency_recruiter`) -> `/agencies/my-jobs`
- tenant/company roles (`tenant_admin`, `hr_manager`, `recruiter`, `hiring_manager`, `interviewer`, `viewer`) -> `/dashboard`
- unknown/no access -> `/unauthorized`

Login page behavior (`frontend/src/pages/auth/Login.tsx`):
- if `from` is an `/admin...` path, keep that path only when `canAccessMasterAdmin(user)` is true
- otherwise redirect to `/unauthorized`

## Actual Admin Route Path
- Admin landing path: `/admin`
- Additional admin routes:
  - `/admin/tenants`
  - `/admin/tenants/:id`
  - `/admin/settings`
  - `/admin/audit`

## Files Changed
- `frontend/src/utils/authAccess.ts`
- `frontend/src/utils/authAccess.test.ts`
- `frontend/src/components/common/ProtectedRoute.test.tsx`
- `backend/shared/tenant_access.py`
- `backend/apps/tenants/tests/test_master_admin_control_plane.py`
- `docs/qa/admin_auth_mapping.md`

## Test Results
- Frontend:
  - `cd frontend && npm test -- --run src/utils/authAccess.test.ts src/components/common/ProtectedRoute.test.tsx`
  - Result: PASS (`2` files, `8` tests)
- Backend:
  - `./venv/bin/python -m pytest -q backend/apps/tenants/tests/test_master_admin_control_plane.py -q`
  - Result: PASS
  - Includes explicit coverage for permission-based admin access on admin API permission gate.

## Scenario Verification Matrix
- master admin login -> `/admin` : pass by shared rule
- tenant admin login -> `/dashboard` : pass
- agency admin login -> `/agencies/my-jobs` : pass
- candidate login -> `/candidate/dashboard` : pass
- unauthorized admin access -> `/unauthorized` : still blocked by protected-route guard
