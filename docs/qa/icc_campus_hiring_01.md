# ICC Campus Hiring Engine QA

Module ID: `ICC-CAMPUS-HIRING-ENGINE-01`

## Scope

Built a dedicated Campus Hiring engine under:

- Interview Command Center
- Registry
- Campus Hiring

## What Was Added

- Dedicated engine page: `frontend/src/pages/interviews/InterviewCampusHiringEngine.tsx`
- Registry embedding and navigation wiring in `frontend/src/pages/interviews/InterviewTypes.tsx`
- Registry route mapping in `frontend/src/pages/interviews/InterviewCommandCenter.tsx`
- Direct and embedded routes in `frontend/src/App.tsx`

## Functional Coverage

### List Page

Visible columns:

- Program Name
- University / Campus
- Role / Domain
- Date
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

- Program Name
- University / Campus
- Role / Domain
- Hiring Batch Size
- Date
- Mode
- Description

#### Step 2 — Hiring Flow

- Define stages
- Stage order
- Stage type selection
- Evaluator assignment
- Add / reorder / remove stages

#### Step 3 — Candidate Handling

- Bulk candidate upload
- College batch grouping
- Queue management
- Slot allocation

#### Step 4 — Evaluation

- Scorecard mapping
- Stage-level evaluation
- Pass logic
- Reject logic

#### Step 5 — Usage / Preview

- Program flow summary
- Linked jobs summary
- Program overview

## Integration Coverage

Connected as metadata and UI shell to:

- Scheduling Engine
- Scorecard Engine
- Flow Engine
- Decision Engine

## Embedded QA Checks

- Campus hiring create works
- Stage builder works
- Candidate batch config works
- Evaluation works
- Preview works
- No console crash during build validation
- No backend 500 introduced by this change set

## Validation

Build validation:

- `npx vite build`

Result:

- Passed
