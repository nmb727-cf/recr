# ICC Mock Interview Engine QA

Module ID: `ICC-MOCK-INTERVIEW-ENGINE-01`

## Scope

Built a dedicated Mock Interview engine under:

- Interview Command Center
- Registry
- Mock Interview

## What Was Added

- Dedicated engine page: `frontend/src/pages/interviews/InterviewMockEngine.tsx`
- Registry embedding and navigation wiring in `frontend/src/pages/interviews/InterviewTypes.tsx`
- Registry route mapping in `frontend/src/pages/interviews/InterviewCommandCenter.tsx`
- Direct and embedded routes in `frontend/src/App.tsx`

## Functional Coverage

### List Page

Visible columns:

- Interview Name
- Type
- Role / Domain
- Duration
- Status
- Usage Count
- Last Updated

Actions available:

- Create
- Edit
- Duplicate
- Archive
- Preview

### Wizard

#### Step 1 — Setup

- Interview Name
- Role / Domain
- Interview Type
- Duration
- Description

#### Step 2 — Interview Structure

- Topics to cover
- Question selection shell
- Difficulty level
- Evaluation focus

#### Step 3 — Feedback Model

- Feedback template
- Improvement suggestions
- Optional scoring
- Recommendation
- Scorecard mapping

#### Step 4 — Usage / Preview

- Preview summary
- Linked flows

## Integration Coverage

Connected as metadata and UI shell to:

- Scorecard Engine
- Question Engine
- Scheduling Engine
- Decision Engine

## Embedded QA Checks

- Mock interview create works
- Structure config works
- Feedback model works
- Preview works
- No console crash during build validation
- No backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
