# ICC Phase 06: Panel Interview Execution Engine

Prompt ID: `ICC-PANEL-INTERVIEW-EXECUTION-06`  
Project: `Talent Operating System`  
Module: `Interview Command Center`  
Phase Name: `Phase 06 - Panel Interview Execution`

## Scope

Shared execution engine for:

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

Core components:

- Panel Interview Execution Shell
- Instructions / Readiness Screen
- Live Session Engine
- Panelist Role Engine
- Candidate Join Engine
- Interviewer Join Engine
- Agenda / Question Flow Engine
- Notes Engine
- Scorecard Engine
- Feedback Consolidation Engine
- Decision Engine
- Attendance / Timeline Engine
- Suspicious / Integrity Log
- Recruiter Monitoring Linkage

Architecture:

- one candidate, multiple panelists
- lead interviewer control flow
- individual panelist runtime
- recruiter monitoring and review shell
- score consolidation and conflict-safe decision layer

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

## 3. API Structure

Candidate APIs:

- fetch interview details
- confirm attendance
- join panel interview
- heartbeat
- leave/reconnect
- submit candidate experience feedback
- fetch completion state

Panelist APIs:

- fetch session details
- join session
- mark attendance
- fetch agenda
- add notes
- submit scorecard
- save/finalize feedback
- submit recommendation
- mark completion

Lead APIs:

- start session
- end session
- control agenda progression
- open/close scorecard window
- request panel decision
- finalize consolidated outcome

Recruiter APIs:

- monitor session status
- fetch attendance
- fetch submitted feedback
- fetch flagged sessions
- fetch score/review shell
- fetch final result

## 4. UI Architecture

Candidate UI:

- details screen
- readiness / instructions
- join waiting screen
- live panel shell
- participant visibility shell
- progress indicator
- completed screen
- reconnect screen

Panelist UI:

- session details
- join panel shell
- candidate info side panel
- agenda panel
- notes panel
- scorecard panel
- recommendation panel

Lead UI:

- start/end controls
- panel roster
- attendance
- agenda progression
- shared coordination controls
- consolidation trigger

Recruiter UI:

- session monitor
- attendance/timeline
- panel submission tracker
- feedback review
- consolidated score
- decision linkage

## 5. Execution Flow

1. Panel interview scheduled
2. Panelists assigned with roles
3. Candidate receives schedule/link
4. Readiness screens open
5. Lead starts session
6. Candidate joins
7. Attendance tracked
8. Agenda progresses
9. Panelists capture notes and scores
10. Session ends
11. Panelists finalize feedback
12. Consolidation runs
13. Final result stored
14. Recruiter reviews
15. Decision engine consumes outcome

## 6. Edge Cases

- candidate no-show
- one panelist absent
- lead absent
- late join
- disconnect
- duplicate session
- expired window
- scorecard pending
- conflicting recommendations
- forced closure
- review before consolidation
- reopening completed session

## 7. Enterprise Features

- role-separated shells
- multi-panelist scoring
- weighted/consolidated recommendations
- shared and private notes
- lead-controlled progression
- attendance and reconnect auditability
- conflict-safe consolidation

## 8. Integration Mapping

Connected systems:

- Scheduling Engine
- Live Session / Meeting Layer
- Scorecard Engine
- Decision Engine
- Candidate Interview Results
- Analytics Engine
- Automation Engine
- Notification Engine

