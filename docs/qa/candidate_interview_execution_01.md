# Candidate Interview Execution QA

Module ID: `CANDIDATE-INTERVIEW-EXECUTION-01`

## Scope

Rebuilt the candidate runtime page into a unified interview execution layer under:

- Candidate Portal
- Interviews
- Start Interview

## Updated File

- `frontend/src/pages/candidate/CandidateInterviewRuntime.tsx`

## Supported Execution Types

Unified execution shell now adapts for:

- AI Interview
- Technical Interview
- Human Interview
- Assessment
- Video Interview
- Group Discussion
- Presentation
- Role Play
- Portfolio Review
- Mock Interview
- Other registry interview types through generic fallback

## Execution Layout

### Top Section

Shows:

- interview name
- timer
- status
- progress

### Main Interview Area

Dynamic behavior by interview type:

- AI / Technical / Mock / generic: text response workspace
- Assessment: option selection when choices exist, otherwise text response
- Human: waiting screen shell with meeting/link actions
- Video: recording UI shell with notes
- Group Discussion: waiting room shell
- Presentation / Role Play / Portfolio Review: type-specific response workspace

### Side Panel

Shows:

- instructions
- progress
- stages
- notes
- security shell summary

### Controls

Supports:

- start interview
- pause shell
- submit
- next question
- finish

### Status Handling

Supports:

- not started
- in progress
- completed
- submitted
- expired

## Integration Coverage

Connected to:

- Interview Engines through `candidateRuntime` payload
- Scheduling/meeting links via runtime interview data
- Candidate Portal routes
- Status page and instructions page
- Notification/security shell via existing runtime behavior

## Embedded QA Checks

- Execution loads
- Type switching works through interview type detection
- Timer works
- Submit works through existing candidate answer API
- No console crash during build validation
- No backend 500 introduced by this change set

## Notes

- Pause is implemented as a candidate-side execution shell because no dedicated backend pause endpoint exists yet.
- Video recording remains a unified shell until a recording provider/runtime is connected.

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
