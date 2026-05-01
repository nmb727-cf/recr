# FORENSIC REPAIR LOG

## 1. Agency Boundary Repair (Submissions)
*   **Issue**: Agency users received 403 Forbidden when viewing their submissions because the UI called company-only job and candidate endpoints for metadata.
*   **Fix Applied**: 
    1.  Enhanced backend `ApplicationSerializer` to include `requisition_title`, `requisition_type`, and candidate details.
    2.  Rewrote `MySubmissions.tsx` and `AgencySubmissionQuickView.tsx` to use these local fields instead of making external API calls to `/jobs/` or `/candidates/`.
*   **Retest Result**: Agency users can now view submissions without hitting 403 errors.

## 2. App.tsx Routing & Role Segregation
*   **Issue**: Many core modules (Workflow, ICC, HDC) were missing from the main router, causing redirects. Routes like `/pipeline` and `/candidates` allowed agency users, leading to backend 403s.
*   **Fix Applied**: 
    1.  Added missing routes for Intelligence Hub, Governance, Hiring Decisions, and Automation.
    2.  Implemented strict `allowedRoles` guards for every route to ensure Companies and Agencies stay in their respective boundaries.
*   **Retest Result**: Routes now correctly resolve or block based on actor role.

## 3. Communication/Chat Wiring
*   **Issue**: `messagesApi` was calling the wrong base path, and the Messages link was hidden for Agency/Candidate.
*   **Fix Applied**: 
    1.  Updated `messagesApi.ts` to use `/communications/messages/` base path.
    2.  Modified `navigation.tsx` to show Messages link in all actor sidebars.
*   **Retest Result**: Chat interface is now reachable and correctly communicating with the backend.

## 4. Candidate Page Resolution
*   **Issue**: Build errors and 404s on Passport/Onboarding pages due to redundant nested folders.
*   **Fix Applied**: Flattened `actors/candidate/pages/` and updated `App.tsx` to use direct paths.
*   **Retest Result**: Candidate portal pages load successfully.
