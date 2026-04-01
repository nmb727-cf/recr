# ICC Phase 01: MCQ / Assessment Execution Engine

Prompt ID: `ICC-MCQ-EXECUTION-01`  
Project: `Talent Operating System`  
Module: `Interview Command Center`  
Phase Name: `Phase 01 - MCQ / Assessment Execution`

## Scope

Shared execution engine for:

- `mcq_assessment`
- `aptitude_test`
- `cognitive_test`
- `language_assessment`
- `psychometric_test`

Single shared engine, config-driven per assessment type.

## 1. System Architecture

Core components:

- Execution Shell
- Instructions / Readiness Screen
- Question Renderer
- Section Engine
- Timer Engine
- Answer Engine
- Autosave / Resume Engine
- Submission Engine
- Scoring Engine
- Result Engine
- Suspicious Activity / Anti-Cheat Log
- Recruiter Review / Monitoring Linkage

Architecture:

- Candidate = global entity
- Attempt = tenant-scoped
- Snapshot-based question/version locking
- Randomization seed stored per attempt
- Candidate runtime separated from reviewer monitoring UI
- Shared backend services for runtime, scoring, anti-cheat, results, and analytics

## 2. Database Design

Primary entities:

- `assessment_attempt`
- `attempt_section_progress`
- `answer_record`
- `timer_state`
- `resume_state`
- `suspicious_activity_log`
- `score_breakdown`
- `result_summary`

Required fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `assessment_template_id`
- `question_set_snapshot_id`
- `status`
- `started_at`
- `submitted_at`
- `auto_submitted_at`
- `last_seen_at`
- `duration_consumed`
- `attempt_token`
- `anti_cheat_flags`
- `scoring_status`
- `review_status`

## 3. API Structure

Candidate APIs:

- start attempt
- load runtime
- load questions
- save answer
- mark for review
- navigate question
- autosave
- resume attempt
- submit attempt
- force submit on timeout
- fetch result
- heartbeat
- runtime status

Reviewer APIs:

- attempt list
- attempt status
- flagged attempts
- answer review
- suspicious activity summary
- score breakdown
- result review shell

## 4. UI Architecture

Candidate UI:

- instructions and readiness
- assessment shell
- section navigation
- timer and progress
- question renderer
- mark for review
- submission confirmation
- completed state
- interrupted/resume state

Reviewer UI:

- attempt queue
- flagged queue
- answer review shell
- suspicious activity panel
- score review shell
- result review and decision linkage

## 5. Execution Flow

Main flow:

1. Candidate receives assessment
2. Opens readiness screen
3. Attempt starts and snapshot locks
4. Questions load
5. Answers autosave continuously
6. Timer runs
7. Candidate submits or timeout forces submission
8. Scoring runs
9. Result stored
10. Decision engine consumes result
11. Reviewer monitors and reviews in separate shell

## 6. Edge Cases

- internet disconnect
- browser refresh
- timeout during submission
- partial save recovery
- duplicate session
- expired window
- empty question set
- randomization mismatch
- autosave lag
- force submit retry
- reviewer opens before scoring complete
- candidate reopens submitted attempt

## 7. Enterprise Features

- tenant-scoped runtime
- reproducible randomization
- snapshot integrity
- anti-cheat-ready architecture
- psychometric compatibility
- analytics-ready lifecycle events
- automation-ready submission/result events

## 8. Integration Mapping

Connected systems:

- Assessment Engine
- Question Engine
- Scorecard Engine
- Decision Engine
- Candidate Interview Results
- Analytics Engine
- Automation Engine

