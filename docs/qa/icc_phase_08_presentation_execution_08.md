# Phase 08: Presentation Execution Engine

Prompt ID: `ICC-PRESENTATION-EXECUTION-08`  
Phase: `Interview Command Center / Execution Engine / Phase 08`  
Module: `Presentation Execution Engine`

## Scope

Shared tenant-scoped presentation runtime for:

- `presentation_round`
- `live_presentation_interview`
- `slide_presentation_round`
- `business_presentation_round`
- `leadership_presentation_round`
- `technical_presentation_round`
- `project_presentation_round`
- `assignment_presentation_round`
- `recorded_presentation_round`
- `presentation_with_qa_round`

Supports live delivery, upload-first delivery, hybrid presentation modes, and optional Q&A.

## 1. System Architecture

- Shared engine: `PresentationExecutionEngine`
- Core components:
  - Presentation execution shell
  - Instructions/readiness
  - Presentation asset engine
  - File upload/validation engine
  - Live delivery engine
  - Screen-share/slide display shell
  - Phase timer engine
  - Q&A engine
  - Assessor observation engine
  - Scorecard engine
  - Notes/feedback engine
  - Result/decision engine
  - Integrity log
  - Recruiter monitoring linkage
- Architecture layers:
  - presentation asset layer
  - session layer
  - delivery layer
  - phase layer
  - observation layer
  - scoring layer
  - review layer
- Candidate, assessor, lead interviewer, and recruiter UIs are fully separated.
- Bound presentation asset is immutable for scoring context once session starts.

## 2. Database Design

Primary entities:

- `presentation_attempt`
- `presentation_session`
- `presentation_asset_record`
- `presentation_upload_log`
- `presentation_phase_progress`
- `presentation_attendance_log`
- `presentation_observation_record`
- `presentation_scorecard_response`
- `presentation_notes_record`
- `presentation_qa_record`
- `presentation_decision_summary`
- `presentation_integrity_log`
- `presentation_result_summary`
- `presentation_resume_state`

Key fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `session_id`
- `asset_id`
- `asset_type`
- `status`
- `started_at`
- `ended_at`
- `joined_at`
- `left_at`
- `attendance_status`
- `mode_type`
- `presentation_duration`
- `qa_duration`
- `upload_status`
- `validation_status`
- `score_status`
- `decision_status`
- `review_status`
- `integrity_flags`
- `storage_url`

## 3. API Structure

Candidate APIs:

- Fetch presentation details
- Confirm attendance
- Upload presentation file
- Validate uploaded file
- Fetch uploaded asset status
- Join presentation round
- Heartbeat
- Leave/reconnect
- Fetch phase state
- Fetch presentation asset binding
- Submit completion state
- Submit candidate feedback

Assessor/interviewer APIs:

- Fetch session details
- Join assessor shell
- Start session if permitted
- Fetch presentation asset
- Add notes
- Add Q&A notes
- Submit scorecard
- Save partial feedback
- Finalize evaluation
- Submit recommendation

Lead interviewer APIs:

- Start session
- Move phase
- Start/end presentation phase
- Start/end Q&A phase
- Pause/resume
- Mark attendance
- End session
- Finalize presentation flow

Recruiter APIs:

- Monitor session status
- Fetch attendance
- Fetch uploaded asset status
- Fetch assessor submissions
- Fetch flagged sessions
- Fetch score/decision review shell
- Fetch final consolidated result
- Fetch presentation analytics summary

## 4. UI Architecture

Candidate UI:

- Presentation details screen
- Readiness/instructions screen
- Upload material screen
- File validation/status screen
- Waiting room/join screen
- Live presentation shell
- Slide/deck preview shell
- Timer/phase visibility
- Screen-share guidance shell
- Q&A participation shell
- Connection state banner
- Completed screen
- Interrupted/reconnect screen

Assessor/interviewer UI:

- Session details
- Presentation viewer shell
- Candidate info side panel
- Notes panel
- Q&A notes panel
- Scorecard panel
- Recommendation panel
- Finalize evaluation state

Lead interviewer UI:

- Start/end controls
- Phase progression controls
- Attendance panel
- Asset readiness panel
- Q&A control shell
- Consolidation/completion controls

Recruiter UI:

- Session monitor
- Attendance and timeline
- Asset status review
- Assessor submission tracker
- Feedback review shell
- Consolidated score view
- Decision review and flow linkage

## 5. Execution Flow

1. Presentation round is scheduled.
2. Candidate receives instructions and upload rules.
3. Candidate uploads material if required.
4. Asset validation runs.
5. Assessors/interviewers are assigned.
6. Candidate enters readiness and waiting room.
7. Session starts.
8. Attendance is tracked.
9. Presentation phase runs.
10. Q&A phase runs if configured.
11. Assessors capture notes and scores.
12. Session ends.
13. Assessors finalize evaluations.
14. Consolidation runs.
15. Final result/decision is stored.
16. Recruiter reviews through dedicated shell.
17. Decision engine consumes outcome.

## 6. Edge Cases

- File upload fails before session
- File validation fails
- Unsupported format
- Candidate joins without uploaded material
- Screen share unavailable
- Candidate disconnects mid-presentation
- Interviewer disconnects mid-session
- Duplicate session
- Expired interview window
- Asset missing at session start
- Q&A not completed
- Missing assessor scorecards
- Conflicting recommendations
- Forced session closure
- Recruiter opens before consolidation completes
- Candidate reopens completed session

## 7. Enterprise Features

- Shared presentation engine across live, uploaded, and hybrid modes
- Candidate global entity preserved with tenant-scoped execution
- Asset validation and asset binding audit trail
- Replace-before-start policy controls
- Timed phase orchestration
- Optional/mandatory Q&A
- Assessor-specific and shared notes models
- Consolidated scoring and conflict handling
- Screen-share and platform-hosted deck support
- Future-ready hooks for recorded presentation, transcript, and AI analysis

## 8. Integration Mapping

- `Scheduling Engine`
- `Presentation Asset / File Layer`
- `Live Session / Meeting Layer`
- `Scorecard Engine`
- `Decision Engine`
- `Candidate Interview Results`
- `Analytics Engine`
- `Automation Engine`
- `Notification Engine`

