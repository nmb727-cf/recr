# Reality-Based Testing Backlog

## High Priority (Broken/Mismatched Flows)
1. **[E2E/Integration] Verify Auth Flow Paths**
   - Ensure the API gateway or Vite proxy correctly maps `/auth/` to `/accounts/`. Write an integration test hitting the frontend endpoint and verifying it reaches the backend.
2. **[E2E/Integration] Verify Organisation Paths**
   - Test if `/organisation/` correctly routes to `/organisations/`.

## Core Application Flows (Missing Tests)
3. **[API] Candidate Creation & Pipeline Movement**
   - Flow: Create candidate -> Add to pipeline -> Move stages.
   - Target: `backend/apps/candidates/`, `backend/apps/pipeline/`
4. **[API] Job Requisition & Publishing**
   - Flow: Create requisition -> Add stages -> Publish -> View Posting.
   - Target: `backend/apps/jobs/`
5. **[API] Agency Assignment Flow**
   - Flow: Invite Agency -> Accept -> Assign to Requisition -> Agency Submits Candidate.
   - Target: `backend/apps/agencies/`
6. **[API] Interview Scheduling**
   - Flow: Create template -> Schedule Interview -> Submit Feedback.
   - Target: `backend/apps/interviews/`

## Backend-Only Features (Missing Tests)
7. **[API] Documents & Offers Workflow**
   - Flow: Generate Offer -> Send -> Accept/Reject.
   - Target: `backend/apps/documents/`
8. **[API] Communications Webhooks**
   - Flow: Simulate webhook payload for email bounce/delivery.
   - Target: `backend/apps/communications/email_webhooks/`
