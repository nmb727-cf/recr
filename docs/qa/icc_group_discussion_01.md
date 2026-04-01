# ICC-GROUP-DISCUSSION-ENGINE-01

## Scope

Built a dedicated Group Discussion Interview Engine under:

- `Interview Command Center -> Registry -> Group Discussion`

Primary files:

- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewGroupDiscussionEngine.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewTypes.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewCommandCenter.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/App.tsx`

## What Was Implemented

### List Page

- Group discussion template list
- Columns:
  - Discussion Name
  - Type
  - Participants Count
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
   - Discussion Name
   - Role / Domain
   - Description
   - Duration
   - Max Participants
2. Discussion Structure
   - Topic selection
   - Discussion instructions
   - Evaluation focus areas
   - Discussion guidelines
3. Evaluation Model
   - Individual scoring
   - Group scoring
   - Evaluator notes
   - Scorecard mapping
4. Participant Handling
   - Multiple candidates
   - Multiple evaluators
   - Participant limit
5. Usage / Preview
   - Linked jobs
   - Linked flows
   - Preview summary

## Integration

- Template persistence via `interviewsApi.listTemplates/createTemplate/updateTemplate`
- Scorecard mapping via `interviewsApi.listScorecards`
- Usage visibility via `interviewsApi.listFlows`
- Registry route mapping for `group_discussion`
- Direct routes:
  - `/interviews/group-discussion`
  - `/interviews/types/group-discussion`

## Embedded QA

### Checked

- Group discussion create flow loads
- Multi-candidate config fields render and update
- Evaluation model fields render and update
- Preview opens and reflects setup and topics
- Registry item routes to group discussion engine
- No dashboard fallback
- No console crash in build validation
- No backend 500 in the implemented frontend integration path

### Result

- `group_discussion` is now mapped as `Built`
- Registry opens the correct dedicated engine
- Build passed successfully with Vite

## Notes

- The engine persists through the shared template model using `metadata.group_discussion`.
- Linked jobs come from template usage metadata, while linked flows and stages are derived from current flow stage usage.
