# Module Audit: rbac

## 1. Backend Files Found

* `apps/rbac/models.py`: Defines `Permission`, `Role`, and `RolePermission` (join table).
* `apps/rbac/permissions.py`: Contains the `require_permission` factory for DRF views.
* `apps/rbac/registry.py`: Central declarative registry of all platform permissions and default role mappings.
* `apps/rbac/utils.py`: Runtime utilities for checking user permissions with built-in caching.
* `apps/rbac/views.py`: Tenant-aware views for role catalog management, cloning, and debugging.
* `apps/rbac/management/commands/seed_rbac.py`: (Inferred) Command to sync the registry with the database.

## 2. Frontend Usage Found

* `../frontend/src/api/rbac.ts`: Integration for role catalog listing, role creation, template cloning, and updates.
* `../frontend/src/api/rbac.ts` supports custom tenant roles and permission editing.

## 3. Confirmed Backend Features

* **Centralized Permission Registry**: Modular definition of permissions (`jobs.job.view`, `candidates.candidate.create`, etc.) in a single file.
* **System vs. Tenant Roles**: Distinction between platform-managed system roles (immutable names) and tenant-created custom roles.
* **Dynamic Permission Factory**: Seamless integration with DRF via the `require_permission` decorator.
* **Performance Caching**: 5-minute caching layer for user permissions to minimize database load on every request.
* **Role Derivation**: Support for creating new roles "based on" existing system templates.
* **Role Applicability Engine**: Logic to filter roles and permissions by tenant type (Agency vs. Company).

## 4. Confirmed Frontend Features

* **Role Administration Dashboard**: Comprehensive UI for viewing system role templates and tenant roles.
* **Permission Mapping UI**: Interface for toggling atomic permissions for specific tenant roles.
* **Role Creation Wizard**: Workflow for cloning system templates into editable tenant roles.

## 5. Backend Without Frontend

* **Action Scoping**: The models and registry have placeholders for `scope` (own/team/all), but this logic is not yet implemented in the permission checks or exposed in the UI.
* **Inactive Permissions**: Backend supports marking permissions as `is_active=False`, which will hide them from all checks and catalogs.

## 6. Frontend Without Backend

* None identified. The backend provides a robust and flexible API for the current role management requirements.

## 7. Validation / Error Handling Gaps

* **Cache Invalidation Gap**: `RBACRoleDetailView` does NOT call `invalidate_user_permission_cache` after updating a role's permissions. This means users may have stale permissions for up to 5 minutes after a role change.
* **Registry Sync Logic**: There is no runtime check to ensure that the database `rbac_permission` table is in sync with `registry.py` before performing checks; it relies entirely on the manual `seed_rbac` command.
* **Missing Permission Validation**: Role creation doesn't strictly validate that the provided `permission_codes` are currently defined in the registry, only that they exist in the database.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/rbac/`. Given this is the security backbone of the application, this is a high-priority gap.
* **Priority**: Unit tests for the `require_permission` decorator and integration tests for tenant-role isolation.

## 9. Schema / API Documentation Gaps

* **Generic Success Responses**: `RBACRoleCatalogView` and `RBACDebugView` return complex nested dictionaries that are not explicitly modeled in the OpenAPI schema.
* **Custom Error Codes**: 403 Forbidden messages from `_can_manage_roles` are not documented with their specific triggers.

## 10. Security / Permission Concerns

* **Stale Permission Window**: Due to the missing cache invalidation, a user who has been stripped of a permission could potentially still perform that action for up to 5 minutes.
* **Role Name Collisions**: While `unique_together = [('name', 'tenant_id')]` exists, if a tenant creates a role with the same name as a system role, the priority logic in `get_user_permissions` correctly picks the tenant role, but this could lead to confusion.
* **Bootstrap Role Dependency**: The system relies on `user.role` (string) matching `Role.name`. If these get out of sync, the user effectively loses all permissions without a clear error.

## 11. Stability / Architecture Concerns

* **Coupling via Role Keys**: The entire system is coupled to string-based role names (e.g., 'recruiter'). Changing a role name in `accounts` requires a corresponding update in `rbac`.
* **Registry Bloat**: As the platform grows, `registry.py` will become extremely large. It may eventually need to be split into module-specific registry files.

## 12. Priority Fixes

### High
* **Fix Cache Invalidation**: Add `invalidate_user_permission_cache` calls to all role update and delete views.
* **Implement Tests**: Add comprehensive test suite for the RBAC resolution logic and view-level protections.

### Medium
* **Formalize Scope Logic**: Implement the `scope` (own/team/all) logic in `utils.py` to support more granular data access.
* **Enhance OpenAPI Documentation**: Add detailed schemas for the role catalog and debug responses.

### Low
* **Automate Seeding**: Run `seed_rbac` automatically during deployment or as part of migrations to ensure the registry is always in sync.

## 13. Unverified Items

* Efficiency of the `_priority` annotation in `get_user_permissions` at scale (UNVERIFIED).
* Interaction between RBAC and Django's built-in `is_staff` / `is_superuser` flags (UNVERIFIED).

## 14. Recommended Next Tests

* `test_permission_caching_and_invalidation`: Verify that permission changes are reflected within the expected timeframe (immediately after fix).
* `test_require_permission_decorator`: Verify that a view decorated with `require_permission` correctly blocks unauthorized users and allows authorized ones.
* `test_tenant_role_isolation`: Verify that a custom role created in Tenant A is not visible or usable by users in Tenant B.
* `test_role_cloning_integrity`: Verify that a cloned role correctly inherits all permissions from its system template.
* `test_seed_rbac_idempotency`: Verify that running the seed command multiple times does not create duplicate permissions or roles.
