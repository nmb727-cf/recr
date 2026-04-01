# Phase 04: Human Interview Execution Engine

Prompt ID: `ICC-HUMAN-INTERVIEW-EXECUTION-04`  
Phase: `Interview Command Center / Execution Engine / Phase 04`  
Module: `Human Interview Execution Engine`

## Scope

Shared tenant-scoped human interview runtime for:

- `technical_interview`
- `hr_interview`
- `managerial_interview`
- `recruiter_screening`
- `offline_interview`
- `phone_interview`
- `external_interviewer`

## 1. System Architecture

- Shared engine: `HumanInterviewExecutionEngine`
- Core components:
  - Interview execution shell
  - Interview instructions
  - Interview details panel
  - Interviewer panel
  - Candidate panel
  - Scorecard engine
  - Feedback engine
  - Decision engine
  - Timeline engine
  - Recruiter monitoring engine
- Role-separated views:
  - candidate
  - interviewer
  - recruiter/reviewer
- Supports online, phone, offline, external interviewer, and multi-step interview patterns.

## 2. Database Design

Primary entities:

- `human_interview_attempt`
- `interviewer_assignment`
- `scorecard_response`
- `feedback_record`
- `decision_record`
- `interview_timeline`
- `interview_notes`

Key fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `status`
- `scheduled_at`
- `started_at`
- `completed_at`
- `attendance_status_candidate`
- `attendance_status_interviewer`
- `final_score`
- `final_recommendation`
- `review_status`
- `decision_status`

## 3. API Structure

Candidate APIs:

- Fetch interview details
- Confirm attendance
- Join interview
- Submit candidate feedback

Interviewer APIs:

- Start interview
- Save notes
- Submit scorecard
- Submit feedback
- Submit recommendation

Recruiter APIs:

- Monitor interview
- Fetch feedback
- Fetch score
- Finalize decision

## 4. UI Architecture

Candidate UI:

- Interview details
- Join screen
- Instructions
- Feedback screen

Interviewer UI:

- Interview panel
- Scorecard
- Notes
- Submit feedback

Recruiter UI:

- Monitor
- Review
- Decision

## 5. Execution Flow

1. Interview is scheduled.
2. Interviewer is assigned.
3. Candidate views details and confirms attendance.
4. Interviewer starts interview.
5. Candidate joins or arrives.
6. Interview is conducted.
7. Interviewer completes notes, scorecard, and recommendation.
8. Recruiter reviews outcome.
9. Decision is finalized and downstream flow consumes it.

## 6. Edge Cases

- No show
- Late join
- Multiple interviewer
- Reschedule
- Interviewer decline
- Candidate confirms but never joins
- Partial scorecard submission
- Decision before all interviewers submit
- Offline interview with manual start/end only

## 7. Enterprise Features

- Shared human interview execution model
- Multi-interviewer support
- External interviewer support
- Offline-safe workflow
- Role-separated UI
- Attendance tracking
- Timeline auditability
- Scorecard snapshotting
- Decision readiness visibility

## 8. Integration Mapping

- `Scorecard Engine`
- `Decision Engine`
- `Flow Engine`
- `Analytics Engine`

