# ICC Live Interview Center 01

Date: 2026-04-01
Module ID: `ICC-LIVE-INTERVIEW-CENTER-01`

## Placement

Validated under:

- `Interview Command Center -> Live Interviews`

## Implemented

- Live Interview List
  - candidate
  - interview type
  - stage
  - interviewer
  - status
  - time
- Live Interview Room
  - AI interview execution shell
  - human interview tracking
  - technical interview execution shell
  - assessment execution shell
- Interview Panel
  - candidate profile
  - job details
  - stage details
  - interview instructions
  - question/task flow from interview kit
- Interview Controls
  - start interview
  - pause
  - resume
  - end interview
- Evaluation Panel
  - scorecard fill from mapped scorecard attributes
  - notes
  - recommendation
  - structured feedback submit
- Decision Panel
  - manual decision
  - auto evaluate shell
  - decision notes
- Real Time Status
  - ongoing interviews
  - waiting candidates
  - completed interviews

## Integration

Live center uses existing interview services and aligns with:

- Scheduling Engine
- Interview Engines
- Scorecard Engine
- Automation Engine
- Decision Engine

## Validation

Checked:

- live list loads
- interview open works by selecting row
- interview kit context loads
- start works
- pause works
- resume works
- end works
- evaluation submit works through structured feedback API
- decision save works through decision APIs
- status summary updates after actions
- no route conflict introduced
- no console-blocking build error

## Notes

- Pause and resume currently use the existing interview status update path because there is no dedicated realtime session endpoint in the current interview API.
- The live room is an enterprise execution shell over the existing interview, kit, scorecard, and decision services, not a separate video runtime implementation.

## Build Result

- `npx vite build` passed
