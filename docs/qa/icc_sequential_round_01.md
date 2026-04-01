# ICC-SEQUENTIAL-ROUND-ENGINE-01

## Scope

Built a dedicated Sequential Round Interview Engine under:

- `Interview Command Center -> Registry -> Sequential Round`

Primary files:

- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewSequentialRoundEngine.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewTypes.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewCommandCenter.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/App.tsx`

## What Was Implemented

### List Page

- Sequential round interview template list
- Columns:
  - Interview Name
  - Type
  - Total Rounds
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
   - Description
   - Total Rounds
   - Duration Summary
2. Round Structure
   - Add round
   - Round name
   - Round order
   - Round duration
   - Round type
   - Round objective
   - Round reorder and remove
3. Per Round Configuration
   - Question / topic flow
   - Interviewer guidance
   - Scorecard mapping
   - Mandatory / optional round
   - Pass / reject / review rule
4. Progression Logic
   - Move to next round
   - Reject after round
   - Manual review between rounds
   - Skip round shell
5. Usage / Preview
   - Round flow summary
   - Linked jobs
   - Linked flows
   - Linked stages

## Integration

- Template persistence via `interviewsApi.listTemplates/createTemplate/updateTemplate`
- Scorecard mapping via `interviewsApi.listScorecards`
- Usage visibility via `interviewsApi.listFlows`
- Registry route mapping for `sequential_round`
- Direct routes:
  - `/interviews/sequential-round`
  - `/interviews/types/sequential-round`

## Embedded QA

### Checked

- Sequential round create flow loads
- Round add works
- Round reorder works
- Per-round config fields render and update
- Scorecard mapping UI works
- Preview opens and reflects round flow
- Registry item routes to sequential round engine
- No dashboard fallback
- No console crash in build validation
- No backend 500 in the implemented frontend integration path

### Result

- `sequential_round` is now mapped as `Built`
- Registry opens the correct dedicated engine
- Build passed successfully with Vite

## Notes

- The engine persists through the shared template model using `metadata.sequential_round`.
- Linked jobs come from template usage metadata, while linked flows and stages are derived from current flow stage usage.
