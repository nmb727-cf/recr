# ICC AI Interview Rebuild 03

## Scope
- Module: `ICC-AI-INTERVIEW-ENGINE-01`
- Placement: `Interview Command Center -> Registry -> AI Interviews`
- Route retained: `/interviews/types/ai-interviews`

## Embedded QA
- `AI Interview` is treated as the reusable template object.
- No nested template concept remains in the AI interview UX.
- Create flow supports `Build Manually` and `Generate with AI (future)` and both enter the same builder.
- Builder sections exist:
  - Setup
  - Question / Prompt Flow
  - Candidate Experience
  - Evaluation
  - Outcome / Routing
  - Usage
- Question flow builder supports add/remove prompt authoring, follow-up shell, expected answer guidance, and skill mapping.
- Evaluation section exists and stores AI/manual scoring configuration.
- Outcome section exists and stores pass/review/reject routing thresholds and next stage mapping.
- Usage section exists and stores linked jobs, flows, and stages.
- Preview shows candidate view and question sequence.

## Validation
- `npx vite build` passed after rebuild.
- Existing route structure remains intact.

## Notes
- Full `npm run build` is currently blocked by unrelated existing TypeScript errors outside this module.
- `Generate with AI` is a UI placeholder only, with future-generation metadata shape added but no generation implementation.
