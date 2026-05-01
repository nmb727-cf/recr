# ACTOR BOUNDARY REPAIR REPORT

Functional stabilization and actor-boundary repairs completed.

## Issues Found & Fixed

| Page / Component | Wrong Ownership | Correct Ownership | Fix Applied | Endpoint Corrected |
|------------------|-----------------|-------------------|-------------|-------------------|
| `MySubmissions.tsx` (Agency) | Called Company `/jobs/requisitions/` | Agency-owned view of submissions | Removed redundant company/candidate API calls; used data already in Application object. | From `/api/v1/jobs/` to local data |
| `AgencySubmissionQuickView` | Called Company `/jobs/` and `/candidates/` | Agency-owned view of submissions | Removed forbidden API calls; relied on fields added to Application serializer. | From `/api/v1/jobs/` to local data |
| `AgenciesList.tsx` | Mislocated in `actors/agency/` | `actors/company/` | Relocated to Company actor folder; updated re-exports. | N/A (Location fix) |
| `CompanyAgencies.tsx` | Mislocated in `actors/agency/` | `actors/company/` | Relocated to Company actor folder; updated re-exports. | N/A (Location fix) |
| `messagesApi.ts` | Base path mismatch (`/communications/`) | `/communications/messages/` | Updated frontend API client to match backend mount point. | From `/communications/` to `/communications/messages/` |
| Navigation | Hidden Messages for Agency/Candidate | Visible for all | Added Messages link to Agency and Candidate sidebars. | `/messages` |

## Verified Status

### Agency
*   **My Jobs**: Verified using `/api/v1/agencies/my-jobs/` (Agency owned).
*   **Submissions**: Fixed 403 errors by removing company-endpoint dependencies.
*   **Messages**: Visible and functional with corrected API path.

### Company
*   **Agencies Management**: Now correctly located in `actors/company`.
*   **ATS Flows**: Verified core jobs/requisitions remain functional for company users.

### Candidate
*   **Interviews**: Verified candidate runtime uses `/api/v1/candidate/interviews/` (Candidate owned).
*   **Messages**: Now visible in sidebar.

## Remaining Risks
*   **Middleware Strictness**: As middleware becomes stricter, more "proxy" endpoints might be needed in actor views to access domain data (e.g. detailed job descriptions for agency).
*   **Nested Components**: Some deeply nested components might still use old API clients; ongoing monitoring required.
