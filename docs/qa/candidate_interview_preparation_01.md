# Candidate Interview Preparation QA

Module ID: `CANDIDATE-INTERVIEW-PREPARATION-01`

## Scope

Built candidate-side preparation center under:

- Candidate Portal
- Interviews
- Preparation

## Files Updated

- `frontend/src/pages/candidate/CandidateInterviewPreparation.tsx`
- `frontend/src/pages/candidate/CandidateInterviewDashboard.tsx`
- `frontend/src/App.tsx`

## Data Sources Used

- `interviewsApi.candidateList()`
- `interviewsApi.candidateInstructions(id)`

## Sections Added

### Upcoming Interview Preparation

Shows:

- interview name
- interview type
- scheduled date
- preparation tips

### Interview Guidelines

Shows:

- instructions
- requirements
- interview format
- expected duration

### Preparation Materials

Supports:

- documents
- links
- videos (future ready state)
- sample questions when attached in interview metadata

### System Check

Supports candidate-side readiness shells for:

- mic check
- camera check
- internet check
- device check

### Candidate Checklist

Shows:

- preparation checklist
- readiness indicator

## Integration Coverage

Connected to:

- Interview Engines through candidate instructions and runtime links
- Scheduling Engine through self-schedule links
- Candidate Dashboard through direct entry buttons
- Notification System indirectly through the same upcoming interview data surface

## Embedded QA Checks

- preparation page loads
- interview info shows
- checklist works
- system check loads
- no console crash during build validation
- no backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
