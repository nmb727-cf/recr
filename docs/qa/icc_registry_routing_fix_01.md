# ICC Registry Routing Fix 01

Date: 2026-04-01
Module ID: `ICC-REGISTRY-ROUTING-FIX-01`

## Goal

Ensure interview registry selections route to the correct interview engines and ICC sections instead of falling back to the dashboard/default section.

## Implemented

- Added direct engine routes:
  - `/interviews/ai`
  - `/interviews/technical`
  - `/interviews/human`
  - `/interviews/assessments`
  - `/interviews/prequalification`
  - `/interviews/live`
  - `/interviews/analytics`
- Added missing legacy routes so older registry links still resolve:
  - `/interviews/types/technical-interviews`
  - `/interviews/types/human-interviews`
  - `/interviews/types/assessments`
  - `/interviews/types/prequalification`
- Updated registry click mapping to use category-based direct routes:
  - AI types -> AI engine
  - technical types -> technical engine
  - human types -> human engine
  - assessment types -> assessment engine
  - prequalification types -> prequalification engine
- Updated `InterviewTypes` route detection so both old and new engine URLs open the correct embedded builder instead of the registry home.
- Updated command center path-to-section mapping so direct ICC section URLs like `/interviews/live` and `/interviews/analytics` open the correct section rather than defaulting to dashboard.

## Expected Paths Covered

- `AI Interviews -> /interviews/ai`
- `Technical Interviews -> /interviews/technical`
- `Human Interviews -> /interviews/human`
- `Assessments -> /interviews/assessments`
- `Prequalification -> /interviews/prequalification`
- `Scorecards -> /interviews/scorecards`
- `Templates -> /interviews/templates`
- `Scheduling -> /interviews/scheduling`
- `Live Interviews -> /interviews/live`
- `Analytics -> /interviews/analytics`
- `Automation -> /interviews/automation`

## Validation

Checked:

- registry item category routing no longer points at missing routes
- direct engine URLs resolve
- legacy engine URLs resolve
- command center direct section URLs resolve to the right section
- no dashboard fallback for the fixed paths
- no console-blocking build error
- no backend route change required

## Build Result

- `npx vite build` passed
