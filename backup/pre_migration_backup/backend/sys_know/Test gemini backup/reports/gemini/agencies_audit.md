# Module Audit: agencies

## 1. Backend Files Found

* `apps/agencies/models.py`: Core models for `AgencyClientRelationship`, `AgencyJobAssignment`, `AgencyPerformanceScore`, `GuestPortal`, and `EmailTrackingConfig`.
* `apps/agencies/serializers.py`: Serializers for relationships, assignments, and performance scores.
* `apps/agencies/views.py`: Comprehensive views for relationship management, guest portals, and candidate submissions.
* `apps/agencies/urls.py`: URL patterns for both company-side and agency-side operations.

## 2. Frontend Usage Found

* `../frontend/src/api/agencies.ts`: Extensive integration for managing partnerships, job assignments, guest portals, and candidate submissions.
* `../frontend/src/api/analytics.ts`: Calls agency performance analytics.
* `../frontend/src/pages/agencies/CompanyAgencies.tsx`: Primary page for managing agency relationships from the company side.

## 3. Confirmed Backend Features

* **Multi-channel Connections**: Support for full tenant relationships, magic-link guest portals, email-domain tracking, and offline clients.
* **Agency Sourcing Flow**: Company assigns jobs to preferred agencies with submission limits and deadlines.
* **Candidate Submission & Deduplication**: Agencies can submit candidates directly into a company's pipeline. Includes cross-tenant candidate creation and deduplication via `global_hash`.
* **Automated Retention & Guarantee**: Models support tracking candidate exclusivity periods and replacement/refund guarantees.
* **Performance Scoring**: Model support for tracking submission, shortlist, and join rates for agencies.

## 4. Confirmed Frontend Features

* **Relationship Management Dashboard**: Comprehensive UI for inviting and managing agency partners.
* **Guest Portal Creation**: Wizard for inviting external partners via magic links.
* **Agency Candidate Submission**: Interface for recruiters from agencies to submit candidates to assigned jobs.
* **Assigned Jobs View**: Agency-side view of jobs they are authorized to source for.

## 5. Backend Without Frontend

* **Performance Score Tracking**: Backend supports automated performance scoring (`AgencyPerformanceScore`), but this data may not be fully visualized in the current UI beyond simple analytics.
* **Commission Milestones**: Backend supports structured payment schedules and milestones, but these may lack complex UI for tracking completion.

## 6. Frontend Without Backend

* **Agency Submission Governance**: The frontend calls `/agencies/submissions/${submissionId}/governance/` to approve/reject agency submissions, but this endpoint is **MISSING** in the backend. This is a significant gap in the submission lifecycle.

## 7. Validation / Error Handling Gaps

* **Incomplete Submission Validation**: `AgencySubmitCandidateView` relies heavily on `global_hash` for deduplication. If `global_hash` generation is inconsistent, duplicate candidates may be created across pools.
* **Manual Data Normalization**: Views like `AvailableAgencyListView` use manual ID normalization logic which should be moved to a robust utility to avoid fragile data type handling.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/agencies/`.
* **Priority**: Integration tests for the cross-tenant candidate submission flow and guest portal invite/accept flow.

## 9. Schema / API Documentation Gaps

* **Missing Detailed Schemas**: Many views lack `@extend_schema` to describe their complex response payloads (e.g., `AgencyMyJobsView` returns a mixed requisition/assignment object).
* **Undocumented Error Codes**: Many views return custom error messages that are not documented in the OpenAPI schema.

## 10. Security / Permission Concerns

* **Cross-Tenant Data Visibility**: `AvailableAgencyListView` returns all agency tenants. This needs to be checked against privacy policies to ensure non-public agencies aren't leaked.
* **Guest Portal Access**: Guest portals are currently unauthenticated (magic links). Need to ensure they are strictly limited to the intended partner's data.

## 11. Stability / Architecture Concerns

* **View Complexity**: `views.py` is nearly 50,000 bytes and over 1,500 lines. This suggests the need for breaking down into smaller components (e.g., `relationship_views.py`, `submission_views.py`, `portal_views.py`).
* **Coupling with Candidates**: `AgencySubmitCandidateView` is tightly coupled with `Candidate` and `Application` models from other apps.

## 12. Priority Fixes

### High
* **Implement Missing Governance Endpoint**: Add `/agencies/submissions/${id}/governance/` to the backend to support the frontend's submission approval flow.
* **Implement Tests**: Add comprehensive test suite for candidate submissions and relationship lifecycle.

### Medium
* **Enhance OpenAPI Documentation**: Add detailed schemas for all agency-side endpoints.
* **Refactor Large Views**: Split `views.py` into logical sub-modules for better maintainability.

### Low
* **Centralize ID Normalization**: Move the `normalize_tenant_id` logic to a shared utility in `apps.core`.

## 13. Unverified Items

* Email tracking domain monitoring logic (UNVERIFIED).
* Actual commission calculation and billing (UNVERIFIED).

## 14. Recommended Next Tests

* `test_agency_relationship_invite_accept`: Verify state transitions from Pending to Active after invitation.
* `test_candidate_submission_deduplication`: Verify an agency cannot submit the same candidate twice to the same job.
* `test_guest_portal_creation_link`: Verify a unique slug and invite token are generated for new guest portals.
* `test_agency_job_assignment_limits`: Verify an agency cannot exceed the `max_submissions` limit on a job assignment.
* `test_agency_performance_score_calc`: Verify the logic that calculates shortlisted and joined rates for agencies.
