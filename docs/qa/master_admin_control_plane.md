# Master Admin Control Plane MVP QA

## 1. Audit summary

### Existing before this work
- Tenant creation: existed via auth registration flows (`accounts.views.create_tenant`).
- Tenant status model: existed on `tenants.Client.status` but no dedicated master-admin API surface.
- Tenant verification state: no explicit backend API or canonical field; only ad-hoc metadata usage.
- Usage limits / feature flags: no master-admin CRUD; tenant-level settings were scattered in org/intelligence settings.
- Platform settings: no platform-level operational settings API.
- Platform audit visibility: generic audit tables existed (`IntelligenceAuditLog`) but no dedicated master-admin access endpoint.
- Discoverable admin UI: no dedicated `/admin/*` control-plane pages.
- Super-admin backend enforcement: not consistently centralized for platform operations.

### Gap classification before implementation
- Backend partial: tenant lifecycle data existed, but admin control APIs missing.
- UI missing: no dedicated control-plane pages/routes/menu.
- Logic missing: safe status workflows and bounded limit/flag mutation APIs.
- Permission missing: no master-admin-only permission boundary for platform control plane.

## 2. Admin MVP scope implemented
- Master admin dashboard: `/admin`
- Tenant list: `/admin/tenants`
- Tenant detail: `/admin/tenants/:id`
- Platform settings: `/admin/settings`
- Admin audit: `/admin/audit`

## 3. Endpoints added/hardened

Added under `/api/v1/admin/`:
- `GET /tenants/`
- `GET /tenants/{tenant_id}/`
- `POST /tenants/{tenant_id}/verify/`
- `POST /tenants/{tenant_id}/suspend/`
- `POST /tenants/{tenant_id}/reactivate/`
- `POST /tenants/{tenant_id}/deactivate/`
- `PUT /tenants/{tenant_id}/feature-flags/`
- `PUT /tenants/{tenant_id}/limits/`
- `GET /settings/`
- `PUT /settings/`
- `GET /audit/`

All above are guarded by:
- `IsAuthenticated`
- `IsSuperAdmin`

All mutation actions are audited using `AuditService` with `master_admin.*` action types.

## 4. Routes/pages added
- `frontend/src/pages/admin/MasterAdminDashboard.tsx`
- `frontend/src/pages/admin/MasterAdminTenants.tsx`
- `frontend/src/pages/admin/MasterAdminTenantDetail.tsx`
- `frontend/src/pages/admin/MasterAdminSettings.tsx`
- `frontend/src/pages/admin/MasterAdminAudit.tsx`
- API client: `frontend/src/api/masterAdmin.ts`
- App routes in `frontend/src/App.tsx`
- Sidebar discoverability entries in `frontend/src/config/navigation.tsx`
- Sidebar filtering in `frontend/src/layouts/AppLayout.tsx` to hide `/admin*` routes from non-super-admin roles

## 5. Tenant action rules
- Verify:
  - updates verification metadata (`verification_state=verified`, timestamp, actor)
- Suspend:
  - allowed unless tenant already terminated
  - stores reason + actor metadata
- Reactivate:
  - allowed unless tenant already terminated
- Deactivate:
  - safe soft-disable by status transition to `terminated`
  - no hard delete performed

Global safety enforcement added:
- Suspended/terminated tenants are blocked from normal API flows by centralized middleware check.
- Admin and auth/public endpoints are exempted to allow platform recovery and login flows.

## 6. Feature flag / limit rules
- Feature flags:
  - explicit object of boolean flags (`{flag_key: true/false}`)
  - stored in organisation settings under `settings.feature_flags`
  - audited with before/after values
- Usage limits:
  - explicit numeric fields (`user_limit`, `job_limit`, `candidate_limit`)
  - bounds validated in serializer
  - stored in organisation settings under `settings.limits`
  - audited with before/after values

## 7. RBAC rules
- Master admin APIs are super-admin only.
- Tenant admin and other roles are denied at backend permission layer.
- Frontend routes for control plane are also role-protected (`super_admin`) but backend remains source of truth.

## 8. Test coverage
- Added: `backend/apps/tenants/tests/test_master_admin_control_plane.py`
  - non-admin denied
  - tenant admin denied
  - verify/suspend/reactivate flow
  - feature flag update
  - limit update
  - audit entry creation

## 9. Deferred admin items
- No billing/subscription control in this MVP (explicitly deferred).
- No impersonation support added.
- No broad master-data CRUD beyond platform settings.
- No enterprise workflow for multi-step admin approvals; this MVP is direct-action with audit trail.
