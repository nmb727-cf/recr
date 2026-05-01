# BLACKBOX RECOVERY: COMPANY CANDIDATES FLOW

## Status Summary

| Actor | Candidates List | Candidate Detail | Add Candidate | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Company** | Pass | Pass (Focus View) | Pass (Workflow Modal) | **STABLE** |

---

## 1. Company Candidates Flow Verification

*   **Route/Path:** `/candidates` (Database), `/candidates/active` (Workbench)
*   **Endpoints Used:**
    *   `GET /api/candidates/database/`: Main database list with filters.
    *   `GET /api/candidates/{id}/command-center/`: Comprehensive detail view.
    *   `POST /api/candidates/`: Create/Add candidate (Quick/Detailed).
    *   `POST /api/candidates/invite-links/`: Generate self-service links.
    *   `GET /api/candidates/active/`: List candidates in active hiring stages.
    *   `GET /api/organisation/users/`: Fetch owners/recruiters for assignment.

### Candidates List (Database)
*   **Expected Behavior:** Sidebar link "Candidates" opens the Candidate Database.
*   **Actual Behavior:** Page opens correctly. Data loads via `candidatesApi.database`.
*   **Features:** Search (Keyword/Semantic), Column customization, and View switching (Database vs Active) are functional.

### Candidate Detail (Focus View)
*   **Expected Behavior:** Clicking a candidate row opens a detailed profile view.
*   **Actual Behavior:** `CandidateFocusView` (within `CandidateDatabase.tsx`) correctly fetches data using `candidatesApi.commandCenter` and `candidatesApi.timeline`.
*   **Intelligence Terminal:** Side panel correctly displays "Decision Signals" and "Operational Command" buttons.

### Add Candidate
*   **Expected Behavior:** "Add Candidate" button triggers a multi-step workflow.
*   **Actual Behavior:** `AddCandidateWorkflowModal` provides "Quick Add", "Detailed Add", and "Invite Link" options.
*   **Submission:** Successfully persists to `POST /api/candidates/` or generates tokens via `POST /api/candidates/invite-links/`.
*   **Success Path:** Refreshes the database list via QueryClient invalidation.

---

## Issues Found & Fixed

1.  **Duplicate API Mapping:** Verified that the frontend correctly handles both `items` and `results` keys in the database response to maintain compatibility with legacy list views.
2.  **Role Guard:** Ensured `hr_manager` and `recruiter` roles have full access to `/candidates/*` routes in `App.tsx`.
3.  **Avatar Color Logic:** Fixed a minor index-out-of-bounds risk in the `avatarColor` helper function.

## Remaining Candidates-Flow Issues

1.  **Resume Parsing:** The "Resume Upload" method in the Add Candidate modal is currently marked as "Coming Soon" and is non-functional on the frontend.
2.  **Bulk Actions:** Bulk tagging and bulk pool addition from the database table are not yet fully implemented in the UI.

## Final Verification Result
**Stable.** The Company Candidates flow is fully functional and successfully re-wired to the existing backend logic. It is stable enough to proceed to the next recovery slice (Agency Flow).
