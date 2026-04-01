# ICC Walk-in Drive Engine QA

Module ID: `ICC-WALKIN-DRIVE-ENGINE-01`

## Scope

Built a dedicated Walk-in Drive engine under:

- Interview Command Center
- Registry
- Walk-in Drive

## What Was Added

- Dedicated engine page: `frontend/src/pages/interviews/InterviewWalkinDriveEngine.tsx`
- Registry embedding and navigation wiring in `frontend/src/pages/interviews/InterviewTypes.tsx`
- Registry route mapping in `frontend/src/pages/interviews/InterviewCommandCenter.tsx`
- Direct and embedded routes in `frontend/src/App.tsx`

## Functional Coverage

### List Page

Visible columns:

- Drive Name
- Role / Domain
- Date
- Location / Mode
- Status
- Candidate Count
- Last Updated

Actions available:

- Create
- Edit
- Duplicate
- Archive
- Preview

### Wizard

#### Step 1 — Setup

- Drive Name
- Role / Domain
- Date
- Mode
- Location
- Description

#### Step 2 — Interview Flow

- Add stage
- Stage order
- Stage type selection
- Evaluator assignment
- Reorder stages
- Remove stages

#### Step 3 — Candidate Handling

- Bulk candidate entry
- Queue management
- Batch handling
- Capacity per slot

#### Step 4 — Evaluation

- Scorecard mapping
- Stage level evaluation
- Pass logic
- Reject logic

#### Step 5 — Usage / Preview

- Stage flow summary
- Linked jobs summary
- Linked flows summary
- Drive overview

## Integration Coverage

Connected as metadata and UI shell to:

- Scheduling Engine
- Scorecard Engine
- Flow Engine
- Decision Engine

## Embedded QA Checks

- Walk-in drive create works
- Stage builder works
- Candidate queue config works
- Evaluation config works
- Preview works
- No console crash during build validation
- No backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
