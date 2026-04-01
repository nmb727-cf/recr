# Phase 55: Candidate-Owned Assignment Contract Binding

## Prompt

Proceed with the next safe owner-module binding for `assign`.

Use this decision sequence:

1. audit existing stable recruiter-assignment contracts
2. bind to a stable existing contract if present
3. otherwise create a target-owned assignment contract before binding
4. add focused tests

## Assignment Contract Audit

Stable assignment contracts found before this phase:

* `PipelineDeadlineService.assign_automation_deadline(...)`
  * owner: Pipeline deadline domain
  * entity owned: `ActionDeadline`
* `InterviewReviewTaskService.assign_task(...)`
  * owner: Interviews review domain
  * entity owned: `InterviewReviewTask`

No stable recruiter-assignment service existed in:

* Candidates
* generic recruiter ownership
* generic follow-up owner assignment outside deadline/review-task ownership

## Safest Next Binding

The safest next owner-module binding was Candidates because:

* candidate ownership already exists in the domain via `Candidate.owner_user_id`
* active engagement ownership already exists via `CandidateEngagement.owner_user`
* assignment behavior was still being done directly inside candidate views
* it could be cleanly extracted into a candidate-owned service boundary without introducing cross-module ownership drift

## Implementation

Added owner-module contract:

* `apps.candidates.services.CandidateAssignmentService.assign_candidate_owner(...)`

Behavior:

* validates tenant scope
* validates candidate existence
* validates assignee user existence
* updates candidate owner in the Candidates domain
* optionally syncs the active engagement owner in the Candidates domain
* records a candidate timeline event for owner-module auditability
* remains idempotent when the same owner is already assigned

`orchestration_center` binding:

* `apps.orchestration_center.services.automation_action_executor.AutomationActionExecutor._execute_assign(...)`

New supported binding:

* `owner_module='candidates'`
* `assignment_target='candidate_owner'`

## Ownership Boundary

Ownership stays clean:

* Candidates owns candidate and active engagement assignment state
* `orchestration_center` only invokes the candidate-owned service contract
* no direct cross-module candidate writes were added inside `orchestration_center`

## Failure And Retry Behavior

* invalid assignee or missing candidate raises inside the owner-module contract
* automation runtime records the action failure and marks the run `partial`
* originating business flow remains non-blocking
* repeated assignment to the same owner is deduplicated

## Tests Added

Candidate owner contract tests:

* `backend/apps/candidates/tests/test_assignment_service.py`

Runtime binding tests:

* `backend/apps/orchestration_center/tests/test_runtime_engine.py`

Covered:

* automation-triggered candidate assignment
* idempotent duplicate assignment behavior
* tenant isolation
* candidate timeline audit creation
* non-blocking downstream failure handling

Verification:

* `python3 manage.py test apps.candidates.tests.test_assignment_service apps.orchestration_center.tests.test_runtime_engine --noinput -v 1`
* `python3 manage.py test apps.pipeline.tests.test_deadline_service apps.interviews.tests.test_review_task_service --noinput -v 1`
* `python3 manage.py check`

## What Remains Unbound

Still intentionally unbound because no approved stable owner-module contract exists yet:

* generic recruiter assignment outside Candidates, Pipeline deadlines, and Interview review tasks
* assignment for other domains that still rely on view-level or implicit ownership updates

## Final Status

`assign` now has three real owner-module bindings:

* Pipeline deadline assignment
* Interview review-task assignment
* Candidate owner assignment

This phase keeps `orchestration_center` orchestration-only and expands assignment only where target modules expose clean ownership contracts.
