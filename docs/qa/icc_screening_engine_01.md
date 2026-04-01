# ICC Screening Engine 01

Date: 2026-04-01
Module ID: `ICC-SCREENING-ENGINE-01`

## Placement

Validated under:

- `Interview Command Center -> Registry -> Screening Interviews`

Routes added:

- `/interviews/screening`
- `/interviews/types/screening-interviews`

## Implemented

- Dedicated screening engine page:
  - [InterviewScreeningEngine.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewScreeningEngine.tsx)
- Supported screening types:
  - `recruiter_screening`
  - `phone_interview`
- Screening list page
  - Interview Name
  - Type
  - Duration
  - Status
  - Usage Count
  - Last Updated
  - Create / Edit / Duplicate / Archive / Preview
- Screening wizard
  - Step 1: Setup
  - Step 2: Question Flow
  - Step 3: Evaluation
  - Step 4: Routing
  - Step 5: Preview

## Integration

Connected to:

- Flow Engine
- Scorecard Engine
- Scheduling Engine
- Question Bank

## Registry Fixes Included

- `recruiter_screening` now routes to the screening engine instead of opening prequalification.
- `phone_interview` now routes to the screening engine instead of opening prequalification.
- Registry shell now includes a `Screening Interviews` tab under Type Registry.

## Validation

Checked:

- recruiter screening route opens screening engine
- phone interview route opens screening engine
- setup step visible
- question flow supports attach and custom add
- evaluation supports scorecard and thresholds
- routing step visible
- no console-blocking build error
- no route conflict introduced

## Build Result

- `npx vite build` passed
