# Phase 06: Panel Interview Execution Engine

Prompt ID: `ICC-PANEL-INTERVIEW-EXECUTION-06`  
Phase: `Interview Command Center / Execution Engine / Phase 06`  
Module: `Panel Interview Execution Engine`

## Scope

Shared tenant-scoped live panel runtime for:

- `panel_interview`
- `technical_panel_interview`
- `hr_panel_interview`
- `leadership_panel_interview`
- `final_panel_round`
- `cross_functional_panel`
- `evaluation_board_interview`
- `expert_panel_assessment`
- `stakeholder_panel_round`
- `committee_interview`

## 1. System Architecture

- Shared engine: `PanelInterviewExecutionEngine`
- Core components:
  - Panel interview shell
  - Instructions/readiness
  - Live session engine
  - Panelist role engine
  - Candidate join engine
  - Interviewer join engine
  - Agenda/question flow engine
  - Notes engine
  - Scorecard engine
  - Feedback consolidation engine
  - Decision engine
  - Attendance/timeline engine
  - Integrity log
  - Recruiter monitoring linkage
- Role-separated runtimes:
  - candidate
  - panelist
  - lead interviewer
  - recruiter/reviewer
- Consolidation is based on individual source-of-truth scorecards and recommendations.

## 2. Database Design

Primary entities:

- `panel_interview_attempt`
- `panel_session`
- `panel_participant_assignment`
- `panel_attendance_log`
- `panel_question_flow`
- `panel_scorecard_response`
- `panel_feedback_record`
- `panel_notes_record`
- `panel_decision_summary`
- `panel_integrity_log`
- `panel_result_summary`
- `panel_resume_state`

Key fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `session_id`
- `panelist_id`
- `participant_role`
- `status`
- `started_at`
- `ended_at`
- `joined_at`
- `left_at`
- `attendance_status`
- `lead_interviewer_id`
- `score_status`
- `consolidation_status`
- `decision_status`
- `review_status`
- `recording_url`
- `integrity_flags`

## 3. API Structure

Candidate APIs:

- Fetch interview details
- Confirm attendance
- Join panel interview
- Heartbeat
- Leave/reconnect
- Submit candidate experience feedback
- Fetch completion state

Panelist APIs:

- Fetch session details
- Join session
- Mark attendance
- Fetch agenda/questions
- Add notes
- Submit scorecard
- Save partial feedback
- Finalize feedback
- Submit recommendation
- Mark panel completion

Lead interviewer APIs:

- Start session
- End session
- Control agenda progression
- Open/close scorecard window
- Request panel decision
- Finalize consolidated outcome

Recruiter APIs:

- Monitor session status
- Fetch attendance
- Fetch submitted panel feedback
- Fetch flagged sessions
- Fetch review shell
- Fetch final consolidated result

## 4. UI Architecture

Candidate UI:

- Interview details
- Readiness/instructions
- Join waiting screen
- Live panel session shell
- Participant visibility shell
- Interview progress indicator
- Connection state banner
- Completed screen
- Interrupted/reconnect screen

Panelist UI:

- Session details
- Join panel shell
- Live interview workspace
- Candidate info panel
- Agenda/question flow panel
- Notes panel
- Individual scorecard panel
- Recommendation panel
- Completion state

Lead interviewer UI:

- Start/end controls
- Panel roster
- Live attendance
- Agenda progression controls
- Shared coordination controls
- Consolidation trigger
- Final panel outcome shell

Recruiter UI:

- Session monitor
- Attendance and timeline
- Panel submission tracker
- Feedback review shell
- Consolidated score view
- Decision review and flow linkage

## 5. Execution Flow

1. Panel interview is scheduled.
2. Panelists are assigned and lead interviewer is set.
3. Candidate receives schedule and secure join link.
4. Candidate and panelists open readiness screens.
5. Lead starts session.
6. Candidate joins.
7. Attendance is tracked.
8. Agenda and question flow progress.
9. Panelists capture notes and scores.
10. Session ends.
11. Panelists finalize feedback.
12. Consolidation runs.
13. Final result is stored.
14. Recruiter reviews in dedicated shell.
15. Decision engine consumes outcome.

## 6. Edge Cases

- Candidate no-show
- One panelist absent
- Lead interviewer absent
- Interviewer joins late
- Candidate disconnects mid-session
- Panelist disconnects mid-session
- Duplicate session
- Expired window
- Scorecard missing from some panelists
- Conflicting recommendations
- Forced session closure
- Recruiter opens before consolidation completes
- Candidate reopens completed session

## 7. Enterprise Features

- Shared multi-interviewer panel runtime
- Role-separated shells
- Lead interviewer control layer
- Shared and private notes
- Weighted/consolidated scoring
- Recommendation conflict handling
- Attendance and reconnect auditability
- Tenant-safe recruiter monitoring
- Future recording/transcript integration points

## 8. Integration Mapping

- `Scheduling Engine`
- `Live Session / Meeting Layer`
- `Scorecard Engine`
- `Decision Engine`
- `Candidate Interview Results`
- `Analytics Engine`
- `Automation Engine`
- `Notification Engine`

