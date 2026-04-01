# HDC-DECISION-ENGINE-02

## 1. System Architecture

Shared engine name: `HiringDecisionEngine`

Purpose:
- transform interview evidence into structured, governed hiring decisions
- aggregate scores, collect feedback, capture votes, generate recommendations, and finalize outcomes
- operate only on valid, tenant-scoped interview results from Interview Command Center

Core components:
1. `Decision Aggregation Engine`
2. `Score Aggregator`
3. `Feedback Collector`
4. `Voting Engine`
5. `Recommendation Engine`
6. `Final Decision Engine`

Input sources:
- Interview Scorecards
- AI Interview Results
- Panel Feedback
- Assessment Scores
- Recruiter Notes

Supported decision outcomes:
- `hire`
- `reject`
- `hold`
- `re_interview`
- `offer_pending`

Architecture layers:
- `Decision Intake Layer`
- `Evidence Aggregation Layer`
- `Feedback & Voting Layer`
- `Recommendation Layer`
- `Finalization Layer`
- `Audit Layer`

Operating model:
- evidence is consumed from completed ICC interview runs and associated scorecards
- score, feedback, and vote inputs are normalized into a decision workspace
- recommendation generation is advisory until final approval/finalization rules are met
- final decisions remain auditable, permission-scoped, and approval-aware
- candidate remains a global entity with tenant association only

Decision lifecycle:
1. Create decision record
2. Aggregate interview evidence
3. Collect stakeholder feedback
4. Capture votes where required
5. Generate recommendation
6. Finalize decision

## 2. Database Design

Primary entities:
- `decision_record`
- `decision_feedback`
- `decision_vote`
- `decision_result`
- `decision_recommendation`

Recommended key fields:

### `decision_record`
- `id`
- `tenant_id`
- `candidate_id`
- `job_id`
- `decision_status`
- `decision_type`
- `source_interview_payload`
- `aggregated_score`
- `committee_required`
- `approval_required`
- `created_by`
- `created_at`
- `updated_at`

### `decision_feedback`
- `id`
- `tenant_id`
- `decision_id`
- `feedback_source_type`
- `feedback_source_id`
- `feedback_author_user_id`
- `feedback_payload`
- `feedback_status`
- `submitted_at`
- `created_at`
- `updated_at`

### `decision_vote`
- `id`
- `tenant_id`
- `decision_id`
- `voter_user_id`
- `vote_type`
- `vote_reason`
- `vote_weight`
- `vote_status`
- `submitted_at`
- `created_at`
- `updated_at`

### `decision_result`
- `id`
- `tenant_id`
- `decision_id`
- `final_decision_type`
- `final_decision_reason`
- `finalized_by`
- `finalized_at`
- `result_status`
- `created_at`
- `updated_at`

### `decision_recommendation`
- `id`
- `tenant_id`
- `decision_id`
- `recommendation_type`
- `recommendation_score`
- `confidence_score`
- `recommendation_payload`
- `generated_at`
- `created_at`
- `updated_at`

## 3. API Structure

### Create Decision
- Purpose: initialize a decision process for a candidate/job pair
- Method: `POST`
- Path: `/api/hdc/decision-engine/decisions`
- Inputs:
  - `candidate_id`
  - `job_id`
  - `source_interview_ids`
  - `decision_context`
- Outputs:
  - `decision_id`
  - `decision_status`
  - `aggregated_score_status`
- Access:
  - Recruiter
  - Hiring Manager

### Submit Feedback
- Purpose: attach recruiter, manager, panel, or reviewer feedback to the decision
- Method: `POST`
- Path: `/api/hdc/decision-engine/decisions/{decision_id}/feedback`
- Inputs:
  - `feedback_source_type`
  - `feedback_source_id`
  - `feedback_payload`
- Outputs:
  - `feedback_id`
  - `feedback_status`
- Access:
  - Recruiter
  - Hiring Manager
  - Panel Members

### Submit Vote
- Purpose: record structured vote on the decision
- Method: `POST`
- Path: `/api/hdc/decision-engine/decisions/{decision_id}/votes`
- Inputs:
  - `vote_type`
  - `vote_reason`
  - `vote_weight`
- Outputs:
  - `vote_id`
  - `vote_status`
  - `vote_summary`
- Access:
  - Hiring Manager
  - Panel Members
  - Decision Committee

### Generate Recommendation
- Purpose: generate advisory recommendation from aggregated evidence
- Method: `POST`
- Path: `/api/hdc/decision-engine/decisions/{decision_id}/recommendation`
- Inputs:
  - `recommendation_mode`
  - `include_votes`
  - `include_feedback`
- Outputs:
  - `recommendation_type`
  - `recommendation_score`
  - `confidence_score`
  - `recommendation_payload`
- Access:
  - Recruiter
  - Hiring Manager
  - Leadership where permitted

### Finalize Decision
- Purpose: finalize candidate decision after required evidence, voting, and approvals
- Method: `POST`
- Path: `/api/hdc/decision-engine/decisions/{decision_id}/finalize`
- Inputs:
  - `final_decision_type`
  - `final_decision_reason`
- Outputs:
  - `decision_result`
  - `downstream_handoff_status`
- Access:
  - Hiring Manager
  - Authorized final decision owner

## 4. UI Architecture

Primary screens:
- Decision dashboard
- Candidate comparison
- Voting interface
- Decision summary

### Decision Dashboard
- decision queue
- candidate status
- aggregated score status
- pending feedback and votes
- finalization readiness

### Candidate Comparison
- side-by-side candidate evidence
- scorecard summary
- assessment summary
- panel and AI interview highlights
- recruiter notes

### Voting Interface
- vote submission form
- current vote summary
- weighted vote visibility
- dissent visibility
- pending voters

### Decision Summary
- recommendation summary
- confidence and evidence breakdown
- final decision selection
- approval/finalization blockers
- audit timeline

UI rules:
- recruiter and hiring manager centered
- decision state must remain explicit
- recommendation must be explainable
- blocked finalization must be visible
- all actions auditable

## 5. Execution Flow

1. Decision is created for a candidate and job
2. Decision Aggregation Engine pulls completed interview evidence from ICC
3. Score Aggregator computes normalized aggregate score from scorecards, assessments, and interview results
4. Feedback Collector ingests recruiter notes, panel feedback, and evaluator comments
5. Voting Engine captures structured votes where voting is enabled
6. Recommendation Engine produces advisory recommendation based on evidence, scores, and votes
7. Final Decision Engine validates readiness and finalizes `hire`, `reject`, `hold`, `re_interview`, or `offer_pending`
8. Decision result is stored and made available to downstream committee, approval, or offer workflows
