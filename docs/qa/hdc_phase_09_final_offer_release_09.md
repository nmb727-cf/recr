# HDC-FINAL-OFFER-RELEASE-09

## 1. System Architecture

Shared engine name: `FinalOfferReleaseEngine`

Purpose:
- convert the fully approved and negotiation-closed hiring package into an officially releasable offer
- enforce readiness validation, approval closure, policy compliance, document binding, controlled dispatch, acceptance handoff, and recall governance
- serve as the final internal control layer before candidate-facing offer delivery

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
  - Final Offer Release Engine
- Offer Acceptance / Pre-boarding / Onboarding

Core components:
1. `Offer Release Readiness Engine`
2. `Offer Packet Assembly Engine`
3. `Offer Approval Closure Engine`
4. `Policy Compliance Validation Engine`
5. `Final Compensation Lock Engine`
6. `Offer Document Binding Engine`
7. `Offer Dispatch Engine`
8. `Offer Acceptance Readiness Engine`
9. `Offer Release Audit Engine`
10. `Release Exception / Recall Engine`

Supported release modes:
- `standard_offer_release`
- `negotiated_offer_release`
- `expedited_offer_release`
- `executive_leadership_offer_release`
- `campus_bulk_hiring_offer_release`
- `exception_approved_offer_release`
- `staged_offer_release`
- `recruiter_assisted_manual_release`
- `system_controlled_release`
- `deferred_scheduled_release`

Role architecture:
- Recruiter
- Hiring Manager
- HR / HRBP
- Compensation Analyst
- Finance Reviewer
- Business Head
- Leadership Approver
- Offer Release Owner
- Governance Reviewer

Operating model:
- release begins only after decision approval is final, compensation package is frozen, and negotiation is closed or explicitly not applicable
- release record acts as the controlled source of truth for dispatch readiness and final released packet
- offer packet includes compensation snapshot, approval evidence, negotiation closure evidence, and bound document version
- dispatch can be immediate, scheduled, or manual-assist controlled
- candidate remains a global entity with tenant association only
- candidate never accesses internal release UI, only downstream candidate-facing offer delivery

Release policy defaults:
- recruiter cannot directly release high-risk, executive, or exception-based offers unless policy explicitly allows it
- HR or governance signoff can be mandatory before dispatch depending on tenant policy and release mode
- scheduled release is allowed only after final approval closure
- release is blocked if negotiation is not formally closed where negotiation is required
- released offers can be recalled only under governed policy paths with audit and downstream impact handling
- recalled offer creates a new release lineage state; prior release remains immutable historical record
- advisory approvals may be missing without blocking only if tenant policy marks them non-blocking
- document regeneration after release is versioned, never silent overwrite

Architecture layers:
- `Readiness & Validation Layer`
- `Packet & Document Layer`
- `Dispatch & Scheduling Layer`
- `Acceptance Handoff Layer`
- `Exception / Recall Layer`
- `Audit Layer`

## 2. Database Design

Primary entities:
- `final_offer_release`
- `offer_release_readiness`
- `offer_release_packet`
- `offer_release_document_binding`
- `offer_release_approval_closure`
- `offer_release_dispatch`
- `offer_release_schedule`
- `offer_release_exception`
- `offer_release_recall`
- `offer_release_audit_log`

Required fields across entities:
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `offer_intelligence_id`
- `compensation_package_id`
- `negotiation_case_id`
- `final_offer_release_id`
- `release_mode`
- `release_status`
- `readiness_status`
- `approval_closure_status`
- `policy_validation_status`
- `document_binding_status`
- `dispatch_status`
- `acceptance_readiness_status`
- `scheduled_release_at`
- `released_at`
- `recalled_at`
- `exception_status`
- `owner_user_id`
- `created_by`
- `created_at`
- `updated_at`

Recommended entity details:

### `final_offer_release`
- `id`
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `offer_intelligence_id`
- `compensation_package_id`
- `negotiation_case_id`
- `release_mode`
- `release_status`
- `owner_user_id`
- `created_by`
- `created_at`
- `updated_at`

### `offer_release_readiness`
- `id`
- `tenant_id`
- `final_offer_release_id`
- `readiness_status`
- `blocker_payload`
- `acceptance_readiness_status`
- `validated_at`
- `created_at`
- `updated_at`

### `offer_release_packet`
- `id`
- `tenant_id`
- `final_offer_release_id`
- `packet_status`
- `packet_payload`
- `frozen_snapshot_status`
- `frozen_at`
- `created_at`
- `updated_at`

### `offer_release_document_binding`
- `id`
- `tenant_id`
- `final_offer_release_id`
- `document_template_id`
- `document_version`
- `document_binding_status`
- `bound_at`
- `created_at`
- `updated_at`

### `offer_release_approval_closure`
- `id`
- `tenant_id`
- `final_offer_release_id`
- `approval_closure_status`
- `closure_payload`
- `validated_at`
- `created_at`
- `updated_at`

### `offer_release_dispatch`
- `id`
- `tenant_id`
- `final_offer_release_id`
- `dispatch_channel`
- `dispatch_status`
- `delivery_status`
- `released_at`
- `delivered_at`
- `created_at`
- `updated_at`

### `offer_release_schedule`
- `id`
- `tenant_id`
- `final_offer_release_id`
- `scheduled_release_at`
- `schedule_status`
- `reschedule_count`
- `created_at`
- `updated_at`

### `offer_release_exception`
- `id`
- `tenant_id`
- `final_offer_release_id`
- `exception_type`
- `exception_status`
- `exception_reason`
- `created_at`
- `updated_at`

### `offer_release_recall`
- `id`
- `tenant_id`
- `final_offer_release_id`
- `recalled_at`
- `recall_status`
- `recall_reason`
- `candidate_opened_status`
- `created_at`
- `updated_at`

### `offer_release_audit_log`
- `id`
- `tenant_id`
- `final_offer_release_id`
- `event_type`
- `actor_user_id`
- `audit_payload`
- `created_at`

## 3. API Structure

### Create Offer Release Record
- Purpose: initialize final release workflow
- Method: `POST`
- Path: `/api/hdc/offers/releases`
- Inputs:
  - `decision_id`
  - `offer_intelligence_id`
  - `compensation_package_id`
  - `negotiation_case_id`
  - `release_mode`
- Outputs:
  - `final_offer_release_id`
  - `release_status`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Offer Release Owner

### Fetch Offer Release Record
- Purpose: fetch full release record
- Method: `GET`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}`
- Outputs:
  - `release_record`
  - `status_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - HR / HRBP
  - Compensation Analyst
  - Finance Reviewer
  - Business Head
  - Leadership Approver
  - Governance Reviewer

### Fetch Release Readiness Summary
- Purpose: retrieve final readiness state
- Method: `GET`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/readiness`
- Outputs:
  - `readiness_summary`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Offer Release Owner
  - Governance Reviewer

### Validate Release Readiness
- Purpose: validate all blockers and dependencies
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/validate-readiness`
- Outputs:
  - `readiness_status`
  - `blocker_list`
- Permissions:
  - HR / HRBP
  - Offer Release Owner
  - Governance Reviewer

### Validate Approvals Closed
- Purpose: confirm all required approvals are fully closed
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/validate-approvals`
- Outputs:
  - `approval_closure_status`
- Permissions:
  - HR / HRBP
  - Governance Reviewer
  - Offer Release Owner

### Validate Compensation Locked
- Purpose: confirm compensation package is frozen
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/validate-compensation-lock`
- Outputs:
  - `compensation_lock_status`
- Permissions:
  - Compensation Analyst
  - HR / HRBP
  - Governance Reviewer

### Validate Policy Compliance
- Purpose: validate final release against policy and exception state
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/validate-policy`
- Outputs:
  - `policy_validation_status`
  - `policy_blockers`
- Permissions:
  - Governance Reviewer
  - HR / HRBP
  - Finance Reviewer

### Validate Document Readiness
- Purpose: confirm bound document is ready for release
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/validate-documents`
- Outputs:
  - `document_binding_status`
- Permissions:
  - HR / HRBP
  - Offer Release Owner

### Assemble Offer Release Packet
- Purpose: assemble final release packet
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/packet`
- Inputs:
  - `packet_mode`
- Outputs:
  - `packet_id`
  - `packet_status`
- Permissions:
  - HR / HRBP
  - Offer Release Owner
  - Compensation Analyst

### Bind Offer Document Template
- Purpose: bind final document template and version
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/documents/bind`
- Inputs:
  - `document_template_id`
  - `document_version`
- Outputs:
  - `document_binding_status`
- Permissions:
  - HR / HRBP
  - Offer Release Owner

### Attach Compensation Snapshot
- Purpose: attach frozen compensation package evidence
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/packet/compensation`
- Inputs:
  - `compensation_package_id`
- Outputs:
  - `attachment_status`
- Permissions:
  - Compensation Analyst
  - HR / HRBP

### Attach Approval Evidence
- Purpose: attach approval closure evidence
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/packet/approvals`
- Outputs:
  - `attachment_status`
- Permissions:
  - HR / HRBP
  - Governance Reviewer

### Fetch Release Packet
- Purpose: fetch assembled packet
- Method: `GET`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/packet`
- Outputs:
  - `release_packet`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Offer Release Owner
  - Governance Reviewer

### Freeze Release Packet Snapshot
- Purpose: freeze final releasable packet
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/packet/freeze`
- Inputs:
  - `freeze_reason`
- Outputs:
  - `frozen_snapshot_status`
- Permissions:
  - HR / HRBP
  - Offer Release Owner
  - Governance Reviewer where required

### Dispatch Offer
- Purpose: dispatch offer immediately
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/dispatch`
- Inputs:
  - `dispatch_channel`
  - `dispatch_note`
- Outputs:
  - `dispatch_status`
  - `released_at`
- Permissions:
  - Offer Release Owner
  - HR / HRBP
  - Recruiter where policy allows

### Schedule Offer Release
- Purpose: schedule future release
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/schedule`
- Inputs:
  - `scheduled_release_at`
  - `schedule_reason`
- Outputs:
  - `schedule_status`
- Permissions:
  - Offer Release Owner
  - HR / HRBP

### Reschedule Release If Allowed
- Purpose: reschedule pending release
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/schedule/reschedule`
- Inputs:
  - `scheduled_release_at`
  - `reschedule_reason`
- Outputs:
  - `schedule_status`
- Permissions:
  - Offer Release Owner
  - HR / HRBP
  - Governance Reviewer where required

### Cancel Scheduled Release
- Purpose: cancel pending scheduled release
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/schedule/cancel`
- Inputs:
  - `cancel_reason`
- Outputs:
  - `schedule_status`
- Permissions:
  - Offer Release Owner
  - HR / HRBP
  - Governance Reviewer where required

### Fetch Dispatch Status
- Purpose: fetch dispatch and delivery state
- Method: `GET`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/dispatch`
- Outputs:
  - `dispatch_status`
  - `delivery_status`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Offer Release Owner

### Retry Dispatch If Allowed
- Purpose: retry failed dispatch with idempotency protection
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/dispatch/retry`
- Inputs:
  - `retry_reason`
- Outputs:
  - `dispatch_status`
- Permissions:
  - Offer Release Owner
  - HR / HRBP

### Mark Release Delivered
- Purpose: mark delivery confirmation state
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/dispatch/delivered`
- Outputs:
  - `delivery_status`
- Permissions:
  - System
  - Offer Release Owner

### Prepare Acceptance Flow Handoff
- Purpose: prepare acceptance workflow handoff
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/acceptance/prepare`
- Outputs:
  - `acceptance_readiness_status`
- Permissions:
  - Offer Release Owner
  - HR / HRBP

### Fetch Acceptance Readiness
- Purpose: fetch acceptance handoff readiness
- Method: `GET`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/acceptance/readiness`
- Outputs:
  - `acceptance_readiness`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Offer Release Owner

### Handoff To Offer Acceptance Workflow
- Purpose: hand off final released offer to acceptance workflow
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/acceptance/handoff`
- Outputs:
  - `handoff_status`
  - `acceptance_workflow_reference`
- Permissions:
  - Offer Release Owner
  - HR / HRBP

### Request Release Exception
- Purpose: request release exception
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/exceptions`
- Inputs:
  - `exception_type`
  - `exception_reason`
- Outputs:
  - `exception_status`
- Permissions:
  - HR / HRBP
  - Offer Release Owner
  - Governance Reviewer

### Approve Release Exception
- Purpose: approve release exception
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/exceptions/{exception_id}/approve`
- Inputs:
  - `approval_note`
- Outputs:
  - `exception_status`
- Permissions:
  - Governance Reviewer
  - Leadership Approver

### Reject Release Exception
- Purpose: reject release exception
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/exceptions/{exception_id}/reject`
- Inputs:
  - `rejection_reason`
- Outputs:
  - `exception_status`
- Permissions:
  - Governance Reviewer
  - Leadership Approver

### Recall Released Offer If Allowed
- Purpose: recall released offer under governed conditions
- Method: `POST`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/recall`
- Inputs:
  - `recall_reason`
- Outputs:
  - `recall_status`
  - `recalled_at`
- Permissions:
  - Governance Reviewer
  - Offer Release Owner
  - Leadership Approver where required

### Fetch Recall History
- Purpose: retrieve recall history
- Method: `GET`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/recalls`
- Outputs:
  - `recall_history`
- Permissions:
  - Governance Reviewer
  - HR / HRBP
  - Leadership Approver

### Fetch Exception History
- Purpose: retrieve release exception history
- Method: `GET`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/exceptions`
- Outputs:
  - `exception_history`
- Permissions:
  - Governance Reviewer
  - HR / HRBP
  - Leadership Approver

### Fetch Release Audit Trail
- Purpose: retrieve immutable release audit history
- Method: `GET`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/audit`
- Outputs:
  - `audit_events`
- Permissions:
  - Governance Reviewer
  - Leadership Approver
  - Authorized admins

### Fetch Release Rationale
- Purpose: fetch rationale for final release decision
- Method: `GET`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/rationale`
- Outputs:
  - `rationale_payload`
- Permissions:
  - HR / HRBP
  - Offer Release Owner
  - Governance Reviewer

### Fetch Readiness Blocker Log
- Purpose: fetch current and historical blockers
- Method: `GET`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/blockers`
- Outputs:
  - `blocker_log`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Offer Release Owner
  - Governance Reviewer

### Fetch Final Frozen Release Snapshot
- Purpose: fetch immutable released packet snapshot
- Method: `GET`
- Path: `/api/hdc/offers/releases/{final_offer_release_id}/snapshot`
- Outputs:
  - `frozen_release_snapshot`
- Permissions:
  - HR / HRBP
  - Offer Release Owner
  - Governance Reviewer
  - Leadership Approver

## 4. UI Architecture

Frontend principles:
- readiness checklist panel
- blocker badges
- frozen offer snapshot view
- document binding visibility
- dispatch timeline
- clear release, delivered, recalled states
- clean enterprise final-authorization layout
- no candidate access to internal release UI

### Recruiter UI

#### Offer Release Dashboard
- active release queue
- pending actions
- release status by candidate

#### Release Readiness Summary
- blocker list
- readiness score/state
- pending dependency indicators

#### Offer Packet Review Screen
- final packet preview
- compensation and negotiation summary
- document bind state

#### Blocker / Dependency Tracker
- missing approval closure
- missing document template
- stale compensation/negotiation link

#### Dispatch Control Panel
- immediate dispatch
- retry control
- delivery state

#### Scheduled Release Tracker
- scheduled releases
- reschedule and cancel controls
- schedule risk badges

### HR / Hiring Manager UI

#### Final Offer Summary View
- final package summary
- release mode
- readiness confirmation

#### Compensation And Negotiation Closure View
- frozen compensation reference
- negotiation closure reference
- stale-state warnings

#### Approval Closure Panel
- mandatory approvals closed
- advisory approvals status
- exception closure state

#### Release Authorization Screen
- final signoff action
- policy and readiness summary
- release note

#### Offer Readiness Confirmation Screen
- final yes/no release state
- blockers and warnings
- dispatch path chosen

### Compensation / Finance / Governance UI

#### Final Compensation Lock Panel
- compensation lock state
- package version lineage
- override or stale-state warnings

#### Policy Compliance Review Screen
- policy fit
- threshold breaches
- exception status

#### Exception / Release Override Screen
- approved exceptions
- pending release override actions
- escalation context

#### Audit Evidence Viewer
- approval evidence
- compensation evidence
- negotiation evidence
- release evidence

#### Recall / Correction Review Screen
- released offer status
- recall request reason
- downstream impact view

### Leadership / Final Approver UI

#### High-Value Release Approval Queue
- executive and high-value offers
- exception-approved releases
- policy-sensitive releases

#### Final Release Decision Screen
- final packet
- risk summary
- signoff controls

#### Exception-Approved Release Summary
- exception lineage
- approval closure state
- readiness confirmation

#### Audit And Rationale Visibility
- full release timeline
- rationale and override visibility
- freeze and recall history

## 5. Execution Flow

1. Hiring decision, compensation, and negotiation reach final approved state
2. Final Offer Release record is created
3. Readiness engine validates blockers and dependencies
4. Offer packet and final document bindings are assembled
5. Compensation and approval evidence are frozen
6. Final authorization step is completed
7. Offer is dispatched immediately or scheduled
8. Dispatch and delivery status are tracked
9. Released offer snapshot is preserved in audit trail
10. Acceptance workflow handoff is triggered
11. Exception or recall path remains available if policy allows

## 6. Edge Cases

- Negotiation marked complete but compensation snapshot not frozen
  - hard block on release readiness
- One approval shows approved but approval closure record stale
  - closure validation fails and rebuild/revalidation required
- Offer template missing at release time
  - packet freeze blocked until template binding succeeds
- Scheduled release time passes during system outage
  - recovery queue replays scheduled release with idempotent dispatch control
- Dispatch channel fails after release authorization
  - release remains authorized but dispatch enters retry/recovery state
- Offer delivered twice due to retry
  - dispatch idempotency key prevents duplicate candidate-visible release
- Release approved but candidate already withdrawn
  - release blocked and routed to correction path
- Recalled offer after candidate already opened it
  - recall allowed only through policy path; candidate-opened status preserved in audit and downstream handling
- Exception release approved but policy changed before dispatch
  - pre-dispatch policy revalidation required
- Frozen release packet conflicts with newer compensation update
  - release marked stale and new release lineage required
- Release created from outdated negotiation version
  - readiness validation blocks until latest valid negotiation lineage is used
- Audit continuity across release, reschedule, recall, and re-release cycles
  - append-only release lineage retained across all cycles

## 7. Enterprise Features

- tenant-scoped final release records
- readiness validation and blocker enforcement
- approval closure verification
- compensation and negotiation lock verification
- packet assembly and document binding
- immediate and scheduled dispatch
- delivery tracking and acceptance handoff
- governed exception and recall workflows
- immutable frozen release snapshots
- auditable final release lifecycle

## 8. Integration Mapping

### Decision Approval Engine
- Consumes:
  - final approval closure state
  - approval evidence
- Produces:
  - release closure validation input
- Events:
  - `hdc.offer.release.approval.closure.validated`
- Downstream:
  - readiness engine

### Offer Intelligence Engine
- Consumes:
  - selected scenario rationale
  - final recommendation context
- Produces:
  - offer packet intelligence context
- Events:
  - `hdc.offer.release.intelligence.context.attached`
- Downstream:
  - packet assembly

### Compensation Engine
- Consumes:
  - frozen compensation package
  - policy snapshot
- Produces:
  - final compensation evidence
- Events:
  - `hdc.offer.release.compensation.lock.validated`
- Downstream:
  - readiness and packet assembly

### Negotiation Engine
- Consumes:
  - final negotiation outcome
  - negotiated package reference
- Produces:
  - negotiation closure validation
- Events:
  - `hdc.offer.release.negotiation.closed`
- Downstream:
  - readiness and dispatch gating

### Offer Acceptance / Offer Management
- Consumes:
  - released offer packet
  - frozen release snapshot
- Produces:
  - acceptance workflow initiation
- Events:
  - `hdc.offer.release.handed.to.acceptance`
- Downstream:
  - candidate-facing acceptance workflow

### Governance Layer
- Consumes:
  - exceptions
  - recalls
  - overrides
  - policy fit states
- Produces:
  - policy block/warn states
  - release exception approvals
- Events:
  - `hdc.offer.release.exception.requested`
  - `hdc.offer.release.recall.requested`
- Downstream:
  - approval and audit consumers

### Approval Engine
- Consumes:
  - release exception and final authorization dependencies
- Produces:
  - final release authorization state
- Events:
  - `hdc.offer.release.routed.for.final.authorization`
- Downstream:
  - dispatch eligibility

### Analytics Layer
- Consumes:
  - release timing
  - dispatch success/failure
  - recall and exception rates
- Produces:
  - release performance metrics
- Events:
  - `hdc.offer.release.metric.updated`
- Downstream:
  - HDC intelligence and operations

### Audit Layer
- Consumes:
  - readiness validations
  - freeze events
  - dispatch events
  - recall events
- Produces:
  - immutable release audit history
- Events:
  - `hdc.offer.release.audit.logged`
- Downstream:
  - governance and compliance reporting

### Notification / Communication Layer
- Consumes:
  - release scheduling
  - dispatch actions
  - recall actions
  - acceptance handoff state
- Produces:
  - internal notifications
  - candidate-facing delivery trigger
- Events:
  - `hdc.offer.release.notification.required`
- Downstream:
  - recruiter, HR, candidate delivery systems

### Candidate-Facing Offer Delivery Workflow
- Consumes:
  - released offer packet
  - dispatch metadata
- Produces:
  - candidate delivery state
  - candidate open/view events
- Events:
  - `hdc.offer.release.candidate.delivery.triggered`
- Downstream:
  - acceptance and pre-boarding flows
