# Module Audit: talent_pools

## 1. Backend Files Found

* `apps/talent_pools/models.py`: Defines `TalentPool`, `CandidateTalentPoolMembership`, and `TalentPoolActivity`.
* `apps/talent_pools/serializers.py`: Serializers for pools, memberships, bulk actions, and activity logs.
* `apps/talent_pools/views.py`: ViewSets for talent pools and memberships, including bulk management and activity tracking.
* `apps/talent_pools/urls.py`: URL patterns using DRF DefaultRouter.
* `apps/talent_pools/services.py`: (Inferred) Internal services for recording activity.

## 2. Frontend Usage Found

* `../frontend/src/api/talentPools.ts`: Complete integration for pool CRUD, bulk candidate assignment, and activity monitoring.
* `../frontend/src/api/talentPools.ts` identifies a potential endpoint mismatch for candidate-specific pool retrieval.

## 3. Confirmed Backend Features

* **Talent Pool Lifecycle**: Full support for creating, updating, and archiving (`is_active=False`) talent pools.
* **Bulk Membership Management**: Robust `bulk-add` and `bulk-remove` actions with comprehensive validation for duplicates and tenant ownership.
* **Activity Audit Trail**: `TalentPoolActivity` model records every significant change (creation, member addition/removal) with actor tracking.
* **Smart Pool Metadata**: Infrastructure for storing search filters (`filters_json`) to support automated candidate grouping.
* **Event-Driven Architecture**: Integration with the core events system to notify other modules of membership changes.
* **Member Counting**: Automated annotation of member counts in pool listing.

## 4. Confirmed Frontend Features

* **Talent Pool Administration**: UI for managing the collection of candidate pools.
* **Batch Assignment UI**: Efficient interface for moving multiple candidates into specific pools.
* **Activity Timeline**: Displaying the history of modifications for a talent pool.

## 5. Backend Without Frontend

* **Automated Smart Pool Execution**: The backend supports `pool_type='smart'`, but the logic to periodically refresh or auto-populate these pools based on `filters_json` is not visible in the current API or viewsets.
* **Pool Coloring**: Backend supports a `color` field for UI indicators, which may have limited usage in the current interface.

## 6. Frontend Without Backend

* **Endpoint Mismatch**: The frontend attempts to fetch a candidate's pools via `/api/v1/candidates/${candidateId}/talent-pools/`, but this specific nested route is **MISSING** in both the candidates and talent_pools URL configurations. The backend currently expects query parameters on the flat memberships list.

## 7. Validation / Error Handling Gaps

* **Inconsistent Bulk Validation**: While `bulk-add` has extensive pre-checks, `bulk-remove` is more permissive and does not provide detailed feedback if some candidate IDs were invalid or not found in the pool.
* **Slug Collisions**: Slugs are generated from names but there is no explicit view-level validation to prevent collisions within a tenant during a `put` update if the name changes to something that would produce an existing slug.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/talent_pools/`.
* **Priority**: Integration tests for the bulk assignment logic and the activity logging accuracy.

## 9. Schema / API Documentation Gaps

* **Action Payload Definitions**: Custom actions like `bulk-add` and `bulk-remove` use standard serializers but may require additional `@extend_schema` decorators to correctly document the request/response shapes in OpenAPI.

## 10. Security / Permission Concerns

* **Missing Granular RBAC**: The ViewSets only require `IsAuthenticated`. Any user within the tenant (including `Viewers` or `Interviewers`) could potentially create or delete talent pools and modify memberships. These should be restricted to `Recruiter` or `Admin` roles.
* **Tenant Isolation**: Filtering is correctly applied at the queryset level using `request.user.tenant_id`.

## 11. Stability / Architecture Concerns

* **ViewSet Bloat**: `TalentPoolViewSet` is handling many custom actions. As membership logic grows (e.g., scoring, automated matching), these might need to be moved to dedicated service classes.
* **Implicit Role Checks**: Tenant type (`agency` vs `company`) is inferred from the user's role prefix, which is a fragile pattern.

## 12. Priority Fixes

### High
* **Fix Endpoint Mismatch**: Implement the `/candidates/${id}/talent-pools/` route or update the frontend to use the existing memberships API with query parameters.
* **Implement Role-based Access**: Add role checks to ensure only recruiters and admins can modify talent pools and memberships.
* **Implement Tests**: Add comprehensive test suite for membership validation and bulk operations.

### Medium
* **Implement Smart Pool Logic**: Complete the implementation of the smart pool filtering engine to auto-populate pools based on criteria.
* **Enhance OpenAPI Documentation**: Add detailed schemas for custom actions and activity logs.

### Low
* **Standardize Bulk Actions**: Align the error handling and validation logic between `bulk-add` and `bulk-remove`.

## 13. Unverified Items

* Background tasks for smart pool synchronization (UNVERIFIED).
* UI visualization of talent pool activity payloads (UNVERIFIED).

## 14. Recommended Next Tests

* `test_bulk_add_candidates_validation`: Verify that duplicates and candidates from other tenants are correctly rejected.
* `test_talent_pool_activity_logging`: Verify that adding a member creates a correctly formatted activity record.
* `test_tenant_pool_isolation`: Verify that a user cannot list or modify talent pools belonging to a different tenant.
* `test_smart_pool_filter_storage`: Verify that complex filter JSON is correctly persisted and retrieved.
* `test_membership_deletion_event`: Verify that removing a candidate from a pool triggers the expected system event.
