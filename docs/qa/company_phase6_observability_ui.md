# Company Phase 6 — Observability + UI

## Workflow Timeline
Status: Implemented

Notes:
- Added reusable company-side workflow timeline/status panel component.
- Wired on:
  - Job Detail
  - Candidate Detail
  - Pipeline Application Detail panel
- Timeline displays recent workflow events from workflow instance timeline APIs.

## Workflow Status Panel
Status: Implemented

Notes:
- Panel now shows:
  - current stage
  - workflow status
  - owner
  - waiting reason
  - pending tasks
  - approvals pending
  - SLA risk / stuck risk
- Added backend workflow instance list filtering by `entity_id` to support entity-level lookup from company pages.

## Dashboard
Status: Implemented

Notes:
- Added company operations snapshot widgets for:
  - Interviews Today
  - Offers Pending
  - Onboarding In Progress
  - Tasks Pending
  - SLA Alerts
- Existing cards (Active Jobs, candidates/pipeline/interviews) remain intact.

## Analytics
Status: Partial

Notes:
- Added company analytics metrics block with:
  - time to hire
  - stage duration
  - interview conversion rate
  - offer acceptance rate
  - onboarding completion rate
- Pipeline distribution chart remains active for stage-level visibility.
- Additional deep analytics pages/charts can be expanded in the next pass.

## UI Fixes
Status: Partial

Notes:
- Implemented targeted company-side visibility/UI wiring for workflow observability and dashboard completeness.
- Did not perform a full global frontend lint debt cleanup in this phase (large pre-existing errors across unrelated modules).

Frontend Stability: Partial

Overall Phase Completion: 84 %

## Test Case Results

Test 1  
Workflow running  
Expected: timeline visible  
Result: Passed (timeline/status panel visible on Job/Candidate/Pipeline details)

Test 2  
Candidate in pipeline  
Expected: stage visible  
Result: Passed (current stage/status visible in panel)

Test 3  
Task pending  
Expected: dashboard widget  
Result: Passed (Tasks Pending widget added)

Test 4  
SLA breach  
Expected: alert  
Result: Passed (SLA Alerts widget added using workflow SLA tracker feed)

Test 5  
Analytics view  
Expected: data visible  
Result: Partial (core metrics visible; deep analytics expansion pending)
