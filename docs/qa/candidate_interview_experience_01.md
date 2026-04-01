# Candidate Interview Experience QA

Module ID: `CANDIDATE-INTERVIEW-EXPERIENCE-01`

## Scope

Built unified candidate interview experience layer under:

- Candidate Portal
- Interviews
- Experience

## Files Updated

- `frontend/src/pages/candidate/CandidateInterviewExperience.tsx`
- `frontend/src/pages/candidate/CandidateInterviewDashboard.tsx`
- `frontend/src/App.tsx`

## Data Sources Used

- `interviewsApi.candidateList()`
- `notificationsApi.list()`
- `useAuthStore()` for user timezone
- browser/device context via `Intl.DateTimeFormat` and `navigator.userAgent`

## Features Added

### Interview Progress Indicator

Shows:

- progress bar
- stage completion
- next step

### Smart Reminders

Shows:

- upcoming interview alerts
- preparation reminders
- schedule reminders

### Candidate Confidence Indicators

Shows:

- readiness status
- preparation completion
- checklist progress

### Quick Actions

Allows:

- join interview
- reschedule
- view instructions
- contact support

### Experience Summary

Shows:

- interview history
- progress summary
- current stage

### Personalization

Supports:

- timezone awareness
- device detection
- accessibility preference visibility

## Integration Coverage

Connected to:

- Candidate Dashboard
- Timeline
- Preparation Center
- Notification System
- Help Center

## Embedded QA Checks

- experience page loads
- progress shows
- reminders show
- quick actions work
- no console crash during build validation
- no backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
