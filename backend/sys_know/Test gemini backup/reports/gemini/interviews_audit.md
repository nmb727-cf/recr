# Module Audit: interviews

## 1. Backend Files Found

* `apps/interviews/models.py`: Core models for `InterviewTemplate`, `Interview`, `InterviewPanelist`, and `InterviewQuestion`.
* `apps/interviews/serializers.py`: Serializers for managing interview data, feedback, and questions.
* `apps/interviews/views.py`: Comprehensive views for recruiters (scheduling, feedback) and candidates (starting, submitting answers).
* `apps/interviews/urls.py`: URL patterns for recruiter-facing interview management.
* `apps/interviews/candidate_urls.py`: Dedicated URL patterns for candidate-facing interview experiences.

## 2. Frontend Usage Found

* `../frontend/src/api/interviews.ts`: Extensive integration for scheduling interviews, submitting feedback, and managing templates.
* `../frontend/src/api/analytics.ts`: Calls interview-related analytics.

## 3. Confirmed Backend Features

* **Multi-Format Interview Engine**: Support for AI Screening, One-Way Video, Live Video, Panel, and Technical interviews.
* **Template-Driven Scheduling**: Recruiters can create reusable templates with duration, passing thresholds, and custom question banks.
* **Panelist Feedback & Scoring**: Support for multiple interviewers providing individual scores and recommendations, which are then averaged in the backend.
* **Asynchronous AI Screening**: Backend logic to start, record, and score candidate answers (text/video) automatically.
* **Automated Shortlisting**: Support in `InterviewTemplate` for passing thresholds and auto-action triggers (Shortlist/Reject).
* **Interview Audit Trail**: Tracking of status transitions from `Scheduled` to `Completed`, `Rescheduled`, or `Cancelled`.

## 4. Confirmed Frontend Features

* **Hiring Dashboard Integration**: Scheduling interviews directly for candidates in the hiring pipeline.
* **Candidate Experience**: A structured interface for candidates to view and complete various types of interviews (AI/Video).
* **Feedback Collection UI**: Multi-column feedback panels for interviewers to provide detailed notes and scores.

## 5. Backend Without Frontend

* **Anti-Cheat Monitoring**: Backend supports `anti_cheat_score` and `anti_cheat_flags`, which may lack full visualization in the current recruiter review UI.
* **AI vs. Human Score Split**: The models track separate `ai_score` and `human_score`, allowing for detailed comparison of automated vs. manual evaluation.

## 6. Frontend Without Backend

* **Interview Package Bindings**: The frontend calls `/jobs/requisitions/.../interview-binding/` and `/interviews/packages/`, but these endpoints are **MISSING** in the backend. This represents a significant gap in the hiring setup workflow.

## 7. Validation / Error Handling Gaps

* **Basic Score Averaging**: The backend performs simple mathematical averaging of panelist scores without support for role weighting (e.g., Lead Interviewer having more weight).
* **Stateless Feedback Submission**: The feedback endpoint doesn't support partial saves or versioning of interviewer notes.
* **Duplicate Panelists**: The `InterviewPanelist` model has a unique constraint, but the `post` method doesn't proactively handle attempts to re-add the same interviewer before the error is raised.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/interviews/`.
* **Priority**: Integration tests for the candidate-facing asynchronous interview flow and the panelist feedback submission logic.

## 9. Schema / API Documentation Gaps

* **Missing Detailed Response Schemas**: Mixed payloads in `InterviewDetailView` (Interview + Panelists + Questions) are not fully defined in the OpenAPI schema.
* **Undocumented Recommendation Values**: The set of allowed recommendations (`strongly_recommend`, `recommend`, etc.) is not explicitly described in the OpenAPI documentation.

## 10. Security / Permission Concerns

* **Interviewer Role Enforcement**: Any authenticated user with access to the tenant can submit feedback as a panelist. Need to enforce that only assigned interviewers or tenant admins can submit feedback.
* **Candidate Link Exposure**: `interview_link` and `recording_url` are exposed via the `InterviewSerializer`. Need to ensure candidate access to recording URLs is restricted.

## 11. Stability / Architecture Concerns

* **View Complexity**: Recruiter and Candidate views are grouped together in a single large file, which could be split for better security and maintainability.
* **Coupling with Pipeline**: The module depends on `Application` model updates and event triggers from the pipeline module.

## 12. Priority Fixes

### High
* **Implement Missing Binding Endpoint**: Add support for job-specific interview package bindings in the backend.
* **Implement Tests**: Add core tests for the interview lifecycle and scoring mechanisms.

### Medium
* **Granular Role Checks**: Enforce role-based access for submitting feedback (only assigned panelists).
* **Enhance OpenAPI Documentation**: Add detailed schemas for complex interview payloads.

### Low
* **Standardize Naming**: Align backend `Template` naming with frontend `Package` naming to avoid confusion.

## 13. Unverified Items

* AI-based video analysis and transcript generation logic (UNVERIFIED).
* External calendar integration (Google/Outlook) for scheduling (UNVERIFIED).

## 14. Recommended Next Tests

* `test_interview_template_auto_shortlist`: Verify that scoring above the threshold triggers the auto-shortlist event.
* `test_candidate_one_way_video_flow`: Verify the end-to-end flow of a candidate starting an AI interview and submitting video answers.
* `test_panelist_score_averaging`: Verify that individual panelist scores are correctly averaged into the `human_score` field on the Interview record.
* `test_interview_rescheduling_logic`: Verify that rescheduling an interview correctly updates the status and notifies participants.
* `test_anti_cheat_flag_logging`: Verify that integrity flags (e.g., window blur, duplicate face) are correctly logged in the metadata.
