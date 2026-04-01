# Candidate Interview Notification QA

Module ID: `CANDIDATE-INTERVIEW-NOTIFICATION-01`

## Scope

Built candidate-side interview notifications under:

- Candidate Portal
- Interviews
- Notifications

## Files Updated

- `frontend/src/pages/candidate/CandidateInterviewNotifications.tsx`
- `frontend/src/pages/candidate/CandidateInterviewDashboard.tsx`
- `frontend/src/App.tsx`

## Data Sources Used

- `interviewsApi.candidateList()`
- `notificationsApi.list()`
- `notificationsApi.markRead()`
- `notificationsApi.markAllRead()`

## Notification Types Covered

- interview scheduled
- interview rescheduled
- reminder
- interview starting soon
- interview completed
- next round invitation
- decision update

## Notification Channels

- in-app notification: live
- email: future-ready UI state
- SMS: future-ready UI state
- push notification: future-ready UI state

## Sections Added

### Upcoming Reminders

Shows:

- upcoming interviews
- reminder time
- quick join

### Updates

Shows:

- reschedule updates
- new interview invitation
- cancellation / next round / decision updates

### History

Shows:

- notification history
- interview-related alerts

## Candidate Actions

- join interview
- confirm schedule
- reschedule request
- view interview

## Integration Coverage

Connected to:

- Scheduling Engine through self-schedule links
- Candidate Dashboard through direct navigation entry
- Interview Engines through runtime and instructions routes
- Notification System through interview notification feed and read-state actions

## Embedded QA Checks

- notifications load
- reminders appear
- join / confirm / reschedule / view actions work
- no console crash during build validation
- no backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
