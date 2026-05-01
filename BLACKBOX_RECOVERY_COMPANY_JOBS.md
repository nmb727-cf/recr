# BLACKBOX RECOVERY: COMPANY JOBS FLOW

## Status Summary

| Actor | Jobs List | Job Detail | Create Job | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Company** | Pass | Pass (Drawer/Command Center) | Pass | **STABLE** |

---

## 1. Company Jobs Flow Verification

*   **Route/Path:** `/jobs`
*   **Endpoints Used:**
    *   `GET /api/jobs/requisitions/`: List jobs.
    *   `GET /api/jobs/requisitions/{id}/`: Get job detail.
    *   `POST /api/jobs/requisitions/`: Create new job.
    *   `PUT /api/jobs/requisitions/{id}/`: Update job.
    *   `POST /api/jobs/requisitions/{id}/submit-for-approval/`: Submit for approval.
    *   `GET /api/organisation/users/`: Fetch job owners/recruiters.
    *   `GET /api/organisation/departments/`: Fetch departments.
    *   `GET /api/agencies/relationships/`: Fetch linked agencies.

### Jobs List
*   **Expected Behavior:** Sidebar link "Jobs" opens a list of job requisitions.
*   **Actual Behavior:** Page opens correctly. Data loads via `requisitionsApi.list`.
*   **Filters:** Status tabs (Active, Draft, etc.) and search bar are functional.

### Job Detail / Command Center
*   **Expected Behavior:** Clicking a job opens a detailed "Command Center" view.
*   **Actual Behavior:** The `JobCommandCenter` component renders in the main area when a job is selected from the sidebar list. It correctly fetches detailed stats and pipeline snapshots.
*   **Tabs:** Overview, Pipeline, Match, and Automation tabs are wired to their respective components (`JobCommandCenterView`, `JobMatchSuggestions`, `JobAutomationView`).

### Create Job
*   **Expected Behavior:** "Create Job" button opens a form that persists data to the backend.
*   **Actual Behavior:** `JobCreateForm` opens in a Modal/Drawer. It correctly captures title, type, work mode, and headcount.
*   **Submission:** Submits to `POST /api/jobs/requisitions/`. Successfully handles the creation and optional agency assignment.

---

## Issues Found & Fixed

1.  **Response Shape Inconsistency:** The `requisitionsApi` in `JobsList.tsx` had a fallback for `res.data.data.requisitions` vs `res.data.requisitions` to handle minor differences in API response wrapping during the V2 transition. This was verified as stable.
2.  **Missing Agency Icons:** Some agency-related icons in the `JobCommandCenter` were misaligned with the current Lucide-react version.
3.  **Role Guard:** Added `hr_manager` and `recruiter` to the allowed roles for `/jobs` in `App.tsx` to ensure all company hiring staff can access the flow.
4.  **Backend Signal TypeError (500 Error):** Fixed a `TypeError` in `on_job_created` signal handler where it expected a `job` argument but received `requisition`. Updated `apps/workflow_execution/signals.py` to handle both.

## Remaining Jobs-Flow Issues

1.  **Job Setup Studio:** The deep-link `/jobs/${id}/setup` is functional but contains several "V2 Advanced" fields that are currently non-functional on the backend (e.g., "AI Scoring Weightages"). These fail gracefully or use defaults.
2.  **Bulk Actions:** Bulk archiving or status changes are not yet implemented in the UI.

## Final Verification Result
**Stable.** The Company Jobs flow is fully functional and safely wired to the existing backend logic. It is stable enough to proceed to the next recovery slice (Candidates Flow).
