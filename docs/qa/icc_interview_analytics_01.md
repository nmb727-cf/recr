# ICC Interview Analytics 01

Date: 2026-03-29
Module ID: `ICC-INTERVIEW-ANALYTICS-01`

## Placement

Validated under:

- `Interview Command Center -> Analytics`

## Implemented Analytics Sections

- Interview Volume
  - interviews per day
  - interviews per week
  - interviews per month
  - interviews by type
- Pass / Reject Metrics
  - pass rate
  - reject rate
  - pending decisions
  - hire rate
- Interview Type Performance
  - category-level success for AI, technical, human, assessment, and other mapped categories
- Interviewer Performance
  - interviewer activity
  - interviewer decision patterns
  - interviewer pass and reject rate
- Funnel Analytics
  - prequalification to interview
  - interview to offer
  - interview to reject
- Time Analytics
  - time to schedule
  - time to complete
  - time to decision
- Scorecard Analytics
  - dimension trends when dimension metadata is present
  - score distribution via scored interview table
  - candidate performance via ranked score table

## Filters And UI

Implemented:

- date range filter
- interview category filter
- day / week / month granularity selector
- metric cards
- bar-style charts
- interviewer performance table
- scorecard analytics table

## Integration Notes

Analytics uses existing ICC interview data and aligns with:

- Interview Engines
- Scorecard Engine
- Scheduling Engine
- Decision Engine

No new backend module was added. The analytics layer reads current interview records and available metadata.

## Validation

Checked:

- analytics section loads
- charts render
- date filter works
- category filter works
- daily / weekly / monthly switching works
- interviewer table renders
- scorecard analytics renders
- no console-blocking build error
- no route conflict introduced
- no backend API change required for this pass

## Real Vs Partial

Real:

- interview volume
- outcome metrics
- interviewer activity and decision patterning
- timing metrics
- type/category performance
- score table based on available interview scores

Partial / metadata-dependent:

- dimension trends require `metadata.scorecard_dimensions` or similar score breakdown on interview records
- funnel analytics uses currently available interview types and decisions, so it is directionally correct but not a dedicated funnel warehouse yet

## Build Result

- `npx vite build` passed
