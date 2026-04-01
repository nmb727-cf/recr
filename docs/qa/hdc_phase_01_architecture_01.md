# HDC-ARCHITECTURE-01

## 1. System Architecture

Shared layer name: `HiringDecisionCommandCenter`

Purpose:
- convert validated interview outcomes into governed hiring decisions
- support structured candidate comparison, committee review, approvals, and final decisioning
- preserve tenant-scoped operations while consuming interview evidence from ICC

Placement:
- Candidate Pipeline
- Interview Command Center
- Hiring Decision Command Center
- Offer Management
- Onboarding

Core components:
1. `Decision Engine`
2. `Candidate Comparison Engine`
3. `Hiring Committee Engine`
4. `Decision Score Aggregator`
5. `Final Decision Engine`
6. `Decision Approval Engine`
7. `Decision Audit Engine`

Supported decision types:
- `hire`
- `reject`
- `hold`
- `reconsider`
- `move_to_next_stage`

Role architecture:
- Recruiter
- Hiring Manager
- Panel Members
- Decision Committee
- Leadership

Operating model:
- HDC consumes only valid, completed, tenant-scoped interview outcomes from ICC
- interview summaries, scorecards, committee input, and analytics signals feed structured decisioning
- final decisions are approval-aware, auditable, and versioned
- candidate remains a global entity with tenant association only

Architecture layers:
- `Decision Intake Layer`
- `Comparison Layer`
- `Committee Workflow Layer`
- `Scoring Aggregation Layer`
- `Approval Layer`
- `Finalization Layer`
- `Audit Layer`

Source-of-truth model:
- interview evidence and scorecards remain owned by ICC
- active decision records and decision workflow state are owned by HDC
- approval outcomes remain governed by HDC approval state plus enterprise governance policies

## 2. Database Design

Primary entities:
- `hiring_decision`
- `decision_committee`
- `decision_vote`
- `decision_score`
- `decision_approval`
- `decision_audit`

Recommended key fields:

### `hiring_decision`
- `id`
- `tenant_id`
- `candidate_id`
- `job_id`
- `decision_type`
- `decision_status`
- `decision_reason`
- `source_interview_summary_payload`
- `final_score`
- `created_by`
- `finalized_by`
- `finalized_at`
- `created_at`
- `updated_at`

### `decision_committee`
- `id`
- `tenant_id`
- `decision_id`
- `committee_type`
- `committee_status`
- `chair_user_id`
- `member_payload`
- `due_at`
- `created_at`
- `updated_at`

### `decision_vote`
- `id`
- `tenant_id`
- `decision_id`
- `committee_id`
- `voter_user_id`
- `vote_type`
- `vote_reason`
- `vote_weight`
- `submitted_at`
- `created_at`
- `updated_at`

### `decision_score`
- `id`
- `tenant_id`
- `decision_id`
- `candidate_id`
- `score_type`
- `score_value`
- `score_source`
- `score_payload`
- `created_at`
- `updated_at`

### `decision_approval`
- `id`
- `tenant_id`
- `decision_id`
- `approval_stage`
- `approver_user_id`
- `approval_status`
- `approval_reason`
- `approved_at`
- `created_at`
- `updated_at`

### `decision_audit`
- `id`
- `tenant_id`
- `decision_id`
- `event_type`
- `actor_user_id`
- `audit_payload`
- `created_at`

## 3. API Structure

### Create Decision
- Purpose: create a new decision workflow from interview outcomes
- Method: `POST`
- Path: `/api/hdc/decisions`
- Inputs:
  - `candidate_id`
  - `job_id`
  - `decision_type`
  - `source_interview_ids`
  - `initial_reason`
- Outputs:
  - `decision_id`
  - `decision_status`
  - `committee_required`
- Access:
  - Recruiter
  - Hiring Manager

### Update Decision
- Purpose: update draft decision details before finalization
- Method: `PATCH`
- Path: `/api/hdc/decisions/{decision_id}`
- Inputs:
  - `decision_type`
  - `decision_reason`
  - `comparison_payload`
  - `committee_config`
- Outputs:
  - updated decision summary
- Access:
  - Recruiter
  - Hiring Manager

### Submit Vote
- Purpose: submit committee or stakeholder vote on a decision
- Method: `POST`
- Path: `/api/hdc/decisions/{decision_id}/votes`
- Inputs:
  - `vote_type`
  - `vote_reason`
  - `vote_weight`
- Outputs:
  - recorded vote
  - committee status
- Access:
  - Panel Members
  - Decision Committee
  - Leadership where configured

### Approve Decision
- Purpose: approve or reject decision at approval stage
- Method: `POST`
- Path: `/api/hdc/decisions/{decision_id}/approvals`
- Inputs:
  - `approval_status`
  - `approval_reason`
- Outputs:
  - approval state
  - remaining approval stages
- Access:
  - Hiring Manager
  - Leadership
  - Authorized approvers

### Finalize Decision
- Purpose: finalize decision after score aggregation, voting, and approvals
- Method: `POST`
- Path: `/api/hdc/decisions/{decision_id}/finalize`
- Inputs:
  - `final_decision_type`
  - `final_reason`
- Outputs:
  - finalized decision record
  - downstream handoff status
- Access:
  - Recruiter
  - Hiring Manager
  - Authorized final decision owner

## 4. UI Architecture

Primary screens:
- Decision dashboard
- Candidate comparison workspace
- Committee voting workspace
- Approval workflow screen

Recommended views:

### Decision Dashboard
- decision queue
- candidate decision status
- pending approvals
- blocked decisions
- finalized outcomes

### Candidate Comparison
- side-by-side candidate comparison
- score summary
- feedback summary
- interviewer and panel evidence
- risk and analytics highlights

### Committee Voting
- committee member roster
- vote submission
- vote summary
- dissent visibility
- deadline state

### Approval Workflow
- approval stages
- current approver
- approval history
- rejection and rework state
- finalization readiness

UI rules:
- recruiter and hiring manager centered
- leadership and committee views permission-scoped
- decision status must be explicit
- approval blockers and dissent must be visible
- all decision actions auditable

## 5. Execution Flow

1. ICC completes interview evaluation and exposes valid interview evidence
2. Recruiter or hiring manager creates a decision record
3. Decision Score Aggregator compiles scorecards, feedback, and analytics indicators
4. Candidate Comparison Engine prepares comparison context if needed
5. Hiring Committee Engine collects votes and recommendations where configured
6. Decision Approval Engine routes required approvals
7. Final Decision Engine finalizes `hire`, `reject`, `hold`, `reconsider`, or `move_to_next_stage`
8. Decision Audit Engine records all actions and state changes
9. Final decision is handed downstream to offer or next-stage operations
