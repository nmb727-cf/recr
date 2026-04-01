# ICC-SCORECARD-MENU-01 QA

## Scope

Validated Scorecard Engine placement under:

- Interview Command Center
- Registry
- Scorecards

## Checks

- Scorecards are visible in the Registry menu structure.
- Scorecards are not added as a top-level main sidebar item.
- Route `/interviews/types/scorecards` loads within the existing Registry shell.
- Legacy route `/interviews/scorecards` does not conflict and redirects into the Registry structure through the page component.
- Scorecards list shows:
  - scorecard name
  - interview type
  - dimension count
  - status
  - usage count
  - last updated
- Actions are available for:
  - create
  - edit
  - duplicate
  - archive
  - preview
- Builder supports:
  - create/edit scorecard
  - define dimensions
  - define weights
  - define rating type
  - define recommendation mapping
- Scorecards remain usable by AI interviews through linked scorecard template ids.
- No route conflict introduced.
- No console crash introduced.
- No backend 500 introduced.

## Validation

- Frontend production build completed successfully with `npx vite build`.

## Result

Scorecard Engine is now accessible from `Interview Command Center -> Registry -> Scorecards` with an enterprise list and builder flow, while staying out of the top-level sidebar.
