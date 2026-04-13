# Module Audit: organisations

## 1. Backend Files Found

* `apps/organisations/models.py`: Defines `Organisation`, `Department`, `Location`, `Team`, and `TeamMembership`.
* `apps/organisations/serializers.py`: Serializers for managing organisational structure and tenant profiles.
* `apps/organisations/views.py`: Comprehensive views for profile management, user invitations, and managing departments/locations/teams.
* `apps/organisations/urls.py`: Unified URL patterns for all organisational endpoints.

## 2. Frontend Usage Found

* `../frontend/src/api/organisation.ts`: Complete integration for managing the organisation profile, users, departments, locations, and teams.
* `../frontend/src/api/organisation.ts` uses `/organisation/profile/`, `/organisation/users/`, etc.

## 3. Confirmed Backend Features

* **Tenant Profile Management**: Support for branding (logos), legal details (CIN, GST), and operational settings (timezone, country).
* **Hierarchical Structure**: Support for parent-child department relationships and head-of-department assignments.
* **Physical Asset Tracking**: Managing office locations with headquarters flagging and latitude/longitude support.
* **Collaboration Framework**: Creating teams with explicit leads and memberships.
* **Integrated User Sourcing**: In-app views for inviting new users to the tenant, including automatic creation of `CustomUser` records.
* **Soft Deletion Architecture**: All major organisational entities support non-destructive deletion with `deleted_at` tracking.

## 4. Confirmed Frontend Features

* **Organisation Settings Dashboard**: Centralized UI for updating company information and legal identities.
* **Team & Structure Builder**: Interfaces for managing physical locations and departmental hierarchies.
* **User Directory & Invitations**: UI for recruiters and admins to manage their team members and invite new colleagues.

## 5. Backend Without Frontend

* **Hierarchical Departmental Querying**: Backend supports complex parent-child links, but the frontend may use a flat list for management.
* **Custom Metadata**: Every model includes a `metadata` JSON field for extension, which may be underutilized in the current UI.

## 6. Frontend Without Backend

* None identified. The backend provides a thorough set of APIs covering all structural and administrative needs of an organisation.

## 7. Validation / Error Handling Gaps

* **Cascade Deletion Risks**: Deleting a department (`soft_delete`) does not check for or handle active child departments or teams, potentially leaving orphaned records in the structure.
* **Incomplete Invitation Logic**: `UserListView.post` generates a random password but lacks a formal invitation/verification token lifecycle (e.g., expiry, resend logic).
* **Duplicate Profile Protection**: `OrganisationProfileView.put` creates a new profile if not found, but doesn't explicitly verify if a profile already exists for the `tenant_id` at the model constraint level beyond the view logic.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/organisations/`.
* **Priority**: Integration tests for user invitation flows and departmental hierarchy management.

## 9. Schema / API Documentation Gaps

* **Mixed Response Types**: `TeamListView` returns augmented data (member counts) that is not reflected in the default OpenAPI schema.
* **Cross-App Serializer Linking**: Documentation for user-related endpoints may not correctly resolve the `UserSerializer` defined in the `accounts` app.

## 10. Security / Permission Concerns

* **Insufficient Admin Controls**: User invitations and organisation profile updates only require `IsAuthenticated`. These should be strictly restricted to `TENANT_ADMIN` or `SUPER_ADMIN` roles.
* **Cross-Tenant User Modification**: `UserDetailView` relies on `tenant_id` filtering, which is correct, but still lacks role-based protection for sensitive user modifications (e.g., changing a user's role).

## 11. Stability / Architecture Concerns

* **View Responsibility Overlap**: The `organisations` app handles user invitations and management, which overlaps with the `accounts` app's responsibilities.
* **Hardcoded Choices**: Organisation sizes and types are hardcoded as choices in the model, making it difficult to expand without migrations.

## 12. Priority Fixes

### High
* **Implement Role-based Access Control**: Restrict structural and user management endpoints to administrative roles.
* **Implement Tests**: Add comprehensive test suite for organisational structure and user invitations.

### Medium
* **Formalize Invitation Lifecycle**: Move user invitation logic to a service that handles secure tokens and email dispatch.
* **Enhance OpenAPI Documentation**: Add detailed schemas for team and user listing responses.

### Low
* **Implement Cascade Safeguards**: Add validation to prevent deletion of departments that still contain active teams or sub-departments.

## 13. Unverified Items

* Organisation-level preference synchronization with the `accounts` app (UNVERIFIED).
* Actual email delivery for new user invitations (UNVERIFIED).

## 14. Recommended Next Tests

* `test_organisation_profile_update_permission`: Verify that only authorised users can update company details.
* `test_department_hierarchy_creation`: Verify the correct linking of child departments to their parents.
* `test_user_invitation_deduplication`: Verify that inviting an existing user returns a conflict or handles it gracefully.
* `test_team_membership_uniqueness`: Verify that a user cannot be added twice to the same team.
* `test_location_headquarters_flagging`: Verify that setting a new HQ correctly updates or respects other location settings.
