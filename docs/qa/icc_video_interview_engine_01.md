# ICC Video Interview Engine 01

Date: 2026-04-01
Module ID: `ICC-VIDEO-INTERVIEW-ENGINE-01`

## Placement

Validated under:

- `Interview Command Center -> Registry -> Video Interviews`

Routes added:

- `/interviews/video`
- `/interviews/types/video-interviews`

## Implemented

- Dedicated video interview engine page:
  - [InterviewVideoEngine.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewVideoEngine.tsx)
- Supported video types:
  - `prerecorded_video`
  - `live_video`
- Video interview list page
  - Interview Name
  - Type
  - Duration
  - Status
  - Usage Count
  - Last Updated
  - Create / Edit / Duplicate / Archive / Preview
- Video wizard
  - Step 1: Setup
  - Step 2: Configuration
  - Step 3: Evaluation
  - Step 4: Routing

## Configuration Coverage

Prerecorded video:

- question recording shell
- response time limit
- retry options

Live video:

- interviewer selection
- live scheduling mode shell
- meeting integration shell

## Integration

Connected to:

- Scheduling Engine
- Integration Engine
- Scorecard Engine
- Flow Engine

## Registry Fixes Included

- `prerecorded_video` now routes to the dedicated video interview engine instead of AI reuse.
- `live_video` now routes to the dedicated video interview engine instead of generic type config.
- Registry shell now includes a `Video Interviews` tab under Type Registry.

## Validation

Checked:

- prerecorded video route opens video engine
- live video route opens video engine
- setup step visible
- prerecorded configuration fields visible
- live video configuration fields visible
- evaluation supports scorecard and thresholds
- routing step visible
- no console-blocking build error
- no route conflict introduced

## Build Result

- `npx vite build` passed
