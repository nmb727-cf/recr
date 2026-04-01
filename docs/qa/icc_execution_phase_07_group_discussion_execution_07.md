# ICC Phase 07: Group Discussion Execution Engine

Prompt ID: `ICC-GROUP-DISCUSSION-EXECUTION-07`  
Project: `Talent Operating System`  
Module: `Interview Command Center`  
Phase Name: `Phase 07 - Group Discussion Execution`

## Scope

Shared execution engine for:

- `group_discussion`
- `moderated_group_discussion`
- `topic_discussion_round`
- `leadership_group_round`
- `campus_group_discussion`
- `assessment_center_group_discussion`
- `communication_group_round`
- `case_based_group_discussion`
- `debate_style_discussion`
- `structured_group_interaction_round`

## 1. System Architecture

Core components:

- Group Discussion Execution Shell
- Instructions / Readiness Screen
- Live Session Engine
- Participant Roster Engine
- Topic / Prompt Engine
- Phase Timer Engine
- Moderator Control Engine
- Candidate Participation Engine
- Assessor Observation Engine
- Scorecard Engine
- Notes / Event Tagging Engine
- Decision / Result Engine
- Integrity / Suspicious Activity Log
- Recruiter Monitoring Linkage

Architecture:

- multi-candidate live discussion session
- moderator-specific runtime
- assessor-specific observation runtime
- recruiter monitoring/review shell
- candidate-safe discussion shell
- participation/event tagging with future transcript-ready hooks

## 2. Database Design

Primary entities:

- `group_discussion_attempt`
- `group_session`
- `group_candidate_assignment`
- `group_attendance_log`
- `group_topic_record`
- `group_phase_progress`
- `participation_event_log`
- `assessor_observation_record`
- `group_scorecard_response`
- `group_notes_record`
- `group_decision_summary`
- `group_integrity_log`
- `group_result_summary`
- `group_resume_state`

## 3. API Structure

Candidate APIs:

- fetch discussion details
- confirm attendance
- join discussion
- heartbeat
- leave/reconnect
- fetch topic/phase state
- submit candidate experience feedback
- fetch completion state

Moderator APIs:

- fetch session details
- join session
- start session
- announce topic
- move phase
- pause/resume discussion
- mark attendance
- tag major events
- end session

Assessor APIs:

- fetch roster
- join assessor shell
- add observation
- tag candidate participation
- submit scorecard
- save/finalize feedback
- submit recommendation

Recruiter APIs:

- monitor session status
- fetch attendance
- fetch assessor submissions
- fetch flagged sessions
- fetch review shell
- fetch final result
- fetch participation summary

## 4. UI Architecture

Candidate UI:

- discussion details
- readiness / instructions
- waiting room
- live discussion shell
- topic display
- phase/timer visibility
- participant roster shell
- completed screen
- reconnect screen

Moderator UI:

- waiting room control
- topic/prompt control
- phase progression controls
- attendance panel
- event tagging panel
- moderation shell
- end session controls

Assessor UI:

- live observation workspace
- candidate roster with quick tags
- notes panel
- participation indicators
- scorecard panel
- recommendation panel

Recruiter UI:

- session monitor
- attendance and timeline
- assessor submission tracker
- participation review shell
- consolidated score view
- decision linkage

## 5. Execution Flow

1. Discussion scheduled
2. Candidates batched
3. Moderators and assessors assigned
4. Candidates receive schedule/join link
5. Readiness/waiting room
6. Moderator starts session
7. Attendance tracked
8. Topic revealed
9. Phases progress
10. Participation and observations captured
11. Session ends
12. Assessors finalize evaluations
13. Consolidation runs
14. Final result stored
15. Recruiter reviews
16. Decision engine consumes outcome

## 6. Edge Cases

- absent candidates
- absent moderator
- absent assessor
- disconnects and reconnects
- duplicate sessions
- expired window
- topic not loaded
- incomplete roster
- pending assessor scorecards
- conflicting recommendations
- forced closure
- review before consolidation
- reopening completed session

## 7. Enterprise Features

- multi-candidate batch coordination
- moderator and assessor role separation
- participation event tagging
- comparative candidate evaluation
- per-candidate consolidated scoring
- conflict-safe consolidation
- full audit trail on moderation, notes, scores, and decisions
- future-ready recording/transcript/AI participation hooks

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

