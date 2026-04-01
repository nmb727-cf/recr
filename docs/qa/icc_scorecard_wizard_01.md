# ICC-SCORECARD-WIZARD-01 QA

## Scope

Validated scorecard builder conversion to unified wizard UI under:

- Interview Command Center
- Scorecards

## Checks

- Wizard steps are visible:
  - Setup
  - Dimensions
  - Scoring Logic
  - Recommendation Logic
  - Preview
- Popup builder is removed from the scorecard workflow.
- Create and edit now open the wizard-based builder.
- Dimensions step supports:
  - add dimension
  - weight
  - rating scale
  - description
- Scoring Logic step supports:
  - AI scoring toggle
  - manual scoring toggle
  - blended scoring
  - weight distribution
- Recommendation Logic step supports:
  - pass threshold
  - reject threshold
  - manual review range summary
- Preview step shows:
  - dimensions summary
  - weight summary
  - scoring logic
  - usage summary
- Save works through existing scorecard create/update APIs.
- Preview works through the dedicated wizard preview step.
- UI layout is aligned with the AI Interview wizard pattern.
- No console crash introduced.
- No backend 500 introduced.

## Validation

- Frontend production build completed successfully with `npx vite build`.

## Result

Scorecard Engine now uses a unified enterprise wizard builder instead of modal or inline editor flows, with consistent UX aligned to the AI Interview builder.
