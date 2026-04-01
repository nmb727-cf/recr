# Phase 07: Group Discussion Execution Engine

Prompt ID: `ICC-GROUP-DISCUSSION-EXECUTION-07`  
Phase: `Interview Command Center / Execution Engine / Phase 07`  
Module: `Group Discussion Execution Engine`

## Scope

Shared tenant-scoped live group discussion runtime for:

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

- Shared engine: `GroupDiscussionExecutionEngine`
- Core components:
  - Group discussion shell
  - Instructions/readiness
  - Live session engine
  - Participant roster engine
  - Topic/prompt engine
  - Phase timer engine
  - Moderator control engine
  - Candidate participation engine
  - Assessor observation engine
  - Scorecard engine
  - Notes/event tagging engine
  - Decision/result engine
  - Integrity log
  - Recruiter monitoring linkage
- Supports one session with multiple candidates and multiple assessors.
- Candidate runtime, moderator runtime, assessor runtime, and recruiter runtime are separate.

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

Key fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `session_id`
- `participant_role`
- `status`
- `started_at`
- `ended_at`
- `joined_at`
- `left_at`
- `attendance_status`
- `topic_id`
- `phase_name`
- `phase_started_at`
- `phase_ended_at`
- `participation_score_status`
- `score_status`
- `decision_status`
- `review_status`
- `integrity_flags`

## 3. API Structure

Candidate APIs:

- Fetch discussion details
- Confirm attendance
- Join discussion
- Heartbeat
- Leave/reconnect
- Fetch topic/phase state
- Submit candidate feedback
- Fetch completion state

Moderator APIs:

- Fetch session details
- Join session
- Start session
- Announce topic
- Move phase
- Pause/resume discussion
- Mark attendance
- Tag major discussion events
- End session

Assessor APIs:

- Fetch session roster
- Join assessor shell
- Add observation
- Tag candidate participation
- Submit scorecard
- Save partial feedback
- Finalize evaluation
- Submit recommendation

Recruiter APIs:

- Monitor session status
- Fetch attendance
- Fetch assessor submissions
- Fetch flagged sessions
- Fetch review shell
- Fetch final consolidated result
- Fetch participation analytics summary

## 4. UI Architecture

Candidate UI:

- Discussion details screen
- Readiness/instructions
- Waiting room
- Live group discussion shell
- Topic display panel
- Phase and timer visibility
- Participant roster shell
- Connection state banner
- Completed screen
- Interrupted/reconnect screen

Moderator UI:

- Session details
- Waiting room control
- Topic/prompt control
- Phase progression controls
- Attendance panel
- Event tagging panel
- Moderation shell
- End session controls

Assessor UI:

- Live observation workspace
- Candidate roster with quick tags
- Notes panel
- Participation indicators
- Scorecard panel
- Recommendation panel
- Finalize evaluation state

Recruiter UI:

- Session monitor
- Attendance and timeline
- Assessor submission tracker
- Participation review shell
- Consolidated score view
- Decision review and flow linkage

## 5. Execution Flow

1. Group discussion is scheduled.
2. Candidates are assigned to batch.
3. Moderators and assessors are assigned.
4. Candidates receive schedule and join link.
5. Candidates enter readiness and waiting room.
6. Moderator starts session.
7. Attendance is tracked.
8. Topic is revealed.
9. Discussion phases progress.
10. Participation and observations are captured.
11. Session ends.
12. Assessors finalize evaluations.
13. Consolidation runs.
14. Final result is stored.
15. Recruiter reviews through dedicated shell.
16. Decision engine consumes outcome.

## 6. Edge Cases

- One or more candidates absent
- Moderator absent
- Assessor absent
- Candidate disconnects mid-session
- Multiple candidates reconnecting
- Duplicate session
- Expired interview window
- Topic not loaded
- Session started with incomplete roster
- Missing assessor scorecards
- Conflicting recommendations
- Forced session closure
- Recruiter opens before consolidation completes
- Candidate reopens completed session

## 7. Enterprise Features

- Shared multi-candidate discussion runtime
- Moderator-specific and assessor-specific shells
- Phase-based discussion orchestration
- Participation tagging and comparative scoring
- Per-candidate evaluation inside one session
- Conflict-safe consolidation
- Attendance and moderation audit logs
- Future transcript and AI participation analysis hooks

## 8. Integration Mapping

- `Scheduling Engine`
- `Live Session / Meeting Layer`
- `Scorecard Engine`
- `Decision Engine`
- `Candidate Interview Results`
- `Analytics Engine`
- `Automation Engine`
- `Notification Engine`

