# Company Phase 1 Completion

## Jobs
Status: Partial
Notes:
- Job create flow now uses the full shared company form (`frontend/src/pages/jobs/JobCreate.tsx` -> `JobCreateForm`) so ownership/hiring-team/workflow-related fields are available in one place.
- Job list/detail/status actions and requisition APIs are present and wired (`frontend/src/pages/jobs/JobsList.tsx`, `frontend/src/pages/jobs/JobDetail.tsx`, `frontend/src/api/jobs.ts`).
- Job detail header now resolves department/location names and hiring manager from org/job metadata instead of showing opaque IDs/static placeholders.
- Job detail Edit action now routes to setup page (`/jobs/:id/setup`) for real edit flow.
- Final pass still needed for end-to-end UI regression across create/edit/approval variants.

## Candidate Management
Status: Partial
Notes:
- Candidate list/database/detail pages are present and connected (`frontend/src/pages/candidates/CandidateDatabase.tsx`, `frontend/src/pages/candidates/CandidateDetail.tsx`, `frontend/src/api/candidates.ts`).
- Candidate detail profile rendering hardened to avoid invalid `NaN years` display when experience is missing.
- Candidate detail Notes tab now supports add-note creation flow (modal + validation + API submit) instead of a non-functional button.
- Candidate action completeness (note add/edit, status actions, bulk company actions) needs focused UX validation round.

## Pipeline
Status: Implemented
Notes:
- Pipeline board, stage transitions, and application movement flows are wired (`frontend/src/pages/pipeline/PipelineBoard.tsx`, `frontend/src/api/pipeline.ts`).
- Fixed broken offer action endpoint path by routing through `pipelineApi.makeOffer(...)` to the correct backend contract (`/pipeline/pipeline/applications/{id}/make-offer/`).
- Pipeline data APIs map to backend URLs in `backend/apps/pipeline/urls.py`.

Frontend Status:
Partial

Workflow Integration:
Working

Overall Phase Completion:
84 %
