# ICC Phase 02: Coding IDE Execution Engine

Prompt ID: `ICC-CODING-EXECUTION-02`  
Project: `Talent Operating System`  
Module: `Interview Command Center`  
Phase Name: `Phase 02 - Coding IDE Execution`

## Scope

Shared execution engine for:

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

Core components:

- Coding Execution Shell
- Instructions / Readiness Screen
- Problem Renderer
- Section / Problem Engine
- IDE Workspace
- Language Runtime Selector
- Code Draft / Autosave Engine
- Compile / Run Engine
- Test Case Evaluation Engine
- Submission Engine
- Scoring Engine
- Result Engine
- Suspicious Activity / Anti-Cheat Log
- Recruiter Review / Monitoring Linkage

Architecture:

- secure sandboxed execution only
- starter code snapshot locked per attempt
- candidate runtime separated from reviewer monitoring shell
- compile/run feedback separated from final hidden testcase evaluation
- per-problem language restrictions supported

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
- `run_count`
- `compile_count`
- `final_submission_version_id`
- `status`
- `scoring_status`
- `review_status`

## 3. API Structure

Candidate APIs:

- start attempt
- load problem set
- load starter code
- change language
- save draft
- autosave draft
- compile code
- run code
- execute custom input
- fetch testcase summary
- next/previous problem
- mark for review
- resume attempt
- submit attempt
- force submit on timeout
- fetch result
- heartbeat
- runtime status

Reviewer APIs:

- attempt status
- submitted attempts
- flagged attempts
- code review shell
- run history
- suspicious activity summary
- score breakdown
- reviewer feedback / manual scoring shell

## 4. UI Architecture

Candidate UI:

- instructions/readiness
- coding shell
- problem navigator
- IDE
- language selector
- compile/run controls
- custom input/output panel
- testcase panel
- mark for review
- submit confirmation
- completed screen
- interrupted/resume screen

Reviewer UI:

- submitted attempts
- flagged attempts
- final submitted code viewer
- language/runtime used
- testcase pass/fail view
- run history
- suspicious indicators
- reviewer notes and override shell

## 5. Execution Flow

1. Candidate opens coding test
2. Readiness validates window and session
3. Attempt starts
4. Problem and starter code snapshots load
5. Draft saves continuously
6. Candidate compiles/runs code
7. Visible feedback returns
8. Candidate submits
9. Final judge runs hidden tests
10. Score calculated
11. Result stored
12. Decision engine consumes result
13. Reviewer monitors and reviews

## 6. Edge Cases

- disconnect
- refresh
- timeout during submit
- partial draft recovery
- duplicate session
- expired window
- empty problem set
- starter code mismatch
- runtime container failure
- compile service unavailable
- hidden testcase delay
- language change mid-attempt
- force submit retry
- reviewer opens before evaluation complete
- candidate reopens submitted attempt

## 7. Enterprise Features

- sandbox isolation
- hidden testcase secrecy
- rate limiting on run/compile
- AI code review-ready hooks
- AI-generated code detection-ready hooks
- SQL/frontend/debugging mode compatibility
- full audit trail on save/run/compile/submit

## 8. Integration Mapping

Connected systems:

- Coding Problem Engine
- Question / Problem Bank Engine
- Sandbox / Judge Infrastructure
- Scorecard Engine
- Decision Engine
- Candidate Interview Results
- Analytics Engine
- Automation Engine

