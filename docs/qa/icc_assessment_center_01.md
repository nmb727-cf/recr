# ICC-ASSESSMENT-CENTER-ENGINE-01

## Scope

Built a dedicated Assessment Center Engine under:

- `Interview Command Center -> Registry -> Assessment Center`

Primary files:

- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewAssessmentCenterEngine.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewTypes.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewCommandCenter.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/App.tsx`

## What Was Implemented

### List Page

- Assessment center template list
- Columns:
  - Assessment Name
  - Type
  - Exercises Count
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
   - Assessment Name
   - Role / Domain
   - Duration
   - Description
2. Exercise Builder
   - Add exercise
   - Exercise type selection
   - Exercise duration
   - Exercise order
   - Exercise reorder and remove
3. Evaluation Model
   - Per exercise scoring
   - Overall scoring
   - Scorecard mapping
   - Pass threshold
4. Scheduling Model
   - Multi-session scheduling
   - Evaluator assignment
   - Candidate grouping
5. Usage / Preview
   - Exercise flow summary
   - Linked jobs
   - Linked flows

## Integration

- Template persistence via `interviewsApi.listTemplates/createTemplate/updateTemplate`
- Scorecard mapping via `interviewsApi.listScorecards`
- Usage visibility via `interviewsApi.listFlows`
- Registry route mapping for `assessment_center`
- Direct routes:
  - `/interviews/assessment-center`
  - `/interviews/types/assessment-center`

## Embedded QA

### Checked

- Assessment center create flow loads
- Exercise builder add and reorder work
- Evaluation config fields render and update
- Preview opens and reflects exercise flow
- Registry item routes to assessment center engine
- No dashboard fallback
- No console crash in build validation
- No backend 500 in the implemented frontend integration path

### Result

- `assessment_center` is now mapped as `Built`
- Registry opens the correct dedicated engine
- Build passed successfully with Vite

## Notes

- The engine persists through the shared template model using `metadata.assessment_center`.
- Linked jobs come from template usage metadata, while linked flows and stages are derived from current flow stage usage.
