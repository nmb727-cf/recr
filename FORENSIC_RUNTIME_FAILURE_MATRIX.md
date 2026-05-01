# FORENSIC RUNTIME FAILURE MATRIX

| Actor | Module/Page | Route | Frontend File | Hook/Service | Endpoint | Failure Type | Root Cause | Fix Status |
|-------|-------------|-------|---------------|--------------|----------|--------------|------------|------------|
| Agency | My Submissions | `/agency/submissions` | `MySubmissions.tsx` | `requisitionsApi.list` | `/api/v1/jobs/requisitions/` | 403 Forbidden | Boundary violation (Agency UI hitting Company endpoint) | FIXED |
| Agency | Submission Detail | (Drawer) | `AgencySubmissionQuickView.tsx` | `requisitionsApi.get` | `/api/v1/jobs/requisitions/<id>/` | 403 Forbidden | Boundary violation (Agency UI hitting Company endpoint) | FIXED |
| Company| Workflow Hub | `/workflows/hub` | `IntelligenceHubWorkspace.tsx` | N/A | `/workflows/hub` | Redirect to Dashboard | Route missing in `App.tsx` after migration | FIXED |
| Company| Hiring Decision | `/hiring-decisions` | `HiringDecisionWorkspace.tsx` | N/A | `/hiring-decisions` | Redirect to Dashboard | Route missing in `App.tsx` after migration | FIXED |
| Agency | Jobs/Pipeline | `/pipeline` | `PipelineBoard.tsx` | `requisitionsApi.list` | `/api/v1/jobs/requisitions/` | 403 Forbidden | RBAC Guard too permissive (Agency allowed on Company page) | FIXED |
| All | Messages | `/messages` | `CommunicationsPage.tsx` | `messagesApi.listThreads` | `/api/v1/communications/threads/` | 404 Not Found | API Path mismatch (Frontend doesn't match Backend mount) | FIXED |
| Candidate| Passport | `/passport` | `Passport.tsx` | N/A | `/passport` | Build Error / 404 | Incorrectly nested folder (`candidate/candidate/Passport`) | FIXED |
