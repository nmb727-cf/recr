# QA Document: ICC Candidate Runtime Stabilization

## 1. Feature Overview
This update stabilizes the candidate-side interview runtime for the Interview Command Center (ICC). It addresses critical audit findings including mapping bugs, missing functional flows (prequalification), and placeholder execution shells.

## 2. Purpose
To ensure that candidates have a robust, operational experience when attending interviews or completing assignments, and to provide clear visibility into their interview status and results.

## 3. Stabilization & Bug Fixes
* **Interview Type Mapping**: Fixed `getExecutionMode` in `CandidateInterviewRuntime.tsx`. `one_way_video` now correctly maps to the video shell instead of the generic AI text area. `async_text`, `whiteboard`, `coding_interview`, and `take_home_assignment` now map to their dedicated shells.
* **Cancelled Interviews**: Backend `CandidateInterviewListView` now includes a `cancelled` bucket. The frontend `CandidateInterviewDashboard.tsx` surfaces these distinctly, ensuring candidates aren't confused by missing or mixed-status interviews.
* **Status Consistency**: Unified status labels and colors across the dashboard and results pages.

## 4. Prequalification Flow
* **Backend**: Created `CandidatePrequalFormDetailView` and `CandidatePrequalSubmitView` in `apps/prequalification/candidate_views.py`. These allow candidates to fetch and submit forms securely.
* **Frontend**: Created `CandidatePrequalification.tsx` at `/candidate/prequalification?form=<id>`. This page renders form sections, questions (yes/no, select, text, etc.), and handles submission with a success state.

## 5. Native Execution Upgrades
* **Take-Home Assignment**: Implemented real file upload UI with state management.
* **One-Way Video**: Upgraded to a dedicated recording mode shell with "Start Recording" controls.
* **Async Audio**: Added a voice response shell with "Record Answer" controls.
* **Coding Interview**: Implemented a code editor shell with monospace font and language-aware tagging.

## 6. Results & Feedback
* **Backend**: Added `CandidateInterviewResultsView` to provide real data including `feedback_visible` handling.
* **Frontend**: Upgraded `CandidateInterviewResults.tsx` to fetch real scores and feedback summary when the hiring team enables visibility.

## 7. UX & Operational Completion
* **Add to Calendar**: Candidates can now add scheduled interviews to their Google Calendar directly from the dashboard.
* **Status Visibility**: "Cancelled / Missed / Expired" count is clearly shown in the dashboard sidebar.

## 8. Test Scenarios
1. **Mapping Test**: Create a `one_way_video` interview. Log in as a candidate. Verify the Video shell renders.
2. **Prequalification Test**: Navigate to `/candidate/prequalification?form=<valid_id>`. Complete the form and submit. Verify success screen.
3. **Results Visibility**: Complete an interview. In the company side, set a decision and enable "Feedback Visible to Candidate". Verify the candidate can see scores and notes in `/candidate/interviews/results`.
4. **Cancelled Bucket**: Cancel an interview from the company side. Verify it appears in the "Cancelled / Missed / Expired" section on the candidate dashboard.
5. **Assignment Upload**: Open a `take_home_assignment` runtime. Upload a file. Verify the "File uploaded successfully" message and state update.

## 9. Technical Implementation Details
* **Frontend Pages**:
    * `CandidateInterviewRuntime.tsx`: Updated mapping and added panels.
    * `CandidateInterviewDashboard.tsx`: Added cancelled bucket and calendar support.
    * `CandidateInterviewResults.tsx`: Switched to real results API.
    * `CandidatePrequalification.tsx`: New page for form delivery.
* **Backend Views**:
    * `apps/interviews/views.py`: `CandidateInterviewListView` (updated), `CandidateInterviewResultsView` (new).
    * `apps/prequalification/candidate_views.py`: `CandidatePrequalFormDetailView`, `CandidatePrequalSubmitView`.
* **API**: Updated `prequalificationApi` and `interviewsApi` in `frontend/src/api/`.
