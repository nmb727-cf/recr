# Recruiter Productivity Tools QA

Module ID: `RECRUITER-PRODUCTIVITY-TOOLS-01`

## Scope

Built recruiter productivity tools under:

- Recruiter Workspace
- Interviews
- Productivity Tools

Available to both:

- company recruiter workspace
- agency recruiter workspace

## Files Updated

- `frontend/src/pages/interviews/RecruiterProductivityTools.tsx`
- `frontend/src/App.tsx`

## Shared Engine

One shared productivity engine is used for both workspaces.

Workspace-specific behavior is selected from authenticated role:

- Company roles:
  - `tenant_admin`
  - `recruiter`
  - `hiring_manager`
- Agency roles:
  - `agency_owner`
  - `agency_admin`
  - `agency_recruiter`

## Data Source Used

- `interviewsApi.list()`
- `interviewsApi.update()`
- `interviewsApi.reschedule()`
- `interviewsApi.complete()`

## Shared UI Sections

- Quick Actions
- Bulk Actions
- Reminder Center
- Productivity Shortcuts
- Pending Work Buckets
- Context Summary

## Company Logic

### Filters

- job
- department
- interviewer
- hiring manager
- status
- date

### Company Actions

- fast schedule next round
- assign interviewer / panel
- pick slot quickly
- remind interviewer
- remind hiring manager
- mark overdue follow-up
- bulk assign
- bulk reschedule
- bulk update interview status
- internal coordination note shell

## Agency Logic

### Filters

- client company
- client job
- recruiter
- candidate owner
- status
- date

### Agency Actions

- schedule recruiter screen fast
- mark screen complete
- send candidate reminder
- schedule with client
- follow up with client
- reschedule quickly
- bulk reminders
- bulk status update
- bulk screening / coordination actions
- quick call log shell
- quick note shell

## Embedded QA Checks

- company productivity tools show company-specific actions
- agency productivity tools show agency-specific actions
- bulk tools work through shared interview APIs
- quick tools work through navigation shortcuts and fast action handlers
- reminders are visible in reminder center
- shared layout remains consistent
- no console crash during build validation
- no backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
