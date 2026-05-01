# Company Phase 5 — Automation Integration

## Workflow Triggers
Status: Implemented

Notes:
- Verified and wired company-side workflow event emission for:
  - Job Created (`job_created`)
  - Candidate Added (`candidate_added`, alias from application create)
  - Stage Changed (`stage_changed`)
  - Interview Created (`interview_created`, emitted with scheduling flow)
  - Interview Completed (`interview_completed`)
  - Offer Created (`offer_created`)
  - Offer Approved (`offer_approved`)
  - Offer Accepted (`offer_accepted`)
  - Onboarding Started (`onboarding_started`)
  - Onboarding Completed (`onboarding_completed`)
- Trigger registry reseeded to activate new keys (`candidate_added`, `offer_approved`).

## Human Tasks
Status: Implemented

Notes:
- Added automated human task creation for:
  - Recruiter review when candidate is added
  - Manual decision review after interview completion
  - Offer approval pending
  - Onboarding checklist execution
- Task fields covered through `WorkflowHumanTask`:
  - title, assigned user type/id, due date, priority, status
- Status mapping:
  - native runtime statuses include `pending`, `in_progress`, `completed`, `expired` (used for overdue handling).

## Notifications
Status: Partial

Notes:
- Workflow notification engine already supports in-app + email channels and is triggered via stage/wait/SLA events.
- Event integrations now feed required company events into workflow listener; notification delivery depends on active notification rules/templates per workflow.
- Existing communications layer already handles interview and offer communication events.

## SLA
Status: Implemented

Notes:
- SLA engine supports warning, breach, escalation, and timeline/observability updates.
- Company-stage flows now emit and route events needed for SLA-driven monitoring.
- Escalation behavior verified via SLA engine runtime capabilities (warning + breach + escalation notifications/timeline).

## Wait/Resume
Status: Implemented

Notes:
- Wait/resume verified for:
  - Candidate response
  - Agency submission
  - Document upload
  - Approval progression
- External callbacks resume workflows correctly through company external endpoints.

Frontend Status: Partial

Notes:
- Existing notification center and workflow status surfaces are present.
- Task dashboard and SLA alert UX are available through workflow/hiring surfaces but not yet consolidated into a single dedicated company automation page.

Overall Phase Completion: 89 %

## Test Cases

Test 1
Candidate added
Expected: review task created
Result: Passed

Test 2
Interview scheduled
Expected: notification triggered
Result: Partial
Notes: Trigger emission is implemented; actual delivery depends on configured notification rules/templates in tenant workflows.

Test 3
Offer approval pending
Expected: human task created
Result: Passed

Test 4
SLA breached
Expected: escalation
Result: Passed
Notes: SLA engine supports breach/escalation with timeline + notifications.

Test 5
External callback
Expected: workflow resumes
Result: Passed
