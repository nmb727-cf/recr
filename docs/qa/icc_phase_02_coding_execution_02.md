# Phase 02: Coding IDE Execution Engine

Prompt ID: `ICC-CODING-EXECUTION-02`  
Phase: `Interview Command Center / Execution Engine / Phase 02`  
Module: `Coding IDE Execution Engine`

## Scope

Shared tenant-scoped coding runtime for:

- `coding_test`
- `programming_assessment`
- `technical_screening_code`
- `frontend_code_assessment`
- `backend_code_assessment`
- `sql_assessment`
- `debugging_test`
- `code_fix_challenge`
- `output_prediction_shell`
- `mixed_coding_round`

## 1. System Architecture

- Shared engine: `CodingExecutionEngine`
- Core components:
  - Coding shell
  - Instructions/readiness
  - Problem renderer
  - Section/problem engine
  - IDE workspace
  - Language runtime selector
  - Draft/autosave engine
  - Compile/run engine
  - Test case evaluation engine
  - Submission engine
  - Scoring engine
  - Result engine
  - Suspicious activity log
  - Reviewer review linkage
- Secure sandboxed execution only. Candidate code never runs on app servers.
- Problem statements, starter code, visible tests, hidden tests, and language rules are snapshot-bound per attempt.
- Resume restores exact draft, selected language, active problem, timer, and layout state.

## 2. Database Design

Primary entities:

- `coding_attempt`
- `coding_attempt_problem_progress`
- `code_submission_record`
- `code_run_log`
- `runtime_state`
- `draft_resume_state`
- `testcase_result_snapshot`
- `suspicious_activity_log`
- `score_breakdown`
- `result_summary`

Key fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `coding_template_id`
- `problem_set_snapshot_id`
- `selected_language`
- `execution_token`
- `status`
- `started_at`
- `submitted_at`
- `auto_submitted_at`
- `last_seen_at`
- `current_problem_id`
- `ide_layout_state`
- `run_count`
- `compile_count`
- `final_submission_version_id`
- `anti_cheat_flags`
- `scoring_status`
- `review_status`

## 3. API Structure

Candidate APIs:

- Start attempt
- Load runtime
- Load problem set
- Load starter code
- Change language
- Save draft
- Autosave draft
- Compile code
- Run code
- Execute custom input
- Fetch testcase summary
- Navigate problems
- Mark problem for review
- Resume attempt
- Submit attempt
- Force submit on timeout
- Fetch result
- Heartbeat
- Runtime status

Reviewer APIs:

- Fetch attempts
- Fetch attempt status
- Fetch flagged attempts
- Fetch code review shell
- Fetch run history
- Fetch suspicious summary
- Fetch score breakdown
- Submit reviewer notes/manual scoring

## 4. UI Architecture

Candidate UI:

- Instructions/readiness
- Interrupted/resume screen
- Coding execution shell
- Problem navigator
- Timer
- IDE workspace
- Language selector
- Run/compile controls
- Custom input/output panel
- Testcase result panel
- Mark for review
- Submit confirmation
- Completed screen

Reviewer UI:

- Attempt queue
- Flagged queue
- Attempt review
- Final code viewer
- Run history viewer
- Score breakdown panel
- Reviewer notes/manual override shell
- Suspicious activity panel

## 5. Execution Flow

1. Candidate opens secure coding link.
2. Readiness and session integrity checks run.
3. Attempt starts and problem snapshot locks.
4. IDE loads with starter code and allowed runtimes.
5. Drafts autosave continuously.
6. Candidate compiles/runs code in secure sandbox.
7. Visible feedback returns; hidden tests remain secret.
8. Candidate submits or is auto-submitted on timeout.
9. Final judge evaluates hidden tests.
10. Scoring and result generation complete.
11. Reviewer inspects code, runs, flags, and scores.

## 6. Edge Cases

- Internet disconnect
- Browser refresh
- Timeout during submission
- Partial draft recovery
- Duplicate session
- Expired window
- Empty problem set
- Starter code mismatch
- Runtime container failure
- Compile service outage
- Hidden testcase evaluation delay
- Mid-attempt language change
- Force submit retry
- Reviewer opens before evaluation completes
- Candidate reopens submitted attempt

## 7. Enterprise Features

- Shared secure coding runtime
- Snapshot-locked starter code
- Language/runtime policy per problem
- Hidden testcase secrecy
- Draft autosave and resume safety
- Rate limiting on compile/run/custom input
- Audit trail for save/run/submit actions
- AI code review and AI-generated code detection integration points
- SQL/frontend/debugging modes via config

## 8. Integration Mapping

- `Coding Problem Engine`
- `Question / Problem Bank Engine`
- `Sandbox / Judge Infrastructure`
- `Scorecard Engine`
- `Decision Engine`
- `Candidate Interview Results`
- `Analytics Engine`
- `Automation Engine`

