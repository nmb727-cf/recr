# ICC-ROLE-PLAY-ENGINE-01

## Scope

Built a dedicated Role Play Interview Engine under:

- `Interview Command Center -> Registry -> Role Play`

Primary files:

- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewRolePlayEngine.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewTypes.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewCommandCenter.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/App.tsx`

## What Was Implemented

### List Page

- Role play template list
- Columns:
  - Interview Name
  - Type
  - Scenario Type
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
   - Scenario Type
   - Duration
   - Description
2. Scenario Builder
   - Scenario description
   - Role instructions
   - Candidate role
   - Interviewer role
   - Expected objectives
3. Evaluation Focus
   - Communication
   - Problem solving
   - Negotiation
   - Empathy
   - Leadership
4. Evaluation Model
   - Scorecard mapping
   - Pass threshold
   - Reject threshold
   - Recommendation logic
5. Usage / Preview
   - Linked jobs
   - Linked flows
   - Preview summary

## Integration

- Template persistence via `interviewsApi.listTemplates/createTemplate/updateTemplate`
- Scorecard mapping via `interviewsApi.listScorecards`
- Usage visibility via `interviewsApi.listFlows`
- Registry route mapping for `role_play`
- Direct routes:
  - `/interviews/role-play`
  - `/interviews/types/role-play`

## Embedded QA

### Checked

- Role play create flow loads
- Scenario builder fields render and update
- Evaluation config fields render and update
- Preview opens and reflects setup and scenario roles
- Registry item routes to role play engine
- No dashboard fallback
- No console crash in build validation
- No backend 500 in the implemented frontend integration path

### Result

- `role_play` is now mapped as `Built`
- Registry opens the correct dedicated engine
- Build passed successfully with Vite

## Notes

- The engine persists through the shared template model using `metadata.role_play`.
- Linked jobs come from template usage metadata, while linked flows and stages are derived from current flow stage usage.
