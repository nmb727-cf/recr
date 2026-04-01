# ICC-BAR-RAISER-ENGINE-01

## Scope

Built a dedicated Bar Raiser Interview Engine under:

- `Interview Command Center -> Registry -> Bar Raiser`

Primary files:

- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewBarRaiserEngine.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewTypes.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewCommandCenter.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/App.tsx`

## What Was Implemented

### List Page

- Bar raiser template list
- Columns:
  - Interview Name
  - Type
  - Level
  - Duration
  - Status
  - Usage Count
  - Last Updated
- Actions:
  - Create
  - Edit
  - Duplicate
  - Archive
  - Preview

### Wizard

Implemented 5-step builder:

1. Setup
   - Interview Name
   - Role / Domain
   - Seniority Level
   - Duration
   - Description
2. Evaluation Focus
   - Leadership evaluation
   - Decision making
   - Ownership
   - Technical depth
   - Culture impact
3. Interview Structure
   - Discussion topics
   - Evaluation prompts
   - Interviewer guidance
   - Expected outcomes
4. Evaluation Model
   - Scorecard mapping
   - Hire / no hire logic
   - Strong hire / hire / no hire scale
   - Final recommendation
5. Usage / Preview
   - Linked jobs
   - Linked flows
   - Preview summary

## Integration

- Template persistence via `interviewsApi.listTemplates/createTemplate/updateTemplate`
- Scorecard mapping via `interviewsApi.listScorecards`
- Usage visibility via `interviewsApi.listFlows`
- Registry route mapping for `bar_raiser`
- Direct routes:
  - `/interviews/bar-raiser`
  - `/interviews/types/bar-raiser`

## Embedded QA

### Checked

- Bar raiser create flow loads
- Evaluation focus configuration works
- Scorecard mapping UI works
- Preview opens and reflects structure and recommendation model
- Registry item routes to bar raiser engine
- No dashboard fallback
- No console crash in build validation
- No backend 500 in the implemented frontend integration path

### Result

- `bar_raiser` is now mapped as `Built`
- Registry opens the correct dedicated engine
- Build passed successfully with Vite

## Notes

- The engine persists through the shared template model using `metadata.bar_raiser`.
- Linked jobs come from template usage metadata, while linked flows and stages are derived from current flow stage usage.
