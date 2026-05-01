# 1. ORGANIZATION MODEL

## Models
- `Organisation` (`backend/apps/organisations/models.py`)
- `Department` (`backend/apps/organisations/models.py`)
- `Location` (`backend/apps/organisations/models.py`)
- `Team` (`backend/apps/organisations/models.py`)
- `TeamMembership` (`backend/apps/organisations/models.py`)

## Organisation fields
- `id` (UUID, PK)
- `tenant_id` (UUID, indexed)
- `name` (Char)
- `org_type` (choices: `company`, `agency`)
- `website` (Char)
- `logo_url` (Text)
- `industry` (Char)
- `size_range` (Char; choices: `1-10`, `11-50`, `51-200`, `201-500`, `500+`)
- `country_code` (Char, default `IN`)
- `contact_phone_country_code` (Char, default `IN`)
- `contact_phone_number` (Char)
- `timezone` (Char, default `UTC`)
- `address_line1` (Char)
- `address_line2` (Char)
- `city` (Char)
- `state` (Char)
- `country` (Char)
- `postal_code` (Char)
- `cin` (Char)
- `gst_number` (Char)
- `registration_number` (Char)
- `settings` (JSON)
- `metadata` (JSON)
- `created_by` (UUID)
- `is_deleted` (Bool, indexed)
- `deleted_at` (DateTime)
- `created_at` (DateTime)
- `updated_at` (DateTime)

## Relationships and linkage
- `Organisation` to tenant: linked by `tenant_id` UUID.
- `Department`, `Location`, `Team` each linked to tenant by `tenant_id` UUID.
- `TeamMembership` links `Team` to a user UUID (`user_id`).

## Hierarchy logic
- Department hierarchy field: `Department.parent_department_id` (UUID nullable).
- Team-to-department linkage field: `Team.department_id` (UUID nullable).
- Team-to-location linkage field: `Team.location_id` (UUID nullable).
- Team lead linkage field: `Team.team_lead_id` (UUID nullable).
- No additional hierarchy computation logic found in `organisations/views.py`; hierarchy is represented through stored IDs.

---

# 2. DEPARTMENTS

## Structure
- Model: `Department`.
- API endpoints in `backend/apps/organisations/urls.py`:
  - `GET/POST /departments/`
  - `GET/PUT/DELETE /departments/<uuid:pk>/`

## Fields
- `id`, `tenant_id`, `name`, `parent_department_id`, `head_user_id`, `description`, `is_active`, `metadata`, `created_by`, `is_deleted`, `deleted_at`, `created_at`, `updated_at`.

## Linkage
- Tenant-scoped by `tenant_id` in all list/get/update/delete queries.
- `Team.department_id` links teams to departments.

---

# 3. TEAMS

## Structure
- Model: `Team`.
- Membership model: `TeamMembership`.
- API endpoints:
  - `GET/POST /teams/`
  - `GET/PUT/DELETE /teams/<uuid:pk>/`
  - `GET/POST /teams/<uuid:team_id>/members/`
  - `DELETE /teams/<uuid:team_id>/members/<uuid:user_id>/`

## Team fields
- `id`, `tenant_id`, `name`, `department_id`, `location_id`, `team_lead_id`, `description`, `is_active`, `metadata`, `created_by`, `is_deleted`, `deleted_at`, `created_at`, `updated_at`.

## Ownership and tenant scope
- Team CRUD in `organisations/views.py` filters by `tenant_id=request.user.tenant_id`.
- Team creation saves `tenant_id` and `created_by` from request user.

## Hierarchy
- No team parent/child field exists.
- Team hierarchy logic not present.

---

# 4. MEMBERS

## Structure
- User model: `CustomUser` (`backend/apps/accounts/models.py`).
- Team membership model: `TeamMembership`.

## TeamMembership fields
- `id`, `tenant_id`, `team` (FK to Team), `user_id` (UUID), `role` (Char), `created_at`, `created_by`.
- DB uniqueness: `unique_together = ('team', 'user_id')`.

## Roles (user-level)
- `CustomUser.role` choices:
  - `super_admin`
  - `tenant_admin`
  - `hr_manager`
  - `hiring_manager`
  - `recruiter`
  - `interviewer`
  - `agency_owner`
  - `agency_admin`
  - `agency_recruiter`
  - `candidate`
  - `viewer`

## Mapping
- Org user list/invite/update/delete endpoints:
  - `GET/POST /organisations/users/`
  - `GET/PUT/DELETE /organisations/users/<uuid:pk>/`
- Team member add checks:
  - Team exists in same tenant.
  - User exists in same tenant.
  - Creates `TeamMembership` if not existing.

---

# 5. RBAC

## Models
- `Permission` (`rbac_permission`)
- `Role` (`rbac_role`)
- `RolePermission` (`rbac_role_permission`)

## Permission structure
- Fields: `code`, `label`, `module`, `module_label`, `resource`, `action`, `description`, `is_active`, `metadata`, timestamps.
- Code format documented in model: `<module>.<resource>.<action>`.

## Role structure
- Fields: `name`, `display_name`, `description`, `is_system`, `tenant_id`, `based_on_role`, timestamps.
- Many-to-many with `Permission` through `RolePermission`.
- Constraint: `unique_together = ('name', 'tenant_id')`.

## Role assignment and effective resolution
- User has role string in `CustomUser.role`.
- Permission resolution in `apps/rbac/utils.py`:
  - Finds `Role` by `name=user.role` with tenant-specific role priority over system role.
  - Resolves permissions from `RolePermission` where permission is active.
  - Caches per user/role key.

## RBAC APIs
- `GET /rbac/debug/`
- `GET/POST /rbac/roles/`
- `POST /rbac/roles/<uuid:template_role_id>/clone-template/`
- `PUT/DELETE /rbac/roles/<uuid:role_id>/`

## RBAC enforcement points
- Generic DRF permission factory: `require_permission(...)` in `apps/rbac/permissions.py`.
- Communications permission aliases in `apps/communications/permissions.py` map to RBAC codes.
- `NotificationControl` views use:
  - `can_view_notification_rules`
  - `can_manage_notification_rules`
- Email account views use:
  - `can_view_email_accounts`
  - `can_manage_email_accounts`
- Role CRUD endpoints gate by `_can_manage_roles(user)` in `rbac/views.py` with allowed roles:
  - `super_admin`, `tenant_admin`, `agency_owner`, `agency_admin`.

---

# 6. LOCATIONS

## Structure
- Model: `Location`.
- API endpoints:
  - `GET/POST /locations/`
  - `GET/PUT/DELETE /locations/<uuid:pk>/`

## Fields
- `id`, `tenant_id`, `name`, `address_line1`, `address_line2`, `city`, `state`, `country`, `postal_code`, `latitude`, `longitude`, `is_headquarters`, `is_active`, `metadata`, `created_by`, `is_deleted`, `deleted_at`, `created_at`, `updated_at`.

## Geo logic
- Latitude/longitude fields exist as decimals.
- Headquarters flag exists (`is_headquarters`).
- No additional geo computation logic in `organisations/views.py`.

## Usage
- `Team.location_id` links team to location.
- Location list/update/delete are tenant-scoped queries.

---

# 7. SETTINGS

## Configurable items found in Settings UI (`frontend/src/pages/Settings.tsx`)
- Organisation profile tab:
  - `name`, `website`, `reference_prefix_custom`, `country_code`, `timezone`, `settings.default_currency`, `industry`, `size_range`, `description`.
- Departments tab:
  - create/update/delete department fields passed from form (name, code in frontend form, status).
- Locations tab:
  - create/update/delete location fields passed from form (name, city, country, remote type flag, status).
- Users tab:
  - invite user (`email`, `role`, optional names).
  - edit user (`role`, `is_active`).
  - delete user.
- Roles & permissions tab:
  - create/update/delete tenant roles.
  - select permission codes for role.
- Communication tab:
  - connect/manage email accounts.
  - set default sender.
  - test/reconnect/disconnect.
  - email preferences (`allow_system_fallback`).
- Account tab:
  - user timezone/language preferences.
  - password change form.

## Storage model usage
- Organisation profile stored in `Organisation` fields plus `Organisation.settings` JSON.
- Reference prefix custom stored on tenant model (`Client.reference_prefix_custom`) in `OrganisationProfileView.put`.
- User account preferences stored in `CustomUser` fields (`timezone`, `language`).
- Email preferences stored in `communications_email_preferences` (`EmailPreference`).

## How used
- Onboarding guard checks `organisation.metadata.onboarding_completed` for non-candidate users.
- Organisation profile API enriches response with effective reference prefix values.
- Communication tab loads feature/oauth/account/template/history endpoints.

---

# 8. INTEGRATIONS

## Generic integrations module
- Model: `Integration` (`backend/apps/integrations/models.py`)
  - `name`, `provider_key`, `category`, `status`, `config_json`, `auth_data_json`, `is_connected`, `last_sync_at`.
  - uniqueness: `(tenant_id, provider_key)`.
- API:
  - `GET/POST /api/v1/integrations/`
  - `GET/DELETE /api/v1/integrations/<uuid:pk>/`

## Communications/email integration structure
- Email account model: `EmailSendingAccount` in `apps/communications/models.py`.
- Credential fields:
  - `access_token_encrypted`
  - `refresh_token_encrypted`
  - `smtp_password_encrypted`
- Related models:
  - `EmailAccountPermission`
  - `EmailPreference`
  - email templates/messages/audit models.

## Credentials handling
- OAuth and SMTP credential data is written via encrypted fields using `encrypt_json` and `encrypt_string` in `email_accounts/services.py`.
- OAuth state handling uses cache key prefix `comm_email_oauth_state` with TTL 900 seconds.
- OAuth initiate and callback endpoints:
  - Gmail initiate/callback
  - Microsoft initiate/callback

---

# 9. WORKFLOWS

## Onboarding workflow (company)
- Signup sets user role `tenant_admin`.
- Email verification required by guard.
- Onboarding wizard posts `hiring_style`, `team_size`, `automation_preference` to `/auth/onboarding/complete/`.
- Backend `CompleteOnboardingView`:
  - derives `user_type` from role mapping.
  - saves onboarding data to `user.metadata.onboarding`.
  - calls `_auto_configure`.
  - `_auto_configure` writes to `Organisation.metadata`:
    - `metadata['onboarding']`.
    - `metadata['onboarding_completed'] = True`.
  - creates automation rules in `AutomationRule` based on preferences.
  - emits `events.onboarding.completed` signal.

## Org setup workflow
- `CompanyOnboarding.tsx` loads org profile and determines setup completeness using frontend utility `isOrganisationSetupIncomplete(org)`.
- Org update uses `PUT /organisations/profile/`.
- Settings Profile tab also updates organisation profile via same endpoint.

## Approval flows
- No organisation/departments/teams/locations/member-change approval endpoints found in `organisations/urls.py` and `organisations/views.py`.
- Notification orchestration admin/debug endpoints exist in communications module for job retry/cancel/test, not org-structure approval.

---

# 10. EDGE CASES

## Multi-team user
- Supported by data model:
  - `TeamMembership` unique per `(team, user_id)`.
  - same user can have memberships across multiple teams.

## Cross-department roles
- User global role stored on `CustomUser.role`.
- TeamMembership has separate `role` field per team membership.
- No explicit backend policy in `organisations/views.py` linking team role constraints to department hierarchy.

## Partial setups
- `OrganisationProfileView.put` creates `Organisation(tenant_id=...)` if missing.
- `OnboardingGuard` redirects non-candidate users to `/onboarding/wizard` if `organisation.metadata.onboarding_completed` is falsy.
- `isOrganisationSetupIncomplete(org)` frontend utility treats setup incomplete when:
  - org missing, or
  - name empty / `My Organisation`, or
  - missing `country_code`/`industry`/`timezone`.

## Team member add duplicate
- Team member add uses `get_or_create`; returns error message if membership already exists.

## User deletion constraints
- In `UserDetailView.delete`:
  - user cannot delete own account.
  - delete marks `is_deleted=True`, `is_active=False`.

## Tenant scoping checks in team membership add
- Team lookup requires same tenant.
- User lookup requires same tenant.

