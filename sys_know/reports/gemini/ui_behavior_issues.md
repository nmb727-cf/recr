# UI Behavior Issues

## Missing Loading States
Many forms across `src/pages/candidates/` and `src/pages/jobs/` lack explicit loading overlays during submit, potentially allowing double submissions.

## Unwired Buttons
Several buttons in `src/pages/dashboard/Dashboard.tsx` may lack `onClick` handlers wired to real API calls.
