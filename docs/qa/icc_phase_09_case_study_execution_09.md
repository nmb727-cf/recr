# Phase 09: Case Study Execution Engine

Prompt ID: `ICC-CASE-STUDY-EXECUTION-09`  
Phase: `Interview Command Center / Execution Engine / Phase 09`  
Module: `Case Study Execution Engine`

## Scope

Shared tenant-scoped case-study runtime for:

- `case_study_round`
- `business_case_interview`
- `strategy_case_round`
- `analytical_case_round`
- `problem_solving_case`
- `written_case_assessment`
- `market_sizing_case`
- `operational_case_round`
- `finance_case_round`
- `consulting_case_round`

Supports structured and multi-section case-solving, timed written response rounds, and immutable case-material delivery.

## 1. System Architecture

- Shared engine: `CaseStudyExecutionEngine`
- Core components:
  - Case study execution shell
  - Instructions/readiness
  - Case brief engine
  - Case material viewer
  - Section/phase engine
  - Timer engine
  - Candidate response workspace
  - Draft/autosave/resume engine
  - Submission engine
  - Evaluation/scorecard engine
  - Notes/review engine
  - Result/decision engine
  - Integrity log
  - Recruiter monitoring linkage
- Architecture layers:
  - case material layer
  - execution layer
  - section/phase layer
  - draft layer
  - submission layer
  - evaluation layer
  - review layer
- Material snapshot is immutable per attempt.
- Resume restores exact case, section state, timer state, and draft state.

## 2. Database Design

Primary entities:

- `case_study_attempt`
- `case_material_snapshot`
- `case_section_progress`
- `case_response_record`
- `case_draft_state`
- `case_submission_record`
- `case_assessor_observation`
- `case_scorecard_response`
- `case_notes_record`
- `case_decision_summary`
- `case_integrity_log`
- `case_result_summary`
- `case_resume_state`

Key fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `case_template_id`
- `material_snapshot_id`
- `status`
- `started_at`
- `completed_at`
- `submitted_at`
- `auto_submitted_at`
- `last_seen_at`
- `current_section_id`
- `duration_consumed_seconds`
- `draft_status`
- `submission_status`
- `score_status`
- `decision_status`
- `review_status`
- `integrity_flags`
- `version_number`
- `storage_url`

## 3. API Structure

Candidate APIs:

- Start attempt
- Fetch case brief
- Fetch case materials
- Fetch section state
- Save draft response
- Autosave draft
- Mark section complete
- Next section
- Previous section if allowed
- Resume attempt
- Submit attempt
- Force submit on timeout
- Fetch completion state
- Fetch candidate-visible result if allowed

Assessor/reviewer APIs:

- Fetch attempt status
- Fetch submitted attempts
- Fetch flagged attempts
- Fetch candidate response package
- Fetch case material snapshot
- Add notes
- Submit scorecard
- Save partial review
- Finalize evaluation
- Submit recommendation
- Fetch final consolidated result

Recruiter APIs:

- Monitor attempt status
- Fetch attendance/activity
- Fetch submitted/pending reviews
- Fetch flagged attempts
- Fetch score/decision review shell
- Fetch analytics summary

## 4. UI Architecture

Candidate UI:

- Instructions screen
- Readiness/start screen
- Case brief screen
- Case material viewer
- Case execution shell
- Section navigator
- Timer/phase visibility
- Draft response workspace
- Save/autosave state
- Submit confirmation
- Completed screen
- Interrupted/resume screen

Assessor/reviewer UI:

- Attempt list
- Submitted case review shell
- Candidate response viewer
- Case material viewer
- Notes panel
- Scorecard panel
- Recommendation panel
- Finalize evaluation state

Recruiter UI:

- Attempt status monitor
- Submitted/pending review tracker
- Flagged attempt view
- Consolidated score view
- Decision review shell
- Flow linkage panel

## 5. Execution Flow

1. Case study round is assigned.
2. Candidate receives instructions and schedule.
3. Candidate opens readiness screen.
4. Attempt starts.
5. Case brief and materials load from immutable snapshot.
6. Candidate drafts responses section by section or in full-case mode.
7. Autosave runs continuously.
8. Candidate reconnects and resumes exact state if interrupted.
9. Candidate submits or system force-submits on timeout.
10. Assessor reviews response package and material snapshot.
11. Scoring and evaluation complete.
12. Consolidation runs if multi-reviewer.
13. Final result/decision is stored.
14. Recruiter reviews in dedicated shell.
15. Decision engine consumes outcome.

## 6. Edge Cases

- Internet disconnect
- Browser refresh
- Timeout during submission
- Partial draft recovery
- Duplicate session
- Expired attempt window
- Empty case materials
- Material snapshot mismatch
- Section not loading
- Autosave lag/conflict
- Attachment failure if enabled
- Assessor opens before submission finalization
- Multi-reviewer conflict
- Candidate reopens submitted attempt

## 7. Enterprise Features

- Shared case-study execution engine
- Immutable material snapshot for audit and safe resume
- Freeform and structured answer template support
- Multi-section timed case flow
- Candidate global entity preserved with tenant-scoped execution
- Draft versioning and submission packaging
- Manual rubric-based assessor scoring
- Section-level and overall scoring
- Multi-reviewer consolidation and conflict handling
- Future hooks for plagiarism/similarity analysis and post-case viva/presentation linkage

## 8. Integration Mapping

- `Case Template / Material Engine`
- `Scorecard Engine`
- `Decision Engine`
- `Candidate Interview Results`
- `Analytics Engine`
- `Automation Engine`
- `Notification Engine`
- `Document / Storage Layer`

