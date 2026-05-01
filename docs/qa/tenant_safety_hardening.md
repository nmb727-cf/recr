# Tenant Safety Hardening QA

## 1) Audit Summary

### Safe patterns found
- Consistent direct scoping in many endpoints: `filter(tenant_id=request.user.tenant_id)`.
- Role-gated access in multiple analytics and agency endpoints.
- Existing candidate visibility logic already attempted association-based access rules.

### Fragile patterns found
- Object fetches without tenant scoping in agency relationship/action endpoints.
- Query-parameter-driven scope controls (`tenant_id`, `agency_tenant_id`, `company_tenant_id`) in several modules.
- Repeated ad-hoc scoping logic in views instead of centralized access helper.
- Candidate visibility logic duplicated in list/detail/database flows.

### High-risk endpoints patched in this change
- Agency relationship detail/actions.
- Agency assignment list/detail/recruiter assignment actions.
- Candidate list/database/detail-visibility path via shared candidate visibility helper.
- Job pipeline snapshot requisition access check.
- Core analytics endpoints now reject tenant scope widening params.

### Modules still most exposed (deferred, not patched in this change)
- `workflow_execution`, `agency_workflows`, `orchestration_center`, and parts of `interviews` due to broad query-param tenant patterns.
- Additional list/detail endpoints outside the high-risk set still use manual per-view checks.

## 2) Old Fragile Patterns
- Scope widening via raw query params:
  - `request.query_params.get('tenant_id')`
  - client-supplied `company_tenant_id` / `agency_tenant_id` in read paths
- Unscoped object fetches:
  - `Model.objects.get(id=pk, is_deleted=False)` without tenant/association check
- Candidate visibility duplicated manually in multiple code paths.

## 3) New Shared Access Model
- Added/used shared tenant hardening in `backend/shared/tenant_access.py`:
  - `validate_no_scope_widening_params(...)`
  - `scope_queryset_by_tenant_fields(...)`
  - `scope_candidate_visibility_qs(...)`
  - `scope_agency_relationship_qs(...)`
  - `TenantAccessMixin` for reusable endpoint integration
- Added reusable manager/queryset primitives in `backend/shared/managers.py`:
  - `TenantScopedQuerySet`
  - `TenantScopedManager`

## 4) High-Risk Endpoints Patched
- `apps/agencies/views.py`
  - `AgencyRelationshipListView`
  - `AgencyRelationshipDetailView`
  - `AgencyRelationshipInviteView`
  - `AgencyRelationshipAcceptView`
  - `AgencyRelationshipSuspendView`
  - `AgencyRelationshipReactivateView`
  - `AgencyJobAssignmentListView`
  - `AgencyJobAssignmentDetailView`
  - `AgencyJobAssignRecruiterView`
- `apps/candidates/views.py`
  - `CandidateListView`
  - `CandidateDatabaseView`
  - `_get_visible_candidate` helper (affects detail/timeline/command-center)
- `apps/jobs/views.py`
  - `JobPipelineSnapshotView` now validates requisition belongs to accessible tenant scope
  - `JobRequisitionListView` now rejects scope-widening params
- `apps/analytics/views.py`
  - dashboard/recruitment/pipeline/agencies/candidates/interviews/interview-intelligence/control-tower reject scope-widening params

## 5) Candidate Global Entity Handling
- Preserved architectural rule: candidate identity remains global.
- Tenant-facing visibility now consistently bounded by explicit associations:
  - Candidate tenant ownership
  - Candidate linked via tenant application
  - Candidate linked via tenant engagement
- No unrestricted cross-tenant candidate list/detail exposure added.

## 6) Admin Override Rules
- Platform admin override is explicit through shared helper (`is_platform_admin`) and only where intentionally enabled (`allow_platform_admin=True`).
- Non-admin paths remain default-deny when tenant context is missing or outside association scope.

## 7) Test Coverage Added
- New tests: `backend/apps/agencies/tests/test_tenant_safety_hardening.py`
  - Reject query-param scope widening.
  - Block cross-tenant relationship read/mutate.
  - Confirm explicit admin override behavior.
  - Validate global candidate visibility is association-bounded.
  - Reject candidate list tenant scope widening via query params.

## 8) Migration / Compatibility Notes
- No API response schema changes introduced.
- Existing endpoints keep same paths and payload structure.
- Behavior change: endpoints now return `400` for explicit forbidden scope params and `404` for cross-tenant object access where previously unscoped reads could succeed.
