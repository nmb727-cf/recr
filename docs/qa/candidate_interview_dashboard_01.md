# Candidate Interview Dashboard QA

Module ID: `CANDIDATE-INTERVIEW-DASHBOARD-01`

## Scope

Expanded the existing candidate interviews page into a full dashboard under:

- Candidate Portal
- Interviews

## Updated File

- `frontend/src/pages/candidate/CandidateInterviewDashboard.tsx`

## Data Sources Used

- `interviewsApi.candidateList()` for upcoming, pending, completed, and missed interview buckets
- `notificationsApi.list()` for interview-related notifications

## Dashboard Sections

### Upcoming Interviews

Shows:

- Interview name
- Type
- Date
- Time
- Status
- Join action

### Pending Interviews

Shows:

- Interviews waiting for candidate action
- In-progress resume state
- Details and reschedule actions where available

### Completed Interviews

Shows:

- Completed interviews
- Status
- Result or decision when available in candidate response payload

### Interview Notifications

Shows:

- Schedule updates
- Reminders
- Decisions

### Quick Actions

Allows:

- Join Interview
- View Details
- Reschedule when a scheduling token/link exists

## Integration Coverage

Connected to:

- Scheduling Engine through available self-scheduling token/link fields
- Candidate interview runtime/instructions/status routes
- Candidate Portal navigation
- Notification System

## Embedded QA Checks

- Dashboard loads
- Interviews appear from candidate interview API
- Join works through existing runtime route
- No console crash during build validation
- No backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
