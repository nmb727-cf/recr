# Module Audit: jobs

## 1. Backend Files Found

* `apps/jobs/models.py`: Defines models for `JobRequisition`, `JobPosting`, `JobStage`, and `CustomFieldDefinition`.
* `apps/jobs/serializers.py`: Serializers for jobs, postings, and stages.
* `apps/jobs/views.py`: Comprehensive views for managing requisitions (approval, publish, clone) and stages.
* `apps/jobs/urls.py`: Main URL patterns for internal job management.
* `apps/jobs/candidate_urls.py`: Separate URL paths for candidate-facing job search and applications.

## 2. Frontend Usage Found

* `../frontend/src/api/jobs.ts`: Large-scale integration for hiring managers and recruiters to manage requisitions and stages.
* `../frontend/src/api/candidate.ts`: Integration for candidates to search and apply to jobs.
* `../frontend/src/api/interviews.ts`: Links job requisitions to interview packages.

## 3. Confirmed Backend Features

* **Job Requisition Lifecycle**: Full support for `Draft -> Pending Approval -> Approved -> Published`.
* **Stage Management**: Customizable stages per job with drag-and-drop reordering support in backend.
* **Public/Private Split**: Requisitions (internal) are linked to Postings (external-facing).
* **Application Deduplication**: Logic in `JobApplyView` to block multiple applications from the same user for a specific job.
* **Skill-based Recommendations**: Candidate-side endpoint `/recommended-jobs/` matching candidate skills with active postings.
* **Custom Fields**: Flexible architecture for tenant-specific custom data fields on job and application entities.

## 4. Confirmed Frontend Features

* **Requisition Management**: Creating and managing the hiring pipeline.
* **Public Job Board**: Searching and viewing job details as a candidate.
* **Job Application**: Direct submission of applications from candidate accounts.
* **Stage Customization**: Reordering and editing hiring stages via UI.

## 5. Backend Without Frontend

* **Job Save**: `JobSaveView` exists as a placeholder and is called by `frontend/src/api/jobs.ts`, but does not persist anything in the backend.
* **Hiring Statuses**: Complex hiring statuses like `in_guarantee_period` or `replacement_required` exist in the model but may be underutilized in the current UI.

## 6. Frontend Without Backend

* None identified. The backend provides a very rich set of endpoints for both sides of the hiring process.

## 7. Validation / Error Handling Gaps

* **Insecure Serializer**: `JobRequisitionSerializer` exposes `salary_min` and `salary_max` even if `salary_visible` is False. It also doesn't handle `is_confidential` to hide sensitive job data.
* **Duplicate Stage Handling**: Requisition creation creates 5 default stages manually; this should be moved to a service to ensure consistency.
* **Conflicting Applications**: `JobApplyView` only checks for duplicates, but doesn't handle cases where a candidate is already in an incompatible stage (e.g., already joined or recently rejected).

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/jobs/`.
* **Priority**: Integration tests for the approval/publish flow and the application submission logic.

## 9. Schema / API Documentation Gaps

* **Generic Responses**: Spectacular documentation is missing detail for complex responses like `JobRequisitionDetailView` which includes stages and placement guarantees.
* **Calculated Fields**: The schema doesn't describe the custom fields structure returned when using `CustomFieldValue`.

## 10. Security / Permission Concerns

* **Confidential Data Exposure**: `JobRequisitionDetailView` allows any authenticated candidate to read active requisitions. If `is_confidential=True` or `salary_visible=False`, sensitive fields MUST be redacted in the serializer. Currently, they are not.
* **Tenant Isolation**: Need to double-check that `JobRequisition.objects.get(id=pk, status='active')` (in `DetailView.get_object`) doesn't accidentally leak non-public data to users of other tenants.

## 11. Stability / Architecture Concerns

* **Model Complexity**: `JobRequisition` is becoming a "God model" with fields for approval, hiring, and automation.
* **Fragmented URLs**: URLs are split across `urls.py` and `candidate_urls.py`, which is good for organization but needs careful permission management.

## 12. Priority Fixes

### High
* **Fix Serializer Leak**: Add logic to `JobRequisitionSerializer` to hide `salary_min`/`max` when `salary_visible` is False and to redact info if `is_confidential` is True.
* **Implement Tests**: Add core integration tests for job creation and application.

### Medium
* **Refactor Stage Creation**: Move default stage creation logic to a service.
* **Implement Saved Job Model**: Complete the `JobSaveView` implementation.

### Low
* **Cleanup Statuses**: Ensure `hiring_status` and `status` are synchronized correctly throughout the lifecycle.

## 13. Unverified Items

* Bulk job import/export (UNVERIFIED).
* External job board integrations (LinkedIn, etc.) (UNVERIFIED).

## 14. Recommended Next Tests

* `test_requisition_approval_lifecycle`: Verify state transitions from Draft to Approved.
* `test_publish_creates_posting`: Verify that publishing an approved requisition creates a corresponding `JobPosting` and sets a slug.
* `test_duplicate_application_prevention`: Verify a candidate cannot apply twice to the same job.
* `test_salary_visibility_redaction`: Verify that salary fields are redacted when `salary_visible` is False.
* `test_job_recommendation_accuracy`: Verify that `/recommended-jobs/` returns postings matching the candidate's skills.
