# Recruiter Interview Queue QA

Module ID: `RECRUITER-INTERVIEW-QUEUE-01`

## Scope

Built a recruiter-side interview queue under:

- Recruiter Workspace
- Interviews
- Queue

Available to both company and agency recruiter roles.

## What Was Added

- Dedicated queue page: `frontend/src/pages/interviews/RecruiterInterviewQueue.tsx`
- Route wiring: `frontend/src/App.tsx`

## Data Source Used

- `interviewsApi.list()` for all queue sections and filters
- Existing interview actions:
  - `interviewsApi.reschedule()`
  - `interviewsApi.update()`
  - `interviewsApi.cancel()`
  - `interviewsApi.complete()`

## Queue Sections

### Upcoming Interviews

Shows:

- Candidate Name
- Job
- Interview Type
- Date
- Time
- Status
- Assigned Interviewer

### Pending Action

Shows:

- interviews needing scheduling
- interviews needing feedback
- interviews needing decision follow-up

### Today’s Interviews

Shows:

- interviews scheduled today
- quick join option
- quick actions

### Overdue Interviews

Shows:

- missed interviews
- pending feedback
- delayed scheduling

## Actions

Supports:

- Schedule
- Reschedule
- Cancel
- Assign interviewer
- Send reminder
- Mark complete

## Filters

Supports:

- Interview type
- Job
- Recruiter
- Status
- Date

## Bulk Actions

Supports:

- Bulk schedule
- Bulk assign
- Bulk reminder

## Integration Coverage

Connected to:

- Scheduling Engine
- Interview Engines
- Candidate system through interview records
- Notification workflow through reminder shell and scheduling/cancel actions

## Notes

- Reminder is implemented as a recruiter workflow shell message for now.
- Bulk assign uses the existing interview update endpoint with interviewer list patching.

## Embedded QA Checks

- Queue loads
- Filters work
- Actions work
- Bulk actions work
- No console crash during build validation
- No backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
