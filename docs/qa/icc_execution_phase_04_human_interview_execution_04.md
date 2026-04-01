# ICC Phase 04: Human Interview Execution Engine

Prompt ID: `ICC-HUMAN-INTERVIEW-EXECUTION-04`  
Project: `Talent Operating System`  
Module: `Interview Command Center`  
Phase Name: `Phase 04 - Human Interview Execution`

## Scope

Shared execution engine for:

- `technical_interview`
- `hr_interview`
- `managerial_interview`
- `recruiter_screening`
- `offline_interview`
- `phone_interview`
- `external_interviewer`

## 1. System Architecture

Core components:

- Interview Execution Shell
- Interview Instructions
- Interview Details Panel
- Interviewer Panel
- Candidate Panel
- Scorecard Engine
- Feedback Engine
- Decision Engine
- Timeline Engine
- Recruiter Monitoring Engine

Architecture:

- human-led runtime, not candidate question-runner
- candidate shell for details/join/feedback
- interviewer shell for notes/scorecard/recommendation
- recruiter shell for monitor/review/decision
- shared backend orchestration with role-specific frontends

## 2. Database Design

Primary entities:

- `human_interview_attempt`
- `interviewer_assignment`
- `scorecard_response`
- `feedback_record`
- `decision_record`
- `interview_timeline`
- `interview_notes`

## 3. API Structure

Candidate APIs:

- fetch interview details
- confirm attendance
- join interview
- submit feedback

Interviewer APIs:

- start interview
- save notes
- submit feedback
- submit scorecard
- finalize recommendation

Recruiter APIs:

- monitor interview
- fetch feedback
- fetch score
- finalize decision

## 4. UI Architecture

Candidate UI:

- interview details
- join screen
- instructions
- feedback screen

Interviewer UI:

- interview panel
- scorecard
- notes
- submit feedback

Recruiter UI:

- monitor
- review
- decision shell

## 5. Execution Flow

1. Interview scheduled
2. Interviewer assigned
3. Candidate confirms
4. Interviewer starts
5. Candidate joins or arrives
6. Interview conducted
7. Scorecard and notes submitted
8. Recruiter reviews
9. Decision finalized

## 6. Edge Cases

- no show
- late join
- multiple interviewer
- reschedule
- interviewer decline
- partial scorecard
- decision before all feedback

## 7. Enterprise Features

- offline-safe execution
- external interviewer support
- attendance tracking
- runtime scorecard snapshots
- candidate experience feedback support
- decision-readiness visibility
- strong role separation

## 8. Integration Mapping

Connected systems:

- Scorecard Engine
- Decision Engine
- Flow Engine
- Analytics Engine

