# ACTOR ENDPOINT MATRIX

This matrix tracks the mapping between frontend pages, their API hooks, and backend endpoints to ensure proper actor-boundary isolation.

| Actor | Page / Flow | Frontend Module | Hook / Service | Endpoint Called | Correct Ownership | Status |
|-------|-------------|-----------------|----------------|-----------------|-------------------|--------|
| Agency | My Jobs | `MyJobs.tsx` | `agenciesApi.myJobs` | `/api/v1/agencies/my-jobs/` | Agency | FIXED |
| Agency | Submissions | `MySubmissions.tsx` | `agenciesApi.mySubmissions` | `/api/v1/agencies/my-submissions/` | Agency | FIXED |
| Agency | Submission Detail | `AgencySubmissionQuickView` | `pipelineApi.getApplication` | `/api/v1/pipeline/applications/<id>/` | Mixed (Domain) | FIXED* |
| Agency | Clients | `AgencyClients.tsx` | `agenciesApi.listClientRelationships` | `/api/v1/agencies/clients/` | Agency | FIXED |
| Company | Agency List | `AgenciesList.tsx` | `agenciesApi.listRelationships` | `/api/v1/agencies/relationships/` | Company | FIXED |
| Company | Jobs List | `JobsList.tsx` | `requisitionsApi.list` | `/api/v1/jobs/requisitions/` | Company | FIXED |
| Candidate| Interviews | `CandidateInterviewStatus` | `interviewsApi.candidateStatus` | `/api/v1/candidate/interviews/<id>/status/` | Candidate | FIXED |
| All | Messages | `CommunicationsPage` | `messagesApi.listThreads` | `/api/v1/communications/messages/threads/` | Shared | FIXED |

*\*FIXED here means the page no longer calls company-only endpoints like `/api/v1/jobs/` or `/api/v1/candidates/` for basic metadata.*
