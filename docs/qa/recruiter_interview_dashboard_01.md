# Recruiter Interview Dashboard QA

Module ID: `RECRUITER-INTERVIEW-DASHBOARD-01`

## Scope

Built a shared recruiter interview dashboard engine under:

- Recruiter Workspace
- Interviews
- Dashboard

Available to both:

- company recruiter workspace
- agency recruiter workspace

## Files Updated

- `frontend/src/pages/interviews/RecruiterInterviewDashboard.tsx`
- `frontend/src/App.tsx`

## Shared Engine Design

One dashboard engine is used for both workspaces.

Workspace logic is selected from authenticated role:

- Company roles:
  - `tenant_admin`
  - `recruiter`
  - `hiring_manager`
- Agency roles:
  - `agency_owner`
  - `agency_admin`
  - `agency_recruiter`

Shared layout remains consistent across both sides:

- filters header
- status summary cards
- today’s interviews
- upcoming interviews
- pending action area
- quick actions
- recent activity

## Data Source Used

- `interviewsApi.list()`

Derived values are read from interview fields and metadata where available:

- `job_title`
- `interview_type`
- `interviewers`
- `scheduled_at`
- `status`
- `metadata.department`
- `metadata.hiring_manager`
- `metadata.client_company`
- `metadata.recruiter_name`
- `metadata.candidate_owner`
- `metadata.stage_name`

## Company Workspace Coverage

### Sections

- Today’s Interviews
- Upcoming Interviews
- Pending Internal Actions
- Upcoming Final / High Priority Rounds
- Job-wise Interview Load
- Recruiter Quick Actions
- Shared Pending Actions
- Recent Activity

### Company Filters

- job
- department
- hiring manager
- interviewer
- interview type
- status
- date

### Company Actions

- schedule interview
- assign interviewer / panel
- send reminder
- request feedback
- move to next round
- finalize decision

## Agency Workspace Coverage

### Sections

- Today’s Interviews
- Upcoming Interviews
- Recruiter Screening Queue
- Client Interview Coordination
- Candidate Follow-up Actions
- Recruiter Quick Actions
- Client-wise Interview Load
- Recent Activity

### Agency Filters

- client company
- client job
- recruiter
- candidate owner
- interview type
- status
- date

### Agency Actions

- schedule recruiter screen
- coordinate client interview
- send candidate reminder
- follow up with client
- update candidate status
- reschedule interview

## Embedded QA Checks

- company dashboard shows company-specific sections and terminology
- agency dashboard shows agency-specific sections and terminology
- filters differ correctly by workspace
- quick actions differ correctly by workspace
- shared visual layout remains consistent
- no console crash during build validation
- no backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
