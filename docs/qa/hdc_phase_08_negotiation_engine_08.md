# HDC-NEGOTIATION-ENGINE-08

## 1. System Architecture

Shared engine name: `NegotiationEngine`

Purpose:
- manage structured pre-offer and post-offer negotiation workflows between company-side stakeholders and candidate-related offer discussion inputs
- ensure negotiation is controlled, auditable, policy-safe, and always linked to approved or approval-trackable compensation structures
- act as the formal workflow layer between compensation design and final offer release

System placement:
- Candidate Pipeline
- Interview Command Center
- Hiring Decision Command Center
  - Decision Engine
  - Hiring Committee Engine
  - Candidate Comparison Engine
  - Decision Approval Engine
  - Offer Intelligence Engine
  - Compensation Engine
  - Negotiation Engine
- Offer Management / Offer Release / Acceptance

Core components:
1. `Negotiation Workflow Engine`
2. `Negotiation Round Engine`
3. `Candidate Ask Capture Engine`
4. `Company Counter Engine`
5. `Concession Tracking Engine`
6. `Approval-Linked Negotiation Engine`
7. `Compensation Delta Engine`
8. `Negotiation Outcome Engine`
9. `Negotiation Risk Engine`
10. `Negotiation Audit Engine`

Supported negotiation modes:
- `pre_offer_negotiation`
- `post_offer_negotiation`
- `recruiter_led_negotiation`
- `hiring_manager_assisted_negotiation`
- `compensation_led_negotiation`
- `executive_leadership_negotiation`
- `budget_sensitive_negotiation`
- `one_round_negotiation`
- `multi_round_negotiation`
- `exception_driven_negotiation`

Role architecture:
- Recruiter
- Hiring Manager
- Compensation Analyst
- HR / HRBP
- Finance Reviewer
- Business Head
- Leadership Approver
- Negotiation Owner

Operating model:
- negotiation case begins from a frozen compensation package or an approved package baseline
- candidate asks and responses are represented through controlled records, recruiter-entered updates, or integrated portal signals, never through direct internal engine access
- company counters are policy-validated before they become active negotiation positions
- negotiation rounds continue until success, pause, withdrawal, failure, or handoff
- final agreed package becomes a frozen negotiation outcome and is then handed to offer release
- candidate remains a global entity with tenant association only

Negotiation policy defaults:
- recruiter cannot directly activate a company counter outside allowed thresholds unless comp/approval rules allow it
- compensation analyst signoff is required before counter activation when compensation delta breaches configurable limits or affects protected components
- finance or leadership approval is required above configured package or concession thresholds
- candidate ask can exceed band and still be recorded for discussion, but cannot activate internal acceptance without exception path
- negotiation can reopen after `agreed` only through governed reopen workflow before final release
- negotiated package creates a new approved/frozen version lineage rather than silently overwriting prior approved package
- failed negotiation can route candidate to `hold`, `reject`, or `reconsider` path based on policy and user action

Architecture layers:
- `Case Management Layer`
- `Round & Position Layer`
- `Delta & Concession Layer`
- `Approval Dependency Layer`
- `Outcome & Handoff Layer`
- `Audit Layer`

## 2. Database Design

Primary entities:
- `negotiation_case`
- `negotiation_round`
- `negotiation_position`
- `negotiation_candidate_request`
- `negotiation_company_counter`
- `negotiation_delta_record`
- `negotiation_concession_record`
- `negotiation_approval_dependency`
- `negotiation_outcome`
- `negotiation_audit_log`

Required fields across entities:
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `offer_intelligence_id`
- `compensation_package_id`
- `negotiation_case_id`
- `round_number`
- `negotiation_status`
- `candidate_expected_ctc`
- `candidate_expected_fixed`
- `candidate_expected_bonus`
- `company_counter_ctc`
- `company_counter_fixed`
- `company_counter_bonus`
- `delta_amount`
- `delta_reason`
- `concession_status`
- `approval_dependency_status`
- `final_negotiation_outcome`
- `risk_level`
- `owner_user_id`
- `created_by`
- `created_at`
- `updated_at`

Recommended entity details:

### `negotiation_case`
- `id`
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `offer_intelligence_id`
- `compensation_package_id`
- `negotiation_mode`
- `negotiation_status`
- `owner_user_id`
- `max_round_count`
- `current_round_number`
- `created_by`
- `created_at`
- `updated_at`

### `negotiation_round`
- `id`
- `tenant_id`
- `negotiation_case_id`
- `round_number`
- `round_status`
- `started_at`
- `closed_at`
- `created_at`
- `updated_at`

### `negotiation_position`
- `id`
- `tenant_id`
- `negotiation_case_id`
- `round_number`
- `position_type`
- `position_payload`
- `position_status`
- `created_at`
- `updated_at`

### `negotiation_candidate_request`
- `id`
- `tenant_id`
- `negotiation_case_id`
- `round_number`
- `candidate_expected_ctc`
- `candidate_expected_fixed`
- `candidate_expected_bonus`
- `candidate_request_payload`
- `captured_by_user_id`
- `created_at`
- `updated_at`

### `negotiation_company_counter`
- `id`
- `tenant_id`
- `negotiation_case_id`
- `round_number`
- `company_counter_ctc`
- `company_counter_fixed`
- `company_counter_bonus`
- `company_counter_payload`
- `counter_status`
- `created_at`
- `updated_at`

### `negotiation_delta_record`
- `id`
- `tenant_id`
- `negotiation_case_id`
- `round_number`
- `delta_amount`
- `delta_reason`
- `delta_payload`
- `created_at`
- `updated_at`

### `negotiation_concession_record`
- `id`
- `tenant_id`
- `negotiation_case_id`
- `round_number`
- `concession_type`
- `concession_status`
- `concession_payload`
- `created_at`
- `updated_at`

### `negotiation_approval_dependency`
- `id`
- `tenant_id`
- `negotiation_case_id`
- `round_number`
- `approval_dependency_status`
- `dependency_payload`
- `created_at`
- `updated_at`

### `negotiation_outcome`
- `id`
- `tenant_id`
- `negotiation_case_id`
- `final_negotiation_outcome`
- `finalized_package_id`
- `outcome_reason`
- `finalized_at`
- `created_at`
- `updated_at`

### `negotiation_audit_log`
- `id`
- `tenant_id`
- `negotiation_case_id`
- `round_number`
- `event_type`
- `actor_user_id`
- `audit_payload`
- `created_at`

## 3. API Structure

### Create Negotiation Case
- Purpose: create negotiation workflow from compensation package baseline
- Method: `POST`
- Path: `/api/hdc/negotiations`
- Inputs:
  - `decision_id`
  - `offer_intelligence_id`
  - `compensation_package_id`
  - `negotiation_mode`
- Outputs:
  - `negotiation_case_id`
  - `negotiation_status`
- Permissions:
  - Recruiter
  - Negotiation Owner
  - HR / HRBP

### Fetch Negotiation Case
- Purpose: fetch negotiation case details
- Method: `GET`
- Path: `/api/hdc/negotiations/{negotiation_case_id}`
- Outputs:
  - `negotiation_case`
  - `current_round`
  - `status_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Analyst
  - HR / HRBP
  - Finance Reviewer
  - Business Head
  - Leadership Approver

### Update Negotiation Case
- Purpose: update owner, mode, limits, or internal metadata
- Method: `PATCH`
- Path: `/api/hdc/negotiations/{negotiation_case_id}`
- Inputs:
  - `case_update_payload`
  - `change_reason`
- Outputs:
  - `updated_case`
- Permissions:
  - Negotiation Owner
  - HR / HRBP
  - Governance Reviewer where required

### Start Negotiation Round
- Purpose: open a new round
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/rounds`
- Inputs:
  - `round_note`
- Outputs:
  - `round_number`
  - `round_status`
- Permissions:
  - Recruiter
  - Negotiation Owner
  - HR / HRBP

### Close Negotiation Round
- Purpose: close active round
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/rounds/{round_number}/close`
- Inputs:
  - `closure_reason`
- Outputs:
  - `round_status`
- Permissions:
  - Recruiter
  - Negotiation Owner
  - HR / HRBP

### Freeze Negotiation State
- Purpose: freeze current state before approval or offer release
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/freeze`
- Inputs:
  - `freeze_reason`
- Outputs:
  - `freeze_status`
  - `frozen_state_reference`
- Permissions:
  - Negotiation Owner
  - Compensation Analyst
  - HR / HRBP

### Fetch Negotiation Summary
- Purpose: fetch high-level summary
- Method: `GET`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/summary`
- Outputs:
  - `negotiation_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Analyst
  - HR / HRBP
  - Leadership Approver

### Fetch Negotiation Timeline
- Purpose: fetch round-by-round timeline
- Method: `GET`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/timeline`
- Outputs:
  - `timeline_events`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Analyst
  - HR / HRBP
  - Governance Reviewer

### Record Candidate Request
- Purpose: capture candidate ask
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/candidate-request`
- Inputs:
  - `candidate_expected_ctc`
  - `candidate_expected_fixed`
  - `candidate_expected_bonus`
  - `candidate_request_payload`
- Outputs:
  - `request_status`
- Permissions:
  - Recruiter
  - Negotiation Owner
  - HR / HRBP
  - Integrated candidate portal adapter if added later

### Record Company Counter
- Purpose: record internal counter proposal
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/company-counter`
- Inputs:
  - `company_counter_ctc`
  - `company_counter_fixed`
  - `company_counter_bonus`
  - `company_counter_payload`
- Outputs:
  - `counter_status`
  - `approval_dependency_status`
- Permissions:
  - Compensation Analyst
  - HR / HRBP
  - Recruiter within allowed bounds

### Record Recruiter Negotiation Note
- Purpose: capture structured recruiter note
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/notes`
- Inputs:
  - `note_payload`
- Outputs:
  - `note_status`
- Permissions:
  - Recruiter
  - Negotiation Owner
  - HR / HRBP

### Capture Compensation Delta
- Purpose: record difference between ask and company position
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/delta`
- Inputs:
  - `delta_reason`
- Outputs:
  - `delta_record`
- Permissions:
  - Compensation Analyst
  - HR / HRBP
  - System

### Add Concession Entry
- Purpose: add concession entry in current round
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/concessions`
- Inputs:
  - `concession_type`
  - `concession_payload`
- Outputs:
  - `concession_status`
- Permissions:
  - Compensation Analyst
  - HR / HRBP
  - Recruiter where allowed

### Mark Concession Accepted / Rejected
- Purpose: close concession state
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/concessions/{concession_id}/resolve`
- Inputs:
  - `concession_status`
  - `resolution_note`
- Outputs:
  - `updated_concession`
- Permissions:
  - Negotiation Owner
  - HR / HRBP
  - Compensation Analyst

### Recompute Negotiated Package Position
- Purpose: recompute current negotiated package
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/recompute`
- Outputs:
  - `current_negotiated_position`
  - `validation_summary`
- Permissions:
  - Compensation Analyst
  - HR / HRBP
  - System

### Compare Round-To-Round Movement
- Purpose: compare movement across rounds
- Method: `GET`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/round-movement`
- Outputs:
  - `round_movement_comparison`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Analyst
  - Leadership Approver

### Fetch Negotiation Approval Dependencies
- Purpose: retrieve negotiation-linked approval requirements
- Method: `GET`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/approval-dependencies`
- Outputs:
  - `approval_dependencies`
- Permissions:
  - Compensation Analyst
  - HR / HRBP
  - Finance Reviewer
  - Governance Reviewer

### Validate Counter Against Policy
- Purpose: validate counter-offer against policy and package boundaries
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/validate-counter`
- Inputs:
  - `counter_payload`
- Outputs:
  - `validation_result`
- Permissions:
  - Compensation Analyst
  - HR / HRBP
  - Finance Reviewer
  - Governance Reviewer

### Trigger Exception Approval
- Purpose: trigger approval when negotiation exceeds approved boundaries
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/trigger-exception-approval`
- Inputs:
  - `exception_reason`
- Outputs:
  - `exception_status`
  - `approval_workflow_id`
- Permissions:
  - Compensation Analyst
  - HR / HRBP
  - Governance Reviewer

### Fetch Negotiation Readiness For Offer Release
- Purpose: determine readiness for release
- Method: `GET`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/readiness`
- Outputs:
  - `negotiation_readiness_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Analyst
  - HR / HRBP
  - Offer Owner

### Block Negotiation Closure If Required Approvals Missing
- Purpose: enforce missing-approval block
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/validate-closure`
- Outputs:
  - `closure_validation`
- Permissions:
  - System
  - Governance Reviewer
  - Compensation Analyst

### Mark Negotiation Success
- Purpose: mark successful negotiation
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/success`
- Inputs:
  - `success_note`
- Outputs:
  - `negotiation_status`
- Permissions:
  - Negotiation Owner
  - HR / HRBP

### Mark Negotiation Failed
- Purpose: mark failed negotiation
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/failed`
- Inputs:
  - `failure_reason`
- Outputs:
  - `negotiation_status`
  - `fallback_path_options`
- Permissions:
  - Negotiation Owner
  - HR / HRBP
  - Hiring Manager

### Mark Negotiation Paused
- Purpose: pause negotiation
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/pause`
- Inputs:
  - `pause_reason`
- Outputs:
  - `negotiation_status`
- Permissions:
  - Recruiter
  - Negotiation Owner
  - HR / HRBP

### Mark Negotiation Withdrawn
- Purpose: mark negotiation withdrawn
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/withdrawn`
- Inputs:
  - `withdrawal_reason`
- Outputs:
  - `negotiation_status`
- Permissions:
  - Recruiter
  - Negotiation Owner
  - HR / HRBP

### Finalize Negotiated Package
- Purpose: freeze agreed negotiated package
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/finalize-package`
- Inputs:
  - `finalization_reason`
- Outputs:
  - `finalized_package_id`
  - `final_negotiation_outcome`
- Permissions:
  - Compensation Analyst
  - HR / HRBP
  - Offer Owner

### Handoff To Offer Release
- Purpose: pass negotiated package to release workflow
- Method: `POST`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/handoff`
- Inputs:
  - `handoff_reason`
- Outputs:
  - `handoff_status`
  - `offer_release_reference`
- Permissions:
  - Offer Owner
  - HR / HRBP

### Fetch Negotiation Audit Trail
- Purpose: retrieve audit history
- Method: `GET`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/audit`
- Outputs:
  - `audit_events`
- Permissions:
  - Governance Reviewer
  - Leadership Approver
  - Authorized admins

### Fetch Concession History
- Purpose: retrieve concessions across rounds
- Method: `GET`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/concessions`
- Outputs:
  - `concession_history`
- Permissions:
  - Recruiter
  - Compensation Analyst
  - HR / HRBP
  - Governance Reviewer

### Fetch Exception History
- Purpose: retrieve negotiation exceptions
- Method: `GET`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/exceptions`
- Outputs:
  - `exception_history`
- Permissions:
  - Compensation Analyst
  - Governance Reviewer
  - Leadership Approver

### Fetch Negotiation Rationale Log
- Purpose: retrieve rationale trail for asks, counters, and decisions
- Method: `GET`
- Path: `/api/hdc/negotiations/{negotiation_case_id}/rationale`
- Outputs:
  - `rationale_log`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Analyst
  - HR / HRBP
  - Governance Reviewer

## 4. UI Architecture

Frontend principles:
- round-by-round negotiation timeline
- side-by-side ask versus counter comparison
- compensation delta cards
- approval dependency warnings
- concession audit visibility
- explicit status states: active, paused, approved, failed, handed-off
- clean enterprise workflow layout
- no candidate access to internal UI

### Recruiter UI

#### Negotiation Dashboard
- active negotiation cases
- owner visibility
- round status
- stalled or blocked cases

#### Candidate Expectation View
- expected CTC, fixed, bonus asks
- expectation history
- competing-offer markers

#### Negotiation Round Tracker
- round number
- current ask/counter
- round status
- pending approvals

#### Current Company Position Screen
- current internal counter
- approved range visibility
- readiness to communicate

#### Concession Log
- concessions by round
- accepted/rejected status
- rationale trail

#### Negotiation Risk Indicator
- acceptance risk
- policy risk
- budget risk
- over-round-count warning

#### Offer-Release Readiness Panel
- final negotiated package state
- missing approvals
- handoff readiness

### Hiring Manager / Business UI

#### Negotiation Summary View
- negotiation status
- business context
- final direction needed

#### Candidate Ask vs Company Counter View
- side-by-side financial comparison
- deltas and tradeoffs

#### Budget Impact Panel
- current package vs budget
- premium or exception impact

#### Decision-Needed Alerts
- pending business decisions
- escalation needs
- threshold breaches

#### Negotiation Outcome Screen
- success/failure/pause/withdrawn state
- fallback path visibility

### Compensation / Finance UI

#### Compensation Delta Screen
- delta by component
- round movement comparison
- threshold visibility

#### Policy And Exception Validation Panel
- band/policy validation
- hard-blocks and warnings
- exception requirement

#### Counter-Offer Builder
- counter package editor
- component adjustments
- approval dependency visibility

#### Approval Dependency Tracker
- compensation, finance, leadership approvals
- SLA visibility

#### Negotiation Package Comparison View
- baseline vs negotiated package
- version comparison
- frozen package references

### Leadership / Approval UI

#### Exception-Based Negotiation Approval Queue
- high-risk counters
- over-threshold concessions
- executive negotiations

#### High-Risk Negotiation Dashboard
- stalled critical negotiations
- policy-sensitive cases
- business impact summary

#### Final Negotiation Sign-Off Screen
- final negotiated position
- approval dependencies
- downstream release readiness

#### Negotiation Audit And Rationale Viewer
- round history
- rationale by actor
- concession and approval history

## 5. Execution Flow

1. Approved compensation package is ready for candidate discussion
2. Negotiation case is created
3. Candidate expectation or counter-demand is captured
4. Internal counter position is prepared
5. Delta and concession analysis run
6. Policy, budget, and exception validation run
7. Required approvals are triggered if thresholds are exceeded
8. Negotiation rounds continue until agreement, pause, withdrawal, or failure
9. Final negotiated package is frozen
10. Negotiation outcome is stored
11. Agreed package is handed off to offer release workflow

## 6. Edge Cases

- Candidate ask captured without internal approved baseline
  - case can open, but company counter activation is blocked until baseline package exists
- Recruiter promises amount not internally approved
  - recorded as policy breach/risk note; unofficial promise cannot become active counter
- Negotiation exceeds allowed round count
  - escalate or force pause/final decision path according to policy
- Concession approved in one round but reversed later
  - prior concession remains in audit; reversal requires explicit new decision and possible approval
- Package changed during active negotiation due to policy update
  - active case marked stale; revalidation required before next counter or finalization
- Candidate verbally agrees but internal approval not complete
  - case can be tentatively marked agreed-in-principle, but cannot hand off to offer release
- Multiple stakeholders update negotiation simultaneously
  - optimistic locking or round-state locking required; latest valid write does not overwrite prior audit entries
- Negotiation paused then resumed after stale compensation data
  - compensation must be refreshed and validated before resuming
- Negotiation successful but offer release blocked by downstream approval
  - negotiation outcome stays successful; handoff remains blocked until downstream clearance
- Failed negotiation but candidate later re-engages
  - governed reopen path creates resumed case or new round lineage
- Audit continuity across reopened negotiation case
  - append-only timeline retained across all reopen cycles
- Negotiated package conflicts with frozen compensation snapshot
  - new negotiated package version created; prior frozen baseline preserved as historical source

## 7. Enterprise Features

- tenant-scoped negotiation cases
- pre-offer and post-offer negotiation support
- round-based negotiation workflow
- structured ask, counter, delta, and concession tracking
- approval-linked counter activation
- policy-safe negotiated package computation
- pause, withdraw, fail, reopen, and handoff states
- frozen negotiated package lineage
- role-based enterprise UI
- auditable negotiation lifecycle

## 8. Integration Mapping

### Compensation Engine
- Consumes:
  - frozen compensation baseline
  - package version data
- Produces:
  - negotiated package candidate
  - delta comparison context
- Events:
  - `hdc.negotiation.baseline.loaded`
- Downstream:
  - counter building and finalization

### Offer Intelligence Engine
- Consumes:
  - expectation and competitiveness context
  - negotiation readiness signals
- Produces:
  - negotiation risk and concession context
- Events:
  - `hdc.negotiation.intelligence.context.attached`
- Downstream:
  - recruiter and comp negotiation views

### Decision Approval Engine
- Consumes:
  - approval lineage and approval thresholds
- Produces:
  - negotiation-side approval dependency rules
- Events:
  - `hdc.negotiation.approval.rules.loaded`
- Downstream:
  - exception and approval flows

### Offer Management / Offer Release
- Consumes:
  - finalized negotiated package
  - final negotiation outcome
- Produces:
  - offer release workflow initiation
- Events:
  - `hdc.negotiation.ready.for.offer.release`
- Downstream:
  - offer authoring and release

### Governance Layer
- Consumes:
  - out-of-policy counters
  - reopened negotiations
  - promise-risk or override cases
- Produces:
  - governance block/warn states
  - approval or exception requirements
- Events:
  - `hdc.negotiation.exception.required`
- Downstream:
  - audit and approval review

### Approval Engine
- Consumes:
  - negotiation approval dependencies
  - exception approval triggers
- Produces:
  - approval workflow state
- Events:
  - `hdc.negotiation.routed.for.approval`
- Downstream:
  - negotiation progression

### Analytics Layer
- Consumes:
  - round count
  - concession rates
  - negotiation success/fail rates
  - delay and stall metrics
- Produces:
  - negotiation intelligence metrics
- Events:
  - `hdc.negotiation.metric.updated`
- Downstream:
  - HDC intelligence and operations

### Audit Layer
- Consumes:
  - all round, ask, counter, concession, approval, freeze, and outcome events
- Produces:
  - immutable negotiation audit trail
- Events:
  - `hdc.negotiation.audit.logged`
- Downstream:
  - governance and compliance review

### Notification / Communication Layer
- Consumes:
  - negotiation round starts
  - approval needs
  - stale or blocked states
  - handoff readiness
- Produces:
  - notifications and reminders to internal stakeholders
- Events:
  - `hdc.negotiation.notification.required`
- Downstream:
  - recruiter, comp, finance, leadership users
