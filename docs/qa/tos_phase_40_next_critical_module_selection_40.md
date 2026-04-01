# TOS-NEXT-CRITICAL-MODULE-SELECTION-40

## 1. System Architecture

Shared layer name: `NextCriticalCoreModuleSelectionLayer`

Purpose:
- force a single next-module decision from the registry and remaining-module map
- rank candidates using criticality, dependency pressure, journey impact, readiness, ambiguity, and delay risk
- keep the output lightweight and admin-visible only
- provide the source of truth for the next implementation prompt

Architecture layers:
- Candidate Evaluation Layer
- Scoring Layer
- Dependency Layer
- Readiness Layer
- Decision Layer
- Sequencing Layer
- Audit Layer

## 2. Database Design

Primary entities:
- `tos_next_module_selection`
- `tos_next_module_candidate_score`
- `tos_next_module_dependency_pressure`
- `tos_next_module_delay_risk`
- `tos_next_module_readiness_record`
- `tos_next_module_recommendation`
- `tos_next_module_rejection_reason`
- `tos_next_module_sequence_plan`
- `tos_next_module_decision_audit`

Tracked fields include:
- `module_key`
- `module_name`
- `candidate_status`
- `criticality_score`
- `dependency_score`
- `journey_impact_score`
- `frontend_gap_score`
- `backend_gap_score`
- `readiness_score`
- `ambiguity_score`
- `delay_risk_score`
- `final_selection_score`
- `selection_status`
- `rejection_reason`
- `recommended_build_mode`
- `recommended_owner_type`
- `recommended_next_step`
- `sequence_rank`
- `notes`

## 3. API Structure

Evaluation APIs:
- fetch candidate module pool
- score module candidates
- fetch candidate scoring summary
- fetch rejected candidates
- fetch dependency pressure summary
- fetch readiness summary

Decision APIs:
- select next critical module
- fetch selected module
- fetch why selected
- fetch why not others
- lock next module decision
- update decision if upstream facts changed

Sequencing APIs:
- fetch immediate implementation order
- fetch backend-first recommendation
- fetch frontend-first recommendation
- fetch blocker prerequisites
- fetch follow-up module sequence

## 4. Django Admin Configuration

Admin visibility is still Django Admin only.

Registered selection models:
- Next Module Selection
- Next Module Candidate Score
- Next Module Dependency Pressure
- Next Module Delay Risk
- Next Module Readiness Record
- Next Module Recommendation
- Next Module Rejection Reason
- Next Module Sequence Plan
- Next Module Decision Audit

Admin supports:
- `list_display`
- `list_filter`
- `search_fields`
- ordering by `final_selection_score`
- inline scoring records
- inline rejection reasons
- inline sequence plan

## 5. Execution Flow

1. Read registry and remaining-module map
2. Build candidate pool
3. Score candidates
4. Apply ambiguity and blocked-state penalties
5. Rank modules
6. Select one next critical module
7. Record rejection reasons for the others
8. Produce immediate implementation order
9. Use this output for the next implementation prompt

## 6. Edge Cases

- score ties
- top module blocked by unclear business rule
- top module depends on hidden upstream work
- backend exists but UI missing
- multiple AI tools already touching the top module
- selected module later becomes blocked
- module is too broad and must be split first
- registry data is stale or incomplete

## 7. Selection Logic

Current forced recommendation:
- `workflow_system`

Why selected:
- it closes the highest-value ATS continuity gap between jobs, pipeline, submissions, recruiter operations, ICC, and HDC
- it has strong dependency pressure because downstream modules assume state movement and action orchestration
- it improves end-to-end user journey continuity faster than isolated UI or dashboard work
- it is implementable backend-first with clear follow-up frontend exposure
- it has lower ambiguity than broader cross-system governance or optional experience extensions

Why not others right now:
- `candidate_database`: critical, but less effective until workflow/state movement is stabilized
- `submissions`: important, but should be built on top of a coherent workflow/state engine
- `job_pipeline`: highly related, but better handled through workflow-system-first execution contracts
- `candidate portal completion`: valuable, but user-facing continuity should not outrun ATS runtime continuity
- `automation` / `analytics` / `governance`: important, but these become stronger once workflow transitions are solid

Recommended build mode:
- `backend_first`

Immediate follow-up sequence:
1. `workflow_system`
2. `job_pipeline`
3. `submissions`
4. `candidate_database`
5. `candidate lifecycle continuity`

## 8. Integration Mapping

Consumes from:
- TOS Core Module Registry
- Remaining Core Module Map
- ICC implementation state
- HDC implementation state
- ATS core modules
- candidate modules
- communication modules
- automation / analytics / governance layers

Produces:
- one selected module
- rejected candidate reasons
- immediate build order
- backend-first or frontend-first recommendation
- follow-up sequence for the next implementation prompts
