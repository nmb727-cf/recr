# Talent Operating System
## Phase 53: Safe Downstream Bindings Expansion

Date: `2026-04-01`
Prompt Basis: `Expand safe downstream bindings through owner-module contracts`

### Newly Real Bindings

#### 1. `notify`

Owner module contract:

- `apps.communications.services.CommunicationDispatchService.dispatch_notification`
- `apps.communications.services.CommunicationDispatchService.queue_email`

Real behaviors now supported:

- reminder notification
- escalation notification
- candidate follow-up notification
- panelist / reviewer reminder notification

Channel support:

- `in_app`
- `email`
- `both`

Ownership:

- communications owns `Notification`
- communications owns queued email dispatch
- `orchestration_center` only resolves payload and calls the communication-owned contract

#### 2. `create_review_task`

Owner module contract:

- `apps.interviews.services.InterviewReviewTaskService.create_task`

Owner record:

- `interviews_review_task`

Real binding now supported for:

- interview feedback review
- other interview-owned review task types routed through `owner_module=interviews`

Ownership:

- interviews owns interview review task state
- `orchestration_center` does not own the review record for interview review work

#### 3. `escalate`

Owner module contract:

- `apps.pipeline.services.PipelineDeadlineService.escalate_automation_deadline`

Optional paired communication contract:

- `CommunicationDispatchService.dispatch_notification`

Real binding now supported for:

- deadline-driven escalation where a pipeline-owned `ActionDeadline` exists
- escalation notification when recipients are explicitly provided

Ownership:

- pipeline owns deadline escalation state
- communications owns escalation notifications
- `orchestration_center` orchestrates only

### Contract Style Used

- communications: direct owner-module service boundary
- interviews: direct owner-module service boundary
- pipeline: direct owner-module service boundary

No hidden direct model writes were added from `orchestration_center` into those domains.

### Idempotency And Failure Behavior

#### Communications

- in-app notifications use `metadata.orchestration_dedupe_key`
- duplicate unread notifications reuse the existing notification
- queued email uses the communications queue contract
- failures remain non-blocking to originating business actions

#### Interview Review Tasks

- deduplicated by `external_reference` for pending tasks
- failures affect only automation action status, not business flow

#### Pipeline Escalation

- deadline escalation is idempotent when the same deadline is already escalated to the same reviewer
- escalation requires an existing owned pipeline deadline
- failures remain inside automation execution and do not block business writes

### Test Coverage Added

Communications tests:

- `backend/apps/communications/tests/test_dispatch_service.py`

Interviews tests:

- `backend/apps/interviews/tests/test_review_task_service.py`

Pipeline tests:

- `backend/apps/pipeline/tests/test_deadline_service.py`

ICC runtime tests:

- `backend/apps/orchestration_center/tests/test_runtime_engine.py`

Coverage includes:

- event -> automation run
- automation run -> downstream contract call
- retry behavior
- duplicate/idempotency protection
- non-blocking failure behavior
- tenant isolation
- communications notification binding
- interview review task binding
- pipeline escalation binding

### Seed / Demo Data Polish

Updated seed command:

- `backend/apps/orchestration_center/management/commands/seed_intelligence_hub.py`

Enhancements:

- deterministic communication templates needed by Intelligence Hub are seeded safely
- built-in automation rules now carry more realistic notification / follow-up / review metadata
- seed command remains rerunnable and safe for dev/staging

### What Remains Stubbed

Still intentionally not fully bound:

- `assign`
- `mark_flag`

Reason:

- no stable owner-module write contract exists yet for those actions

Partially bound:

- `create_review_task` is real for interview-owned review work only
- non-interview review domains remain on ICC fallback behavior or should be deferred until owner-module contracts exist

### Verification

Executed successfully:

- `python3 manage.py test apps.communications.tests.test_dispatch_service apps.interviews.tests.test_review_task_service apps.pipeline.tests.test_deadline_service apps.orchestration_center.tests.test_runtime_engine -v 1`
- `python3 manage.py seed_intelligence_hub`
- `python3 manage.py check`
- `python3 manage.py migrate interviews`

### Recommended Next Step

Next safe binding candidates:

1. introduce owner-module contracts for `assign`
2. introduce owner-module contracts for `mark_flag`
3. expand review bindings to HDC / offer workflows only after those modules expose stable review-task ownership contracts
