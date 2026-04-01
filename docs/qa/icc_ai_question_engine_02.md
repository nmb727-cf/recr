# ICC AI Question Engine 02

## Scope
- Module: `ICC-AI-QUESTION-ENGINE-02`
- Placement: `Interview Command Center -> Registry -> AI Interviews -> Step 2`

## Embedded QA
- Step 2 visibly adapts based on AI interview type.
- Question cards support add, remove, duplicate, and reorder.
- Response mode changes visible fields:
  - video: preparation and duration guidance
  - audio: verbal and duration guidance
  - text: min/max length guidance
- Follow-up shell exists with enable toggle, objective, and trigger note.
- Expected answer guidance exists with poor-answer and keyword guidance.
- Evaluation dimensions and skill tags exist per question.
- Preview shows intro, type context, question count, question sequence, and response summary.

## Validation
- `npx vite build` passed after the Step 2 upgrade.
