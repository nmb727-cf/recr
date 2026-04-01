# HDC-COMMITTEE-ENGINE-03

## 1. System Architecture

Shared engine name: `HiringCommitteeEngine`

Purpose:
- provide the structured collaborative decision layer for hiring
- manage committee formation, member assignment, review workflow, voting, quorum, dissent, escalation, and final committee recommendation
- operate on tenant-scoped decision contexts created by the HDC Decision Engine

System placement:
- Candidate Pipeline
- Interview Command Center
- Hiring Decision Command Center
  - Decision Engine
  - Hiring Committee Engine
  - Approval Engine
- Offer Management

Core components:
1. `Committee Setup Engine`
2. `Member Assignment Engine`
3. `Committee Review Engine`
4. `Voting Engine`
5. `Quorum Engine`
6. `Weighted Decision Engine`
7. `Dissent / Conflict Engine`
8. `Committee Recommendation Engine`
9. `Escalation Engine`
10. `Committee Audit Engine`

Supported committee modes:
- `single_reviewer_committee`
- `recruiter_hiring_manager_committee`
- `panel_decision_committee`
- `leadership_approval_committee`
- `final_hiring_committee`
- `exceptional_escalation_committee`

Role architecture:
- Recruiter
- Hiring Manager
- Panel Lead
- Committee Member
- Decision Owner
- Leadership Approver
- Governance Reviewer

Operating model:
- committee workflows are created from an existing decision context and candidate/job scope
- committee members review normalized interview evidence, score summaries, feedback, and analytics flags
- voting can be standard, weighted, unanimous, advisory, or mandatory-member-driven
- committee output is a governed recommendation, not necessarily the final hiring approval
- candidate remains a global entity with tenant association only
- candidate never accesses committee UI or committee state

Decision rules:
- recruiter vote is configurable by committee type and tenant policy; default is allowed for recruiter-led committees and disabled for leadership-only committees
- hiring manager vote can be mandatory when committee type requires business ownership
- leadership can override committee recommendation only through explicit override path with audit reason
- committee can reopen after finalization only if new evidence arrives and governance policy allows reopening
- dissent note is mandatory when a required member votes against majority or when weighted vote materially changes outcome

Architecture layers:
- `Committee Configuration Layer`
- `Assignment Layer`
- `Review Layer`
- `Voting & Quorum Layer`
- `Conflict & Escalation Layer`
- `Recommendation Layer`
- `Audit Layer`

## 2. Database Design

Primary entities:
- `hiring_committee`
- `hiring_committee_member`
- `hiring_committee_assignment`
- `hiring_committee_review`
- `hiring_committee_vote`
- `hiring_committee_quorum`
- `hiring_committee_recommendation`
- `hiring_committee_conflict`
- `hiring_committee_escalation`
- `hiring_committee_audit_log`

Required fields across entities:
- `tenant_id`
- `candidate_id`
- `job_id`
- `decision_id`
- `committee_type`
- `member_role`
- `vote_weight`
- `vote_status`
- `review_status`
- `quorum_status`
- `escalation_status`
- `recommendation_status`
- `created_at`
- `updated_at`

Recommended entity details:

### `hiring_committee`
- `id`
- `tenant_id`
- `candidate_id`
- `job_id`
- `decision_id`
- `committee_type`
- `committee_status`
- `decision_mode`
- `recruiter_vote_allowed`
- `hiring_manager_vote_required`
- `leadership_override_allowed`
- `reopen_allowed`
- `activated_at`
- `finalized_at`
- `created_at`
- `updated_at`

### `hiring_committee_member`
- `id`
- `tenant_id`
- `committee_id`
- `user_id`
- `member_role`
- `member_status`
- `is_required`
- `is_advisory`
- `vote_weight`
- `created_at`
- `updated_at`

### `hiring_committee_assignment`
- `id`
- `tenant_id`
- `committee_id`
- `user_id`
- `assignment_status`
- `assigned_at`
- `accepted_at`
- `replaced_by_user_id`
- `created_at`
- `updated_at`

### `hiring_committee_review`
- `id`
- `tenant_id`
- `committee_id`
- `member_id`
- `decision_id`
- `review_payload`
- `review_status`
- `submitted_at`
- `created_at`
- `updated_at`

### `hiring_committee_vote`
- `id`
- `tenant_id`
- `committee_id`
- `decision_id`
- `member_id`
- `vote_type`
- `vote_weight`
- `vote_status`
- `dissent_note`
- `stale_vote_status`
- `submitted_at`
- `created_at`
- `updated_at`

### `hiring_committee_quorum`
- `id`
- `tenant_id`
- `committee_id`
- `quorum_type`
- `required_member_count`
- `required_vote_count`
- `quorum_status`
- `validated_at`
- `created_at`
- `updated_at`

### `hiring_committee_recommendation`
- `id`
- `tenant_id`
- `committee_id`
- `decision_id`
- `recommendation_type`
- `recommendation_payload`
- `recommendation_status`
- `generated_at`
- `created_at`
- `updated_at`

### `hiring_committee_conflict`
- `id`
- `tenant_id`
- `committee_id`
- `decision_id`
- `conflict_type`
- `conflict_payload`
- `conflict_status`
- `created_at`
- `updated_at`

### `hiring_committee_escalation`
- `id`
- `tenant_id`
- `committee_id`
- `decision_id`
- `escalation_type`
- `escalation_status`
- `escalated_to_role`
- `escalated_to_user_id`
- `escalated_at`
- `resolved_at`
- `created_at`
- `updated_at`

### `hiring_committee_audit_log`
- `id`
- `tenant_id`
- `committee_id`
- `decision_id`
- `event_type`
- `actor_user_id`
- `audit_payload`
- `created_at`

## 3. API Structure

### Create Committee
- Purpose: create committee workflow for a decision
- Method: `POST`
- Path: `/api/hdc/committees`
- Inputs:
  - `decision_id`
  - `candidate_id`
  - `job_id`
  - `committee_type`
  - `decision_mode`
- Outputs:
  - `committee_id`
  - `committee_status`
  - `committee_config`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Decision Owner

### Assign Committee Members
- Purpose: assign or replace committee members
- Method: `POST`
- Path: `/api/hdc/committees/{committee_id}/members`
- Inputs:
  - `member_list`
  - `required_member_flags`
  - `vote_weights`
- Outputs:
  - `assignment_summary`
  - `committee_member_state`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Decision Owner

### Fetch Committee Details
- Purpose: return full committee structure, status, and evidence context
- Method: `GET`
- Path: `/api/hdc/committees/{committee_id}`
- Inputs:
  - `committee_id`
- Outputs:
  - `committee_details`
  - `member_list`
  - `quorum_state`
  - `recommendation_state`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Committee Member
  - Leadership Approver
  - Governance Reviewer

### Update Committee Structure
- Purpose: update committee mode, members, or rules before finalization
- Method: `PATCH`
- Path: `/api/hdc/committees/{committee_id}`
- Inputs:
  - `committee_type`
  - `decision_mode`
  - `member_changes`
  - `override_reason`
- Outputs:
  - `updated_committee_state`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Decision Owner
  - Governance Reviewer where required

### Activate Committee Review
- Purpose: move committee into active review state
- Method: `POST`
- Path: `/api/hdc/committees/{committee_id}/activate`
- Inputs:
  - `activation_note`
- Outputs:
  - `committee_status`
  - `review_deadline`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Decision Owner

### Submit Committee Review
- Purpose: submit structured review and comments
- Method: `POST`
- Path: `/api/hdc/committees/{committee_id}/reviews`
- Inputs:
  - `review_payload`
  - `review_note`
- Outputs:
  - `review_id`
  - `review_status`
- Permissions:
  - Committee Member
  - Hiring Manager
  - Panel Lead

### Submit Vote
- Purpose: submit vote with optional dissent
- Method: `POST`
- Path: `/api/hdc/committees/{committee_id}/votes`
- Inputs:
  - `vote_type`
  - `vote_reason`
  - `dissent_note`
- Outputs:
  - `vote_id`
  - `vote_status`
  - `current_vote_summary`
- Permissions:
  - Committee Member
  - Hiring Manager if allowed
  - Recruiter if allowed
  - Leadership Approver if configured

### Fetch Vote Summary
- Purpose: fetch current vote distribution and status
- Method: `GET`
- Path: `/api/hdc/committees/{committee_id}/votes/summary`
- Inputs:
  - `committee_id`
- Outputs:
  - `vote_summary`
  - `weighted_outcome`
  - `pending_members`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Decision Owner
  - Leadership Approver

### Validate Quorum
- Purpose: validate minimum quorum and required-member participation
- Method: `POST`
- Path: `/api/hdc/committees/{committee_id}/quorum/validate`
- Inputs:
  - `committee_id`
- Outputs:
  - `quorum_status`
  - `missing_required_members`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Decision Owner
  - Governance Reviewer

### Generate Committee Recommendation
- Purpose: generate committee recommendation from reviews, votes, and quorum state
- Method: `POST`
- Path: `/api/hdc/committees/{committee_id}/recommendation`
- Inputs:
  - `include_advisory_votes`
  - `force_recompute`
- Outputs:
  - `recommendation_type`
  - `recommendation_status`
  - `recommendation_payload`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Decision Owner

### Escalate Committee Conflict
- Purpose: escalate split or blocked committee state
- Method: `POST`
- Path: `/api/hdc/committees/{committee_id}/escalate`
- Inputs:
  - `escalation_type`
  - `escalation_reason`
  - `target_role`
- Outputs:
  - `escalation_id`
  - `escalation_status`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Decision Owner
  - Governance Reviewer where required

### Finalize Committee Outcome
- Purpose: finalize committee recommendation and hand off downstream
- Method: `POST`
- Path: `/api/hdc/committees/{committee_id}/finalize`
- Inputs:
  - `final_recommendation_type`
  - `finalization_reason`
- Outputs:
  - `committee_outcome`
  - `downstream_handoff_status`
- Permissions:
  - Hiring Manager
  - Decision Owner
  - Leadership Approver where required

### Fetch Committee Timeline
- Purpose: view end-to-end committee lifecycle
- Method: `GET`
- Path: `/api/hdc/committees/{committee_id}/timeline`
- Outputs:
  - `timeline_events`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Leadership Approver
  - Governance Reviewer

### Fetch Dissent Log
- Purpose: inspect dissent and minority positions
- Method: `GET`
- Path: `/api/hdc/committees/{committee_id}/dissent`
- Outputs:
  - `dissent_log`
- Permissions:
  - Hiring Manager
  - Decision Owner
  - Leadership Approver
  - Governance Reviewer

### Fetch Escalation History
- Purpose: inspect escalations and their outcomes
- Method: `GET`
- Path: `/api/hdc/committees/{committee_id}/escalations`
- Outputs:
  - `escalation_history`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Leadership Approver
  - Governance Reviewer

### Fetch Audit Trail
- Purpose: retrieve immutable committee audit history
- Method: `GET`
- Path: `/api/hdc/committees/{committee_id}/audit`
- Outputs:
  - `audit_events`
- Permissions:
  - Governance Reviewer
  - Leadership Approver
  - Authorized admins

## 4. UI Architecture

Frontend principles:
- role-based screen visibility
- explicit status and quorum visibility
- audit and decision history always available to authorized users
- structured comparison cards and evidence summaries
- clean enterprise workflow layout

### Recruiter UI

#### Committee Dashboard
- committee queue
- pending assignments
- review progress
- quorum state
- escalation flags

#### Committee Creation Flow
- choose committee mode
- define decision mode
- set quorum rule
- set optional weighted voting

#### Member Assignment Screen
- assign members by role
- mark required versus advisory members
- configure vote weight
- replace unavailable members

#### Committee Status Tracker
- member completion state
- pending votes
- recommendation readiness
- handoff state

#### Conflict / Escalation Tracker
- split vote indicator
- missing quorum indicator
- escalation owner
- escalation outcome

### Committee Member UI

#### Assigned Candidate Review Screen
- candidate summary
- interview evidence summary
- scorecard summary
- panel feedback highlights
- analytics/gov flags where permitted

#### Interview Result Summary
- per-engine evidence cards
- composite summary if applicable
- recruiter notes
- comparison summary where allowed

#### Feedback Entry Screen
- structured review form
- recommendation notes
- submit review status

#### Voting Interface
- vote selection
- rationale field
- visibility into whether vote is weighted
- submission state

#### Dissent Capture Screen
- dissent reason
- disagreement category
- mandatory dissent note when required

### Hiring Manager / Leadership UI

#### Committee Overview
- committee composition
- required members
- voting mode
- review progress

#### Vote Summary
- majority or unanimous status
- weighted results
- tie or conflict indicators
- pending critical voters

#### Recommendation View
- recommendation type
- evidence summary
- dissent summary
- confidence and blockers

#### Escalation Review
- escalation trigger
- escalation context
- override actions
- resolution path

#### Final Committee Outcome Screen
- final committee recommendation
- override history
- downstream approval or offer handoff
- audit timeline

## 5. Execution Flow

1. Candidate completes interview process
2. Decision Engine creates decision context
3. Hiring committee is created or an existing committee template is selected
4. Members are assigned with required/advisory status and optional vote weights
5. Committee review is activated
6. Members review candidate evidence, scorecards, feedback, and analytics indicators
7. Members submit structured feedback and vote
8. Quorum validation runs
9. Recommendation is generated from vote mode, required-member state, and evidence
10. Conflict and split-decision logic runs if consensus is not reached
11. Escalation occurs if tie, split, missing mandatory vote, or governance rule requires higher review
12. Final committee outcome is stored
13. Output passes to approval engine or offer layer

## 6. Edge Cases

- Committee member not responding
  - reminder and escalation path starts; quorum can remain blocked until replacement or override
- Quorum not met
  - recommendation cannot finalize unless override policy allows escalation path
- Tie vote
  - conflict record created and escalation or tie-break rule applied
- Split committee
  - dissent captured; escalation or leadership review required if no valid consensus
- Leadership override
  - allowed only through explicit override action with reason and audit trail
- Member replaced mid-review
  - prior review/vote locked in audit; replacement gets fresh assignment; stale required-member state recomputed
- Stale vote after candidate data changed
  - vote marked stale; member must reconfirm or resubmit before quorum passes
- Decision reopened after new evidence
  - reopen only if policy allows; prior recommendation remains in audit history
- Committee finalized but approval later rejected
  - final committee outcome remains stored, but downstream overall decision state reopens or routes back for rework
- Audit trail inconsistency prevention
  - committee finalization, escalations, and overrides use immutable append-only audit writes with transaction boundary enforcement

## 7. Enterprise Features

- configurable committee modes
- required versus advisory member modeling
- quorum validation and weighted voting
- unanimous and majority decision support
- dissent and minority-position capture
- leadership override with governed audit
- escalation engine for split or blocked committees
- role-based enterprise UI
- immutable audit-ready committee history
- tenant-scoped operation with candidate-global rule preserved

## 8. Integration Mapping

### Decision Engine
- Consumes:
  - `decision_id`
  - decision context
  - aggregated evidence summary
- Produces:
  - committee recommendation
  - committee outcome status
- Events:
  - `hdc.committee.created`
  - `hdc.committee.finalized`
- Downstream:
  - Approval Engine
  - Offer layer

### Interview Scorecards
- Consumes:
  - published scorecard summaries and normalized scores
- Produces:
  - evidence cards for committee review
- Events:
  - no direct write-back; read-only evidence consumption
- Downstream:
  - Committee review UI
  - Recommendation generation

### AI Interview Results
- Consumes:
  - AI interview summary, transcript highlights, scores, flags
- Produces:
  - evidence inputs for committee context
- Events:
  - no direct write-back
- Downstream:
  - Review workspace
  - Recommendation engine

### Panel Feedback
- Consumes:
  - panelist feedback summaries and dissent notes from ICC
- Produces:
  - structured context for committee review
- Events:
  - no direct write-back
- Downstream:
  - Voting and recommendation

### Approval Engine
- Consumes:
  - finalized committee recommendation
  - escalation outcomes
- Produces:
  - approval status
  - rejection/rework outcome
- Events:
  - `hdc.committee.recommendation.sent_for_approval`
- Downstream:
  - Final decision path
  - Offer engine

### Governance Layer
- Consumes:
  - override, dissent, escalation, and reopening events
- Produces:
  - governance blocks
  - review requirements
- Events:
  - `hdc.committee.escalated`
  - `hdc.committee.override.requested`
- Downstream:
  - Approval and audit consumers

### Audit Layer
- Consumes:
  - all committee lifecycle events
- Produces:
  - immutable committee audit history
- Events:
  - `hdc.committee.audit.logged`
- Downstream:
  - Governance review
  - compliance reporting

### Analytics Layer
- Consumes:
  - committee throughput, dissent, escalation, and outcome signals
- Produces:
  - decision latency metrics
  - committee conflict analytics
- Events:
  - `hdc.committee.metric.updated`
- Downstream:
  - HDC intelligence layers
  - operational dashboards
