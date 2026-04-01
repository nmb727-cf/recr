# HDC-CANDIDATE-COMPARISON-04

## 1. System Architecture

Shared engine name: `CandidateComparisonEngine`

Purpose:
- provide structured, auditable comparison of multiple candidates for the same role or decision pool
- help recruiters, hiring managers, committee members, and leadership compare interview evidence, normalized scores, fit signals, and risk indicators before final decisioning
- operate as a decision-support layer, not as an autonomous decision maker

System placement:
- Candidate Pipeline
- Interview Command Center
- Hiring Decision Command Center
  - Decision Engine
  - Hiring Committee Engine
  - Candidate Comparison Engine
  - Approval Engine
- Offer Management

Core components:
1. `Comparison Dataset Engine`
2. `Candidate Fit Scoring Engine`
3. `Comparison Matrix Engine`
4. `Weighted Comparison Engine`
5. `Evidence Aggregation Engine`
6. `Strength / Risk Highlight Engine`
7. `Score Normalization Engine`
8. `Interview Signal Comparison Engine`
9. `Decision Support Summary Engine`
10. `Comparison Audit Engine`

Supported comparison modes:
- `shortlist_comparison`
- `final_round_comparison`
- `committee_comparison`
- `recruiter_screening_comparison`
- `role_fit_comparison`
- `offer_stage_comparison`
- `replacement_backup_comparison`
- `hiring_pool_ranking_comparison`

Role architecture:
- Recruiter
- Hiring Manager
- Committee Member
- Leadership Reviewer
- Governance Reviewer

Operating model:
- comparison sets are scoped to a tenant, job, and decision pool
- candidate data is pulled from completed ICC evidence and HDC decision context
- raw scores and normalized scores can both be shown, subject to role permissions
- weights can be user-defined only if tenant policy and governance model allow it
- official comparison models can be locked by governance
- candidate remains a global entity with tenant association only
- candidate never accesses comparison UI, snapshots, or ranking state

Comparison rules:
- normalized and raw score views are both supported
- weighted and unweighted ranking are both supported
- mandatory criteria mismatches can block recommendation even if total score is high
- hidden metrics can be suppressed by role permission or governance policy
- tie handling requires explicit tie state, not silent rank ordering
- frozen snapshots preserve audit state even if source data changes later

Architecture layers:
- `Comparison Set Layer`
- `Evidence Aggregation Layer`
- `Normalization Layer`
- `Weighting & Ranking Layer`
- `Summary Layer`
- `Snapshot & Audit Layer`

## 2. Database Design

Primary entities:
- `candidate_comparison_set`
- `candidate_comparison_entry`
- `candidate_comparison_metric`
- `candidate_comparison_score`
- `candidate_comparison_weight`
- `candidate_comparison_summary`
- `candidate_comparison_risk_flag`
- `candidate_comparison_decision_note`
- `candidate_comparison_snapshot`
- `candidate_comparison_audit_log`

Required fields across entities:
- `tenant_id`
- `job_id`
- `decision_id`
- `comparison_set_id`
- `candidate_id`
- `comparison_mode`
- `metric_type`
- `metric_value`
- `normalized_score`
- `weight_value`
- `rank_order`
- `risk_level`
- `recommendation_status`
- `snapshot_status`
- `created_by`
- `created_at`
- `updated_at`

Recommended entity details:

### `candidate_comparison_set`
- `id`
- `tenant_id`
- `job_id`
- `decision_id`
- `comparison_mode`
- `comparison_status`
- `governance_model_locked`
- `created_by`
- `created_at`
- `updated_at`

### `candidate_comparison_entry`
- `id`
- `tenant_id`
- `comparison_set_id`
- `candidate_id`
- `entry_status`
- `rank_order`
- `eligibility_status`
- `created_at`
- `updated_at`

### `candidate_comparison_metric`
- `id`
- `tenant_id`
- `comparison_set_id`
- `candidate_id`
- `metric_type`
- `metric_source`
- `metric_value`
- `metric_visibility`
- `created_at`
- `updated_at`

### `candidate_comparison_score`
- `id`
- `tenant_id`
- `comparison_set_id`
- `candidate_id`
- `raw_score`
- `normalized_score`
- `score_formula_version`
- `score_status`
- `created_at`
- `updated_at`

### `candidate_comparison_weight`
- `id`
- `tenant_id`
- `comparison_set_id`
- `metric_type`
- `weight_value`
- `weight_source`
- `weight_status`
- `created_at`
- `updated_at`

### `candidate_comparison_summary`
- `id`
- `tenant_id`
- `comparison_set_id`
- `summary_payload`
- `recommendation_status`
- `generated_at`
- `created_at`
- `updated_at`

### `candidate_comparison_risk_flag`
- `id`
- `tenant_id`
- `comparison_set_id`
- `candidate_id`
- `risk_type`
- `risk_level`
- `risk_payload`
- `created_at`
- `updated_at`

### `candidate_comparison_decision_note`
- `id`
- `tenant_id`
- `comparison_set_id`
- `candidate_id`
- `author_user_id`
- `note_payload`
- `created_at`
- `updated_at`

### `candidate_comparison_snapshot`
- `id`
- `tenant_id`
- `comparison_set_id`
- `snapshot_status`
- `snapshot_payload`
- `frozen_by`
- `frozen_at`
- `created_at`
- `updated_at`

### `candidate_comparison_audit_log`
- `id`
- `tenant_id`
- `comparison_set_id`
- `candidate_id`
- `event_type`
- `actor_user_id`
- `audit_payload`
- `created_at`

## 3. API Structure

### Create Comparison Set
- Purpose: create a comparison workspace for a role or decision pool
- Method: `POST`
- Path: `/api/hdc/comparisons`
- Inputs:
  - `job_id`
  - `decision_id`
  - `comparison_mode`
  - `candidate_ids`
- Outputs:
  - `comparison_set_id`
  - `comparison_status`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Committee Member where configured

### Add Candidates To Comparison Set
- Purpose: add one or more candidates to an existing set
- Method: `POST`
- Path: `/api/hdc/comparisons/{comparison_set_id}/candidates`
- Inputs:
  - `candidate_ids`
- Outputs:
  - `entry_summary`
  - `comparison_set_state`
- Permissions:
  - Recruiter
  - Hiring Manager

### Remove Candidate From Comparison Set
- Purpose: remove candidate from active comparison set
- Method: `DELETE`
- Path: `/api/hdc/comparisons/{comparison_set_id}/candidates/{candidate_id}`
- Inputs:
  - `candidate_id`
- Outputs:
  - `updated_comparison_set_state`
- Permissions:
  - Recruiter
  - Hiring Manager

### Fetch Comparison Set
- Purpose: fetch comparison set metadata and participants
- Method: `GET`
- Path: `/api/hdc/comparisons/{comparison_set_id}`
- Outputs:
  - `comparison_set`
  - `candidate_entries`
  - `status_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Committee Member
  - Leadership Reviewer
  - Governance Reviewer

### Fetch Comparison Matrix
- Purpose: fetch full candidate comparison matrix
- Method: `GET`
- Path: `/api/hdc/comparisons/{comparison_set_id}/matrix`
- Outputs:
  - `comparison_matrix`
  - `metric_visibility_map`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Committee Member
  - Leadership Reviewer

### Fetch Weighted Comparison
- Purpose: fetch weighted ranking view
- Method: `GET`
- Path: `/api/hdc/comparisons/{comparison_set_id}/weighted`
- Outputs:
  - `weighted_scores`
  - `ranked_candidates`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Committee Member
  - Leadership Reviewer

### Update Comparison Weights
- Purpose: update metric weights where permitted
- Method: `PATCH`
- Path: `/api/hdc/comparisons/{comparison_set_id}/weights`
- Inputs:
  - `weight_updates`
  - `change_reason`
- Outputs:
  - `weight_state`
  - `recomputed_rankings`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Governance Reviewer if official model is locked

### Normalize Comparison Scores
- Purpose: recompute normalized scores
- Method: `POST`
- Path: `/api/hdc/comparisons/{comparison_set_id}/normalize`
- Inputs:
  - `normalization_mode`
- Outputs:
  - `normalized_score_state`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Governance Reviewer

### Generate Comparison Summary
- Purpose: create structured summary of strengths, risks, and comparison rationale
- Method: `POST`
- Path: `/api/hdc/comparisons/{comparison_set_id}/summary`
- Inputs:
  - `summary_mode`
  - `include_risk_flags`
- Outputs:
  - `summary_payload`
  - `recommendation_status`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Committee Member
  - Leadership Reviewer

### Generate Ranked Recommendation
- Purpose: generate decision-support ranking output
- Method: `POST`
- Path: `/api/hdc/comparisons/{comparison_set_id}/recommendation`
- Inputs:
  - `weight_mode`
  - `mandatory_criteria_mode`
- Outputs:
  - `ranked_recommendation`
  - `tie_state`
  - `blocked_candidates`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Leadership Reviewer

### Save Decision Notes
- Purpose: store structured notes against comparison results
- Method: `POST`
- Path: `/api/hdc/comparisons/{comparison_set_id}/notes`
- Inputs:
  - `candidate_id`
  - `note_payload`
- Outputs:
  - `note_id`
  - `note_status`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Committee Member

### Freeze Comparison Snapshot
- Purpose: freeze an auditable comparison state for committee or approval use
- Method: `POST`
- Path: `/api/hdc/comparisons/{comparison_set_id}/freeze`
- Inputs:
  - `freeze_reason`
- Outputs:
  - `snapshot_id`
  - `snapshot_status`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Leadership Reviewer
  - Governance Reviewer

### Fetch Comparison History
- Purpose: retrieve prior comparison versions and updates
- Method: `GET`
- Path: `/api/hdc/comparisons/{comparison_set_id}/history`
- Outputs:
  - `comparison_history`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Governance Reviewer

### Fetch Comparison Audit Log
- Purpose: retrieve audit trail for comparison actions
- Method: `GET`
- Path: `/api/hdc/comparisons/{comparison_set_id}/audit`
- Outputs:
  - `audit_events`
- Permissions:
  - Governance Reviewer
  - Leadership Reviewer
  - Authorized admins

### Fetch Comparison Rationale
- Purpose: retrieve ranking and recommendation rationale
- Method: `GET`
- Path: `/api/hdc/comparisons/{comparison_set_id}/rationale`
- Outputs:
  - `rationale_payload`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Committee Member
  - Leadership Reviewer

### Fetch Risk Highlights
- Purpose: retrieve comparison-level and candidate-level risk flags
- Method: `GET`
- Path: `/api/hdc/comparisons/{comparison_set_id}/risks`
- Outputs:
  - `risk_flags`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Committee Member
  - Leadership Reviewer
  - Governance Reviewer

### Fetch Comparison Snapshot
- Purpose: retrieve frozen comparison snapshot
- Method: `GET`
- Path: `/api/hdc/comparisons/{comparison_set_id}/snapshot`
- Outputs:
  - `snapshot_payload`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Committee Member
  - Leadership Reviewer
  - Governance Reviewer

## 4. UI Architecture

Frontend principles:
- side-by-side compare in card mode and table mode
- filterable metrics
- score trend visibility
- interview evidence panel
- structured recommendation summary
- clean enterprise layout
- no candidate access

### Recruiter UI

#### Comparison Dashboard
- comparison set queue
- active role pools
- pending stale sets
- snapshot status

#### Candidate Selection Panel
- select candidates by job and decision stage
- filter withdrawn or blocked candidates
- add/remove entries

#### Comparison Matrix View
- table mode for metrics
- side-by-side score and evidence view
- mandatory criteria visibility

#### Ranking / Weighting Controls
- editable weight sliders or numeric controls where permitted
- official model lock indicator
- recompute action

#### Strength And Weakness Summary
- strengths by candidate
- weakness and risk highlights
- recruiter notes

### Hiring Manager UI

#### Finalist Comparison Screen
- final-round candidate set
- recommendation summary
- tie and blocker visibility

#### Role-Fit Comparison Cards
- candidate fit cards
- competency emphasis
- mandatory criteria match state

#### Interview Evidence Comparison
- scorecards
- feedback summaries
- AI interview outputs where allowed
- assessment summaries

#### Decision Support Summary
- ranked recommendation
- rationale view
- confidence and risk view

#### Notes / Recommendation Screen
- decision notes
- shortlisting comments
- approval-ready summary

### Committee / Leadership UI

#### Committee Comparison Summary
- committee-ready frozen view
- comparison rationale
- decision-state visibility

#### Weighted Comparison Screen
- weighted matrix
- ranking and tie indicators
- governance model lock state

#### Risk Flag Visibility
- candidate risk flags
- mismatch markers
- stale data indicators

#### Recommendation Comparison
- recommendation by candidate
- backup candidate visibility
- dissent-support context where relevant

#### Freeze / Snapshot / Decision-Ready View
- freeze action
- snapshot evidence
- audit and version timeline

## 5. Execution Flow

1. Candidates reach decision stage
2. Recruiter or hiring manager creates comparison set
3. System pulls structured evidence from ICC and HDC decision context
4. Scores and metrics are normalized
5. Comparison matrix is generated
6. User adjusts weights if permitted
7. Recommendation summary and ranked output are generated
8. Committee or manager reviews comparison set
9. Snapshot is frozen for audit and decision trail
10. Output passes to decision engine, committee engine, or approval layer

## 6. Edge Cases

- Candidates at different stage depth
  - compare only common metrics by default and flag partial comparability
- Missing scorecard for one candidate
  - show incomplete evidence state and lower recommendation confidence
- Incomparable metrics
  - exclude from normalized ranking and flag in rationale
- Stale data after new interview feedback
  - comparison set marked stale until recomputed
- Tie ranking
  - explicit tie state surfaced; no hidden ordering
- Hidden candidate due to permission restriction
  - candidate omitted or redacted based on policy; audit entry preserved
- Weighted model mismatch with governance rule
  - custom weighting blocked or warning issued depending on policy
- Candidate withdrawn after comparison set created
  - candidate marked inactive and removed from recommendation unless snapshot is frozen
- Snapshot frozen then underlying data changes
  - frozen view preserved, live comparison marked newer-state-available
- Comparison across different job roles blocked or warned
  - hard block by default, warning only if tenant policy explicitly allows controlled pool comparison

## 7. Enterprise Features

- tenant-scoped comparison sets
- structured evidence aggregation from ICC and HDC
- raw and normalized score comparison
- weighted and unweighted ranking
- governance-lockable official comparison model
- mandatory criteria and deal-breaker gating
- risk highlighting and decision-support summary
- frozen comparison snapshots for audit
- role-based visibility and metric suppression
- no candidate access with candidate-global rule preserved

## 8. Integration Mapping

### Decision Engine
- Consumes:
  - decision context
  - candidate pool state
- Produces:
  - ranked comparison summary
  - decision-support recommendation
- Events:
  - `hdc.comparison.created`
  - `hdc.comparison.summary.generated`
- Downstream:
  - committee review
  - decision finalization support

### Hiring Committee Engine
- Consumes:
  - frozen comparison snapshot
  - weighted ranking view
- Produces:
  - committee-ready comparison context
- Events:
  - `hdc.comparison.snapshot.frozen`
- Downstream:
  - committee recommendation workflow

### Interview Scorecards
- Consumes:
  - competency scores
  - stage scores
  - scorecard summaries
- Produces:
  - metric inputs
  - evidence panels
- Events:
  - read-only evidence use
- Downstream:
  - normalization and matrix generation

### AI Interview Results
- Consumes:
  - interview summaries
  - scores
  - fit signals where allowed
- Produces:
  - comparison evidence
  - interview signal metrics
- Events:
  - read-only evidence use
- Downstream:
  - evidence aggregation and fit scoring

### Assessment Results
- Consumes:
  - technical and assessment outcomes
- Produces:
  - comparison metrics and gating indicators
- Events:
  - read-only evidence use
- Downstream:
  - weighted and mandatory criteria evaluation

### Approval Engine
- Consumes:
  - frozen comparison snapshot
  - recommendation summary
- Produces:
  - approval review context
- Events:
  - `hdc.comparison.sent_for_approval_context`
- Downstream:
  - approval stages

### Governance Layer
- Consumes:
  - weight updates
  - snapshot freezes
  - official model override attempts
- Produces:
  - governance lock state
  - policy block/warn state
- Events:
  - `hdc.comparison.model.override.requested`
- Downstream:
  - audit and approval controls

### Analytics Layer
- Consumes:
  - comparison usage
  - ranking outcomes
  - tie/conflict frequency
- Produces:
  - decision-support analytics
  - hiring funnel comparison metrics
- Events:
  - `hdc.comparison.metric.updated`
- Downstream:
  - HDC intelligence layers

### Audit Layer
- Consumes:
  - all comparison creation, weight, freeze, and rationale actions
- Produces:
  - immutable audit trail
- Events:
  - `hdc.comparison.audit.logged`
- Downstream:
  - governance review
  - compliance reporting
