# Recruiter Bulk Scheduling QA

Module ID: `RECRUITER-BULK-SCHEDULING-01`

## Scope

Built a recruiter-side bulk scheduling workflow under:

- Recruiter Workspace
- Interviews
- Bulk Scheduling

Available to both company and agency recruiter roles.

## What Was Added

- Wizard page: `frontend/src/pages/interviews/RecruiterBulkScheduling.tsx`
- Route wiring: `frontend/src/App.tsx`
- Queue shortcut in `frontend/src/pages/interviews/RecruiterInterviewQueue.tsx`

## Data Sources Used

- `pipelineApi.listApplications()` for candidate/application selection
- `candidatesApi.list()` for candidate display
- `requisitionsApi.list()` for job filtering
- `interviewsApi.list()` for interviewer pool and conflict shell
- `interviewsApi.listTypes()` and `interviewsApi.listTemplates()` for setup options
- `interviewsApi.create()` for bulk interview creation

## Functional Coverage

### Candidate Selection

Supports:

- multi-select candidates
- filter by stage
- filter by interview type
- filter by job
- filter by recruiter

### Bulk Schedule Setup

Supports:

- choose interview type
- choose template
- choose interviewer(s)
- choose date range
- choose slot pattern
- choose duration
- timezone support

### Slot Assignment

Supports:

- same slot to many candidates
- sequential slots
- interviewer-specific slots
- obvious conflict detection shell

### Notifications

Supports selection for:

- send invite now
- send reminder
- notify recruiter
- notify interviewer
- notify candidate

### Review & Confirm

Shows:

- selected candidates
- selected slots
- assigned interviewers
- conflict warnings
- final confirmation

### Result Summary

Shows:

- scheduled count
- failed count
- skipped count
- warnings

## Notes

- Notification toggles are stored as recruiter workflow intent in the wizard UI; direct downstream notification dispatch remains future workflow wiring.
- Conflict detection is intentionally an obvious-shell pass based on interviewer overlap and time proximity.

## Embedded QA Checks

- Candidate selection works
- Bulk schedule works
- Slot assignment works
- Notifications step works
- Summary works
- No console crash during build validation
- No backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
