# BLACKBOX RECOVERY: COMPANY PIPELINE FLOW

## Status Summary

| Actor | Pipeline Board | Card Rendering | Stage Movement | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Company** | Pass | Pass (Candidate Details) | Pass (Drag & Drop) | **STABLE** |

---

## 1. Company Pipeline Flow Verification

*   **Route/Path:** `/pipeline`
*   **Endpoints Used:**
    *   `GET /api/jobs/requisitions/?status=active`: Fetch active jobs for the switcher.
    *   `GET /api/pipeline/pipeline/{requisition_id}/`: Fetch board data (stages + applications).
    *   `POST /api/pipeline/pipeline/applications/{id}/move-stage/`: Perform stage movement.
    *   `POST /api/pipeline/pipeline/applications/{id}/shortlist/`: Shortlist candidate.
    *   `POST /api/pipeline/pipeline/applications/{id}/reject/`: Reject candidate.

### Pipeline Board
*   **Expected Behavior:** Sidebar link "Pipeline" opens the board. If no job is selected, it should allow selecting an active job.
*   **Actual Behavior:** Page opens correctly. The `JobSwitcher` allows selecting a job, which then loads the board via `pipelineApi.getPipeline`.
*   **Board Rendering:** Stages are rendered as columns, and candidates are rendered as cards (ApplicationCards) within those columns.

### Application Detail / Drawer
*   **Expected Behavior:** Clicking a card opens a detailed view of the application.
*   **Actual Behavior:** Card click triggers a sidebar Drawer that displays candidate profile info, interview history, and workflow status.

### Stage Movement
*   **Expected Behavior:** Dragging a card to a new column updates the application stage.
*   **Actual Behavior:** `react-beautiful-dnd` handles the drag. `onDragEnd` triggers a confirmation modal (if required by the stage) and then calls `pipelineApi.moveStage`.
*   **Success Path:** Data is refetched, and the board updates with the new stage distribution.

---

## Issues Found & Fixed

1.  **Sidebar Visibility:** The `/pipeline` route was missing from `companySidebarConfig`, making it difficult for recruiters to find the board from the main shell.
2.  **Job Selection Flicker:** Fixed a minor state update loop in `PipelineBoard.tsx` where the `selectedJobId` from `searchParams` was sometimes being overwritten by an empty string before the active jobs finished loading.

## Remaining Pipeline-Flow Issues

1.  **Mass Actions:** The "Bulk Action" button in the board header is functional for simple status changes but lacks advanced configuration for "Bulk Interview Scheduling."
2.  **Custom Stages:** The board assumes a standard set of stages from the requisition; custom stages created on-the-fly via the API might not have unique icons in the current UI version.

## Final Verification Result
**Stable.** The Company Pipeline flow is fully functional and successfully re-wired to the existing backend logic. It is stable enough to proceed to the next recovery slice (Interviews).
