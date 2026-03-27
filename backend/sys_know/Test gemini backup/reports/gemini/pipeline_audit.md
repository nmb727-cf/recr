# Module Audit: pipeline

## 1. Backend Files Found

* `apps/pipeline/models.py`: Core models for `Application`, `ApplicationStageHistory`, `ActionDeadline`, `Placement`, `CommissionRecord`, and `PlacementGuarantee`.
* `apps/pipeline/serializers.py`: Serializers for all pipeline-related models with calculated fields for guarantee and protection.
* `apps/pipeline/views.py`: Comprehensive views for application lifecycle (create, move, shortlist, reject, withdraw, offer), bulk actions, and pipeline grouping.
* `apps/pipeline/urls.py`: URL patterns for application and pipeline management.
* `apps/pipeline/guarantee.py`: Complex business logic for tracking and resolving placement guarantees for agency candidates.
* `apps/pipeline/commercial_views.py`: Separate views for commercial closure (placements and commissions).

## 2. Frontend Usage Found

* `../frontend/src/api/pipeline.ts`: Integration for the Kanban pipeline board and bulk application actions.
* `../frontend/src/api/analytics.ts`: Calls pipeline analytics for reporting.
* `../frontend/src/api/candidates.ts`: Links candidate profiles to their current pipeline status.

## 3. Confirmed Backend Features

* **Application State Machine**: `validate_application_move` enforces no skipping of stages and mandatory interview completion before hiring.
* **Audit Logging**: `ApplicationStageHistory` records every stage transition with mandatory notes.
* **SLA/Deadline Automation**: Automatic creation of `ActionDeadline` records for initial review (24h), interview scheduling (48h), and offer follow-up (48h).
* **Cross-Tenant Guarantee Engine**: Automated lifecycle tracking (Active -> Breached -> Replacement/Refund Requested -> Expired) for agency placements based on partnership terms.
* **Bulk Processing**: Backend support for batch moving, rejecting, or shortlisting multiple candidates in one request.
* **Commercial Closure Separation**: Decoupled commercial state (`Placement`) from the hiring process, allowing billing to proceed independently.

## 4. Confirmed Frontend Features

* **Kanban Pipeline Board**: Grouping candidates by hiring stage for specific job requisitions.
* **Batch Action Interface**: Efficient UI for recruiters to process multiple applications simultaneously.
* **Application History**: Displaying the timeline of stage movements and notes for a candidate.

## 5. Backend Without Frontend

* **Placement & Commission Management**: Extensive backend models and views for commercial billing and commission tracking (`commercial_views.py`) exist but are not found in the primary frontend pipeline API.
* **Guarantee Resolution Workflow**: Complex breach/refund logic in `guarantee.py` may lack deep integration in the current recruiter UI.

## 6. Frontend Without Backend

* None identified. The backend provides a very robust set of endpoints covering all required pipeline and application features.

## 7. Validation / Error Handling Gaps

* **Insecure Application Updates**: `ApplicationDetailView.put` allows updating application status without calling `check_protected_action`, potentially bypassing agency protection rules.
* **Missing Custom Validation**: The state machine doesn't support custom validation rules per stage (e.g., "must have an assessment score to move past screening").
* **Bulk Error Feedback**: `BulkActionView` returns a list of errors but continues processing valid applications; the frontend needs to handle this partial success state clearly.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/pipeline/`. This module is critical as it handles hiring logic and commercial state.
* **Priority**: Integration tests for the stage movement state machine and the guarantee resolution logic.

## 9. Schema / API Documentation Gaps

* **Generic Success Responses**: Spectacular documentation is missing detail for complex payloads in `PipelineView` and `ApplicationDetailView`.
* **Undocumented Calculated Fields**: The `is_agency_protected` and `is_under_guarantee` fields in `ApplicationSerializer` are not explicitly defined in the OpenAPI schema.

## 10. Security / Permission Concerns

* **Insufficient Granular RBAC**: Current views only require `IsAuthenticated`. They lack role-based checks (e.g., only HR Managers should move candidates to the 'Joined' stage).
* **Missing Protection Enforcement**: Need to audit all status-changing views to ensure they call `check_protected_action` to respect agency exclusivity periods.

## 11. Stability / Architecture Concerns

* **God Views**: `views.py` is nearly 1,000 lines and contains a mix of hiring logic and administrative tools.
* **Hook Proliferation**: The module relies on many external hooks from `apps.candidates.pipeline_hooks` which may lead to fragile coupling.

## 12. Priority Fixes

### High
* **Enforce Protection on Updates**: Add `check_protected_action` to `ApplicationDetailView.put` and `ApplicationMoveStageView`.
* **Implement Tests**: Add comprehensive test suite for application stage movements and SLA deadline creation.

### Medium
* **Granular Role Checks**: Implement permission decorators (`@require_permission`) for sensitive actions like Hiring, Offering, or Bulk Rejecting.
* **Enhance OpenAPI Documentation**: Add detailed schemas for the grouped Pipeline payload.

### Low
* **Centralize Guarantee Logic**: Ensure all guarantee-related status changes are handled exclusively via `guarantee.py` to avoid inconsistent state.

## 13. Unverified Items

* Commercial commission invoicing and reminder automation (UNVERIFIED).
* External job board application sync (UNVERIFIED).

## 14. Recommended Next Tests

* `test_application_stage_skip_prevention`: Verify a candidate cannot skip stages without moving through them sequentially.
* `test_hire_requires_interview`: Verify a candidate cannot be moved to 'Joined' or 'Offer' without at least one completed interview.
* `test_sla_deadline_creation`: Verify that a 'shortlist' action creates a 48-hour interview scheduling deadline.
* `test_duplicate_application_protection`: Verify correct deduplication logic in the manual application creation flow.
* `test_guarantee_breach_resolution`: Verify that marking a guarantee as breached for a replacement request resets the job's hiring status.
