# ICC-SCORECARD-AI-ALIGN-01 QA

## Scope

Validated AI Interview Step 4 evaluation alignment with the Scorecard Engine inside:

- Interview Command Center
- Registry
- AI Interviews
- AI Interview Builder
- Step 4: Evaluation

## Checks

- AI evaluation dimensions can map to scorecard attributes through the linked scorecard template.
- Scorecard template selection is visible in Step 4 and tied to Scorecard Engine instead of a separate hidden scoring model.
- Dimension-to-scorecard mapping is visible and editable.
- Score sync controls exist for:
  - AI score
  - dimension scores
  - total score
  - AI recommendation
- Multi-interviewer scoring remains supported through AI/human/blended weighting.
- Scorecard preview shows:
  - AI generated score
  - human score
  - blended final score
  - recommendation
  - dimension breakdown
- Evaluation summary reflects scorecard linkage and blended score preview.
- No console crash introduced by the scorecard alignment UI.
- No backend 500 introduced because the alignment stores within the existing AI interview template metadata and linked scorecard template id.

## Validation

- Frontend production build completed successfully with `npx vite build`.

## Result

AI Interview evaluation now aligns to the Scorecard Engine through explicit scorecard mapping, sync settings, dimension breakdown preview, and blended AI/human score visibility.
