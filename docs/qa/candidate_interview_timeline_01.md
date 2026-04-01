# Candidate Interview Timeline QA

Module ID: `CANDIDATE-INTERVIEW-TIMELINE-01`

## Scope

Built candidate-side interview timeline under:

- Candidate Portal
- Interviews
- Timeline

## Files Updated

- `frontend/src/pages/candidate/CandidateInterviewTimeline.tsx`
- `frontend/src/pages/candidate/CandidateInterviewDashboard.tsx`
- `frontend/src/App.tsx`

## Data Source Used

- `interviewsApi.candidateList()`

## Timeline Coverage

Shows:

- interview stages
- stage status
- stage dates
- stage results

Timeline order is derived from:

- `interview_round`
- `scheduled_at`
- interview metadata such as `stage_name`, `flow_stage`, and `round_name`

## Status Types Supported

- completed
- scheduled
- upcoming
- in progress
- skipped
- cancelled

## Stage Details Visible

- stage name
- interview type
- date
- duration
- instructions access
- status

## Candidate Actions

- view stage details
- join interview
- schedule / reschedule interview
- view results

## Current Progress

Highlights:

- current stage
- next stage

## Integration Coverage

Connected to:

- Interview Flow data where stage metadata is available
- Scheduling Engine through self-schedule links
- Candidate Dashboard through direct entry buttons
- Interview Engines through runtime and instructions routes

## Embedded QA Checks

- timeline loads
- stages display correctly from current candidate interview feed
- status updates render correctly
- actions work
- no console crash during build validation
- no backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
