# Phase 54: Assignment And Operational Flag Bindings

## Prompt

Proceed with the next safe downstream bindings.

Implement stable owner-module contracts for:

1. `assign`
2. `mark_flag`

Rules:

* use owner-module contracts only
* do not use direct cross-module model writes from `orchestration_center`
* preserve tenant isolation
* preserve audit trail
* keep execution retry-safe and idempotent
* failures must remain non-blocking to originating business flows
* maintain clean ownership boundaries

## Outcome

This phase completes the next safe downstream bindings for `assign` and `mark_flag` without expanding into high-risk lifecycle automation.

The implementation keeps `orchestration_center` orchestration-only and binds through owner-module contracts:

* Pipeline-owned deadline contract for assignment updates on `ActionDeadline`
* Pipeline-owned operational flag contract for `Application` and `ActionDeadline`
* Interview-owned review-task contract for reviewer assignment
* Interview-owned operational flag contract for `Interview` and `InterviewReviewTask`

## Integration Style

### Assign

Owner-module contracts used:

* `apps.pipeline.services.PipelineDeadlineService.assign_automation_deadline(...)`
* `apps.interviews.services.InterviewReviewTaskService.assign_task(...)`

Supported real bindings:

* follow-up owner assignment on pipeline deadlines
* reviewer assignment on interview review tasks

Unsupported targets remain intentionally unbound and return `stubbed_unbound`.

### Mark Flag

Owner-module contracts used:

* `apps.pipeline.services.PipelineDeadlineService.mark_operational_flag(...)`
* `apps.interviews.services.InterviewReviewTaskService.mark_operational_flag(...)`

Supported real flags:

* `attention_needed`
* `review_required`
* `overdue_risk`
* `manual_check_required`

Flags remain operational metadata only. They do not mutate critical lifecycle state.

## Ownership Boundary

Ownership stays clean:

* Pipeline continues to own deadlines and application operational metadata
* Interviews continues to own review tasks and interview operational metadata
* `orchestration_center` does not directly write cross-module ownership fields or flag state
* `orchestration_center` only invokes stable owner-module service contracts

## Idempotency And Failure Behavior

Idempotency:

* assignment contracts return existing state as non-created when the target owner is already assigned
* flag contracts compare semantic payloads and ignore dynamic timestamp differences
* automation executor remains safe to retry

Failure behavior:

* failures are isolated to the automation action result
* audit trail remains intact
* originating business flow is not blocked
* unsupported target contracts return `stubbed_unbound` instead of forcing unsafe writes

## Files Updated

Backend services:

* `backend/apps/pipeline/services.py`
* `backend/apps/interviews/services.py`
* `backend/apps/orchestration_center/services/automation_action_executor.py`

Tests:

* `backend/apps/pipeline/tests/test_deadline_service.py`
* `backend/apps/interviews/tests/test_review_task_service.py`
* `backend/apps/orchestration_center/tests/test_runtime_engine.py`

## Test Coverage

Focused tests now cover:

* pipeline-owned assignment binding
* interview-owned review assignment binding
* pipeline-owned operational flag binding
* interview-owned operational flag binding
* idempotent duplicate behavior for both assignment and flagging flows
* tenant-scoped contract execution through the runtime engine

Verification:

* `python3 manage.py test apps.pipeline.tests.test_deadline_service apps.interviews.tests.test_review_task_service apps.orchestration_center.tests.test_runtime_engine -v 1`
* `python3 manage.py check`

## What Remains Stubbed

Still intentionally unbound because no stable owner-module contract is approved yet:

* generic assignment outside pipeline deadlines and interview review tasks
* generic flagging outside pipeline and interview operational metadata

High-risk automation remains out of scope:

* auto-reject
* auto-stage-move
* auto-offer transitions

## Final Status

`assign` and `mark_flag` are now real where safe owner-module contracts exist, with retry-safe, non-blocking, tenant-aware execution and preserved ownership boundaries.
