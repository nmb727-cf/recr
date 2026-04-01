# Phase 11: Composite Flow Execution Engine

Prompt ID: `ICC-COMPOSITE-FLOW-EXECUTION-11`  
Phase: `Interview Command Center / Execution Engine / Phase 11`  
Module: `Composite Flow Execution Engine`

## Scope

Shared orchestration engine for composite interview journeys combining multiple execution engines, including:

- assessment + AI interview
- coding test + panel round
- AI screening + video interview + human interview
- case study + presentation + Q&A
- portfolio review + walkthrough + panel evaluation
- screening chain + final decision flow
- recruiter-designed multi-step paths
- auto-progression flows
- manually controlled progression flows

This engine sits above all child execution engines and provides unified candidate journey orchestration.

## 1. System Architecture

- Shared engine: `CompositeFlowExecutionEngine`
- Core components:
  - Composite flow orchestrator
  - Candidate journey shell
  - Step runtime router
  - Flow state engine
  - Branching/decision engine
  - Resume/recovery engine
  - Score aggregation engine
  - Transition rule engine
  - Reviewer/recruiter monitoring linkage
  - Attempt timeline engine
  - Final result consolidation engine
  - Notification/automation trigger linkage
  - Integrity/cross-step audit engine
  - Experience consistency layer

Architecture layers:

- flow definition layer
- step registry layer
- runtime routing layer
- state layer
- branching layer
- aggregation layer
- review layer
- audit layer

Execution model:

- Candidate remains global.
- Composite attempt, monitoring, review, and decision are tenant-scoped.
- Each child engine remains independently executable and preserves its own immutable attempt linkage.
- Composite engine snapshots the entire flow definition at start and never mutates the candidate’s active journey mid-attempt.
- Composite flow sits above execution engines and below the broader Flow Engine / AI Builder / Automation stack.

Orchestration rules:

- Child engines plug in through a step registry and callback contract.
- Step completion events sync back to composite state.
- Conditional branching resolves from:
  - score thresholds
  - reviewer decisions
  - manual overrides
  - explicit fail/reject/retry/hold outcomes
- Candidate sees one unified journey shell, not a collection of unrelated tools.

## 2. Database Design

Primary entities:

- `composite_flow_attempt`
- `composite_flow_definition_snapshot`
- `composite_flow_step_instance`
- `composite_flow_step_state`
- `composite_flow_transition_log`
- `composite_flow_branch_record`
- `composite_flow_score_aggregate`
- `composite_flow_resume_state`
- `composite_flow_reviewer_state`
- `composite_flow_decision_summary`
- `composite_flow_integrity_log`
- `composite_flow_result_summary`
- `composite_flow_timeline`

Key fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `flow_definition_id`
- `flow_snapshot_id`
- `current_step_id`
- `status`
- `started_at`
- `completed_at`
- `submitted_at`
- `terminated_at`
- `last_seen_at`
- `branch_path`
- `step_order`
- `step_type`
- `step_status`
- `entry_condition_status`
- `exit_condition_status`
- `auto_progress_allowed`
- `manual_review_required`
- `aggregated_score_status`
- `decision_status`
- `review_status`
- `integrity_flags`
- `resume_token`

Entity purposes:

- `composite_flow_attempt`: root orchestration record
- `composite_flow_definition_snapshot`: immutable flow blueprint at attempt start
- `composite_flow_step_instance`: concrete step records bound to child engines
- `composite_flow_step_state`: mutable runtime state for current step lifecycle
- `composite_flow_transition_log`: step entry/exit/transition audit
- `composite_flow_branch_record`: branch decisions and evaluated conditions
- `composite_flow_score_aggregate`: progressive and final scoring state
- `composite_flow_resume_state`: exact recovery state across steps
- `composite_flow_reviewer_state`: pending review/manual approval tracking
- `composite_flow_decision_summary`: consolidated decision state
- `composite_flow_integrity_log`: suspicious events, override logs, reset logs
- `composite_flow_result_summary`: final candidate/reviewer-visible result state
- `composite_flow_timeline`: end-to-end journey timeline

## 3. API Structure

**Candidate APIs**

`POST /candidate/composite-flows/{execution_id}/start`
- Purpose: start composite flow
- Method: `POST`
- Inputs:
  - secure execution token
  - readiness confirmation
- Outputs:
  - `attempt_id`
  - flow summary
  - first step context
- Access: candidate only

`GET /candidate/composite-flows/{attempt_id}/state`
- Purpose: fetch current flow state
- Method: `GET`
- Outputs:
  - current step
  - journey status
  - waiting/review state
- Access: candidate only

`GET /candidate/composite-flows/{attempt_id}/step`
- Purpose: fetch current step
- Method: `GET`
- Outputs:
  - active step metadata
  - child engine launcher context
- Access: candidate only

`POST /candidate/composite-flows/{attempt_id}/continue`
- Purpose: continue current step
- Method: `POST`
- Inputs:
  - resume token or action state
- Outputs:
  - routed child engine action
- Access: candidate only

`GET /candidate/composite-flows/{attempt_id}/progress`
- Purpose: fetch candidate journey progress
- Method: `GET`
- Outputs:
  - completed/current/pending step summary
- Access: candidate only

`POST /candidate/composite-flows/{attempt_id}/resume`
- Purpose: resume flow
- Method: `POST`
- Inputs:
  - resume token
  - session metadata
- Outputs:
  - exact restore state
- Access: candidate only

`GET /candidate/composite-flows/{attempt_id}/next-action`
- Purpose: fetch next allowed action
- Method: `GET`
- Outputs:
  - continue / wait / review pending / completed
- Access: candidate only

`POST /candidate/composite-flows/{attempt_id}/step-submit`
- Purpose: wrapper submit if composite shell needs explicit handoff
- Method: `POST`
- Inputs:
  - step completion acknowledgement
- Outputs:
  - transition evaluation state
- Access: candidate only

`GET /candidate/composite-flows/{attempt_id}/interruption`
- Purpose: fetch interruption state
- Method: `GET`
- Outputs:
  - blocked or resumable state
- Access: candidate only

`GET /candidate/composite-flows/{attempt_id}/completion`
- Purpose: fetch completion state
- Method: `GET`
- Outputs:
  - overall flow completion
  - decision pending or complete
- Access: candidate only

`GET /candidate/composite-flows/{attempt_id}/result`
- Purpose: fetch candidate-visible final result
- Method: `GET`
- Outputs:
  - visibility-safe final result
- Access: candidate only

**Flow orchestration APIs**

`POST /orchestration/composite-flows/{attempt_id}/resolve-next-step`
- Purpose: resolve next step
- Method: `POST`
- Inputs:
  - current step outcome
  - branch context
- Outputs:
  - next step id or terminal state
- Access: internal service only

`POST /orchestration/composite-flows/{attempt_id}/mark-step-complete`
- Purpose: mark step complete
- Method: `POST`
- Inputs:
  - child step result
- Outputs:
  - updated step state
- Access: internal service only

`POST /orchestration/composite-flows/{attempt_id}/evaluate-branch`
- Purpose: evaluate branch conditions
- Method: `POST`
- Inputs:
  - score data
  - reviewer outcome
  - rule payload
- Outputs:
  - branch decision
- Access: internal service only

`POST /orchestration/composite-flows/{attempt_id}/route`
- Purpose: route to child engine
- Method: `POST`
- Inputs:
  - step instance
- Outputs:
  - child engine runtime binding
- Access: internal service only

`POST /orchestration/composite-flows/{attempt_id}/sync-child`
- Purpose: sync child engine status
- Method: `POST`
- Inputs:
  - child attempt linkage
  - child status callback
- Outputs:
  - composite step state update
- Access: internal service only

`POST /orchestration/composite-flows/{attempt_id}/aggregate`
- Purpose: aggregate scores
- Method: `POST`
- Inputs:
  - per-step result data
- Outputs:
  - aggregate score state
- Access: internal service only

`POST /orchestration/composite-flows/{attempt_id}/finalize`
- Purpose: finalize flow
- Method: `POST`
- Inputs:
  - final aggregation and decision context
- Outputs:
  - final result summary
- Access: internal service only

`POST /orchestration/composite-flows/{attempt_id}/terminate`
- Purpose: terminate flow
- Method: `POST`
- Inputs:
  - termination reason
- Outputs:
  - terminated state
- Access: internal service or authorized recruiter override

`POST /orchestration/composite-flows/{attempt_id}/retry-step`
- Purpose: retry or reopen step if policy allows
- Method: `POST`
- Inputs:
  - step id
  - reopen reason
- Outputs:
  - reopened step state
- Access: internal service or authorized override

**Recruiter / reviewer APIs**

`GET /interviews/composite-flows/{attempt_id}/status`
- Purpose: fetch composite attempt status
- Method: `GET`
- Outputs:
  - current state
  - current step
  - overall health
- Access: recruiter/reviewer only

`GET /interviews/composite-flows/{attempt_id}/steps`
- Purpose: fetch step-by-step progress
- Method: `GET`
- Outputs:
  - per-step lifecycle
  - child attempt linkage
- Access: recruiter/reviewer only

`GET /interviews/composite-flows/blocked`
- Purpose: fetch blocked/flagged flows
- Method: `GET`
- Outputs:
  - blocked and flagged queue
- Access: recruiter/reviewer only

`GET /interviews/composite-flows/pending-manual-review`
- Purpose: fetch pending manual review steps
- Method: `GET`
- Outputs:
  - flows waiting on reviewer decision
- Access: recruiter/reviewer only

`GET /interviews/composite-flows/{attempt_id}/scores`
- Purpose: fetch aggregated score view
- Method: `GET`
- Outputs:
  - per-step and aggregate scoring
- Access: recruiter/reviewer only

`GET /interviews/composite-flows/{attempt_id}/branch-path`
- Purpose: fetch branch path
- Method: `GET`
- Outputs:
  - executed branch chain
- Access: recruiter/reviewer only

`GET /interviews/composite-flows/{attempt_id}/decision`
- Purpose: fetch final decision shell
- Method: `GET`
- Outputs:
  - final decision state
  - pending blockers
- Access: recruiter/reviewer only

`GET /interviews/composite-flows/{attempt_id}/timeline`
- Purpose: fetch audit trail
- Method: `GET`
- Outputs:
  - full timeline
- Access: recruiter/reviewer only

`POST /interviews/composite-flows/{attempt_id}/override-transition`
- Purpose: override transition
- Method: `POST`
- Inputs:
  - step id
  - override target
  - reason
- Outputs:
  - updated transition state
- Access: authorized recruiter/reviewer only

`POST /interviews/composite-flows/{attempt_id}/control`
- Purpose: force move / hold / terminate
- Method: `POST`
- Inputs:
  - action
  - reason
- Outputs:
  - updated flow state
- Access: authorized recruiter/reviewer only

**Assessor APIs**

`GET /assessors/composite-flows/{attempt_id}/step-context`
- Purpose: fetch assigned step review context
- Method: `GET`
- Outputs:
  - step-specific review context
  - prior-step visibility if permitted
- Access: assigned assessor only

`POST /assessors/composite-flows/{attempt_id}/step-outcome`
- Purpose: submit step review outcome
- Method: `POST`
- Inputs:
  - step decision
  - scoring/recommendation payload
- Outputs:
  - step review completion state
- Access: assigned assessor only

`POST /assessors/composite-flows/{attempt_id}/step-decision-complete`
- Purpose: mark step decision complete
- Method: `POST`
- Inputs:
  - final step decision
- Outputs:
  - transition-ready state
- Access: assigned assessor only

`POST /assessors/composite-flows/{attempt_id}/escalate`
- Purpose: escalate to recruiter or hiring manager
- Method: `POST`
- Inputs:
  - escalation reason
- Outputs:
  - escalation state
- Access: assigned assessor only

## 4. UI Architecture

**Candidate UI**

- Composite journey home screen
- Step readiness/context screen
- Unified progress tracker
- Current step launcher
- Continue/resume screen
- Step completion state
- Waiting/review pending state
- Branch outcome state if visible
- Flow completed screen
- Interrupted/recover screen

Candidate UI rules:

- One unified candidate journey shell
- Consistent progress model across child engines
- Candidate should not feel routed into unrelated products
- Upcoming steps may be:
  - hidden
  - partially visible
  - fully visible
  depending on flow policy

**Assessor / reviewer UI**

- Step-specific review shell entry
- Composite flow context panel
- Candidate journey summary
- Prior completed step visibility if permitted
- Pending review actions
- Step result submission state

**Recruiter UI**

- Composite flow monitor
- Per-step status tracker
- Blocked/pending review queue
- Score aggregation view
- Branch path visualization
- Final decision shell
- Timeline/audit shell
- Exception handling panel

## 5. Execution Flow

1. Composite flow is assigned to candidate.
2. Candidate sees unified interview journey.
3. Candidate starts flow.
4. Current step is routed to relevant child execution engine.
5. Step executes and completes.
6. Step result syncs back to composite state.
7. Transition logic evaluates next action.
8. Candidate continues to next step or enters wait/review state.
9. Branching occurs if conditions require it.
10. Additional steps execute as needed.
11. Scores aggregate progressively.
12. Final flow completion and decision occur.
13. Recruiter reviews full journey through dedicated shell.
14. Decision engine consumes final outcome.
15. Automation, notifications, and analytics update downstream systems.

Special flows:

- Normal sequential flow
- Async wait-for-review flow
- Conditional branch flow
- Interrupted/resume flow
- Step failure/retry flow
- Live step scheduled later flow
- Termination/rejection flow
- Suspicious activity path

## 6. Edge Cases

- Child engine attempt completes but sync fails
- Branch evaluation fails
- Recruiter changes flow template after candidate started
- Duplicate login/session
- Expired flow window
- Current step unavailable
- Live step scheduled later than async step completion
- Reviewer decision delayed
- Score aggregation mismatch
- One step invalidates previous assumption
- Manual override conflicts with auto progression
- Candidate reopens completed flow
- Final decision requested before all mandatory steps complete

Handling rules:

- Flow template changes after start do not affect active attempt because flow snapshot is immutable.
- Sync failure between child and composite flow creates reconciliation task and blocks unsafe progression.
- Aggregation mismatch triggers review-blocking integrity flag and recalculation.
- Completed flow reopen returns read-only completion state only.

## 7. Enterprise Features

- Shared orchestration engine above all execution engines
- Child engines remain reusable and independently executable
- Immutable flow definition snapshot
- Unified candidate journey shell
- Cross-step resume and recovery architecture
- Conditional branching and transition rule engine
- Manual and automatic progression support
- Per-step and aggregate scoring support
- Pass/fail, hold, escalate, retry, and reject branch handling
- Cross-step integrity audit and override logging
- Mixed async + live step orchestration
- Reviewer/recruiter exception handling
- Future parallel-step-ready shell
- AI Builder and Automation-ready callback model

## 8. Integration Mapping

- `MCQ / Assessment Engine`
  - Consumes: step launch context
  - Produces: child attempt result and completion callback
  - Events: `assessment_step_completed`

- `Coding IDE Engine`
  - Consumes: coding step configuration
  - Produces: score, status, review outputs
  - Events: `coding_step_completed`

- `AI Interview Engine`
  - Consumes: AI step launch context
  - Produces: evaluation outputs and recommendation state
  - Events: `ai_step_completed`

- `Human Interview Engine`
  - Consumes: scheduled human step config
  - Produces: reviewer outcome and scorecard result
  - Events: `human_step_completed`

- `Video Interview Engine`
  - Consumes: video step rules
  - Produces: submission/review result
  - Events: `video_step_completed`

- `Panel Interview Engine`
  - Consumes: panel step configuration
  - Produces: consolidated panel decision
  - Events: `panel_step_completed`

- `Group Discussion Engine`
  - Consumes: discussion batch step config
  - Produces: per-candidate result
  - Events: `group_step_completed`

- `Presentation Engine`
  - Consumes: presentation step configuration
  - Produces: presentation review result
  - Events: `presentation_step_completed`

- `Case Study Engine`
  - Consumes: case-study step configuration
  - Produces: case result package
  - Events: `case_step_completed`

- `Portfolio Review Engine`
  - Consumes: portfolio step configuration
  - Produces: review outcome and snapshot linkage
  - Events: `portfolio_step_completed`

- `Flow Engine`
  - Consumes: recruiter-defined journey templates and orchestration rules
  - Produces: frozen composite flow definitions
  - Events: `composite_flow_started`, `composite_flow_completed`

- `Scorecard Engine`
  - Consumes: per-step scores and weights
  - Produces: aggregated score model
  - Events: `composite_score_aggregated`

- `Decision Engine`
  - Consumes: aggregate result, branch path, manual overrides, final reviewer outcomes
  - Produces: final composite decision
  - Events: `composite_decision_ready`, `composite_decision_finalized`

- `Candidate Interview Results`
  - Consumes: candidate-visible final summary
  - Produces: unified result state for candidate journey
  - Events: `candidate_composite_result_published`

- `Analytics Engine`
  - Consumes: per-step timings, branch behavior, failure/retry states, aggregate outcomes
  - Produces: journey analytics and funnel insights
  - Events: `composite_step_transitioned`, `composite_flow_result_finalized`

- `Automation Engine`
  - Consumes: step completion, blocked state, pending review, final decision
  - Produces: reminders, escalations, next-step automations
  - Events: `composite_flow_blocked`, `composite_flow_waiting_review`, `composite_flow_ready_next`

- `Notification Engine`
  - Consumes: step readiness, scheduling states, review outcomes, final completion
  - Produces: candidate/reviewer/recruiter notifications
  - Events: `composite_step_ready`, `composite_step_scheduled`, `composite_flow_completed`

