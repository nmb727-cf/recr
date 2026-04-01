# ICC-PORTFOLIO-REVIEW-ENGINE-01

## Scope

Built a dedicated Portfolio Review Interview Engine under:

- `Interview Command Center -> Registry -> Portfolio Review`

Primary files:

- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewPortfolioReviewEngine.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewTypes.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewCommandCenter.tsx`
- `/home/nirav/projects/SaaS_Project/frontend/src/App.tsx`

## What Was Implemented

### List Page

- Portfolio review template list
- Columns:
  - Interview Name
  - Type
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
   - Duration
   - Description
2. Portfolio Configuration
   - Portfolio submission instructions
   - Portfolio types allowed
   - Link upload
   - File upload
   - Project discussion structure
3. Evaluation Focus
   - Project quality
   - Problem solving
   - Creativity
   - Technical depth
   - Ownership
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
- Registry route mapping for `portfolio_review`
- Direct routes:
  - `/interviews/portfolio-review`
  - `/interviews/types/portfolio-review`

## Embedded QA

### Checked

- Portfolio review create flow loads
- Portfolio configuration fields render and update
- Evaluation config fields render and update
- Preview opens and reflects portfolio settings
- Registry item routes to portfolio review engine
- No dashboard fallback
- No console crash in build validation
- No backend 500 in the implemented frontend integration path

### Result

- `portfolio_review` is now mapped as `Built`
- Registry opens the correct dedicated engine
- Build passed successfully with Vite

## Notes

- The engine persists through the shared template model using `metadata.portfolio_review`.
- Linked jobs come from template usage metadata, while linked flows and stages are derived from current flow stage usage.
