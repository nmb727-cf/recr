# Phase 01: MCQ / Assessment Execution Engine

Prompt ID: `ICC-MCQ-EXECUTION-01`  
Phase: `Interview Command Center / Execution Engine / Phase 01`  
Module: `MCQ / Assessment Execution Engine`

## Scope

Shared tenant-scoped assessment runtime for:

- `mcq_assessment`
- `aptitude_test`
- `cognitive_test`
- `language_assessment`
- `psychometric_test`

Candidate runtime is separate from recruiter and reviewer monitoring.

## 1. System Architecture

- Shared engine: `AssessmentExecutionEngine`
- Core components:
  - Execution shell
  - Instructions/readiness
  - Question renderer
  - Section engine
  - Timer engine
  - Answer engine
  - Autosave/resume engine
  - Submission engine
  - Scoring engine
  - Result engine
  - Suspicious activity log
  - Reviewer linkage
- Candidate is global; attempts and execution are tenant-scoped.
- Question delivery is snapshot-based. Randomization is locked per attempt via stored seed and question-set snapshot.
- Resume restores exact sequence, section state, timer state, and review flags.
- Reviewer shell is read/review only and must never reuse candidate execution UI.

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

Key fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `assessment_template_id`
- `question_set_snapshot_id`
- `attempt_token`
- `status`
- `started_at`
- `submitted_at`
- `auto_submitted_at`
- `last_seen_at`
- `duration_consumed_seconds`
- `current_section_id`
- `current_question_id`
- `randomization_seed`
- `anti_cheat_flags`
- `scoring_status`
- `review_status`

Critical rule:

- Snapshot consistency is mandatory. Resume must reopen the same question order and same section/question state.

## 3. API Structure

Candidate APIs:

- Start attempt
- Load runtime state
- Load questions
- Save answer
- Mark/unmark for review
- Navigate next/previous/jump
- Autosave
- Resume attempt
- Submit attempt
- Force submit on timeout
- Fetch result
- Heartbeat
- Runtime status

Reviewer APIs:

- List attempts
- Fetch attempt status
- Fetch flagged attempts
- Fetch suspicious summary
- Fetch answers
- Fetch score breakdown
- Fetch result review shell

Access rules:

- Candidate APIs require candidate context plus secure attempt token.
- Reviewer APIs require tenant-scoped reviewer authorization.

## 4. UI Architecture

Candidate UI:

- Instructions screen
- Readiness/start screen
- Assessment shell
- Section navigator
- Timer bar
- Question renderer
- Mark for review control
- Submit confirmation
- Completed screen
- Interrupted/resume screen

Reviewer UI:

- Attempt queue
- Flagged attempt queue
- Attempt detail shell
- Suspicious activity panel
- Answer review panel
- Score review shell

## 5. Execution Flow

1. Candidate receives assessment.
2. Candidate opens readiness screen.
3. Engine validates token, window, and session integrity.
4. Attempt starts and question snapshot locks.
5. Questions load and timer starts.
6. Answers autosave continuously.
7. Candidate submits or system force-submits on timeout.
8. Scoring runs.
9. Result summary is stored.
10. Reviewer monitors and reviews in separate shell.
11. Decision layer consumes outcome if configured.

## 6. Edge Cases

- Internet disconnect
- Browser refresh
- Timeout during submission
- Partial save recovery
- Duplicate session
- Expired window
- Empty question set
- Randomized set mismatch
- Autosave lag
- Force submit retry
- Section timer expiry
- Reviewer opens before score finalization
- Candidate reopens submitted attempt

## 7. Enterprise Features

- Shared config-driven engine
- Global candidate model preserved
- Tenant-scoped execution
- Snapshot immutability
- Reproducible randomization
- Anti-cheat-ready architecture
- Resume-safe runtime
- Reviewer/candidate UI separation
- Audit trail and suspicious event logging
- Psychometric and non-pass/fail compatibility

## 8. Integration Mapping

- `Assessment Engine`: template and timing rules
- `Question Engine`: question set snapshot and order
- `Scorecard Engine`: score mapping and downstream evaluation
- `Decision Engine`: pass/fail/manual review consumption
- `Candidate Interview Results`: candidate-safe result visibility
- `Analytics Engine`: timing, score, and suspicious metrics
- `Automation Engine`: reminders, routing, follow-up tasks

