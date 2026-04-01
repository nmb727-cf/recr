# ICC-SCORECARD-REPOSITION-01 QA

## Scope

Validated Scorecard Engine repositioning to:

- Interview Command Center
- Scorecards

## Checks

- Scorecards are visible as a separate Interview Command Center menu item.
- Registry no longer contains the Scorecards entry.
- Route `/interviews/scorecards` remains valid and loads the scorecard workspace.
- Legacy route `/interviews/types/scorecards` redirects to `/interviews/scorecards`.
- Scorecard builder remains accessible for create and edit flows.
- Scorecard preview remains accessible.
- Existing scorecard integrations with AI interviews remain intact because linked scorecard template ids and API calls are unchanged.
- No route conflict introduced.
- No console crash introduced.
- No backend 500 introduced.

## Validation

- Frontend production build completed successfully with `npx vite build`.

## Result

Scorecard Engine is now positioned as a separate reusable system under Interview Command Center while keeping routing, builder behavior, and integrations intact.
