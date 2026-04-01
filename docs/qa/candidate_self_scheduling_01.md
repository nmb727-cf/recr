# Candidate Self Scheduling QA

Module ID: `CANDIDATE-SELF-SCHEDULING-01`

## Scope

Expanded the existing candidate self-scheduling page under:

- Candidate Portal
- Interviews
- Schedule / Reschedule

## Updated File

- `frontend/src/pages/interviews/CandidateSelfSchedule.tsx`

## Data Sources Used

- `interviewsApi.getPublicSchedulingLink(token)` for available slots and interview details
- `interviewsApi.bookPublicSchedulingLink(token, data)` for slot confirmation and reschedule
- `interviewsApi.cancelInterviewFlex(interviewId, data)` for candidate cancellation request when authenticated candidate access is available

## Functional Coverage

### Available Slots

Shows:

- available dates
- available time slots
- timezone display

### Candidate Actions

Allows:

- select slot
- confirm slot
- reschedule
- cancel request

### Scheduling Modes

Surface logic supports:

- recruiter defined slots
- system generated slots
- panel availability slots

### Confirmation

Shows:

- selected slot
- interviewer when available
- interview type
- confirmation button

### Notifications

Communicates:

- schedule confirmation
- reschedule notification
- reminder flow

### Status Handling

Supports:

- scheduled
- rescheduled
- cancelled
- pending

## Integration Coverage

Connected to:

- Scheduling Engine
- Candidate interview portal
- Candidate dashboard reschedule path
- Notification workflow through scheduling events

## Embedded QA Checks

- Slots load
- Slot selection works
- Reschedule works through scheduling-link booking flow
- Confirmation works
- No console crash during build validation
- No backend 500 introduced by this change set

## Notes

- Public scheduling link API already supports slot booking and repeated booking for reschedule scenarios when the link remains active.
- Cancellation uses the existing interview cancel-flex endpoint and depends on authenticated candidate access when invoked from the candidate portal.

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
