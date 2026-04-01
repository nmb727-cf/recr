# HDC-OFFER-ACCEPTANCE-10

## 1. System Architecture

Shared engine name: `OfferAcceptanceEngine`

Purpose:
- manage the controlled post-release phase where a candidate receives an offer, reviews an immutable released snapshot, and responds with acceptance, rejection, or clarification
- move the organization from released offer state into accepted, rejected, expired, held, or rework-triggered outcomes
- provide the structured bridge between final offer release and onboarding or hiring closure

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
  - Offer Acceptance Engine
- Pre-boarding / Onboarding / Offer Closure / Re-open Decision

Core components:
1. `Offer Receipt Engine`
2. `Candidate Response Engine`
3. `Acceptance Validation Engine`
4. `Clarification / Query Engine`
5. `Offer Rejection Engine`
6. `Expiry / Timeout Engine`
7. `Acceptance State Engine`
8. `Acceptance-to-Onboarding Handoff Engine`
9. `Offer Rework / Reopen Trigger Engine`
10. `Offer Acceptance Audit Engine`

Supported acceptance modes:
- `standard_acceptance`
- `conditional_acceptance`
- `acceptance_with_query`
- `acceptance_pending_documents`
- `rejection`
- `rejection_with_reason`
- `timeout_no_response`
- `expired_offer`
- `recruiter_assisted_response_capture`
- `executive_sensitive_offer_acceptance_mode`

Role architecture:
- Candidate
- Recruiter
- Hiring Manager
- HR / HRBP
- Offer Owner
- Governance Reviewer
- Leadership Viewer

Operating model:
- offer acceptance starts only after final offer release creates a candidate-facing released snapshot
- candidate interacts only with the immutable released offer version assigned to the acceptance case
- internal teams track open, viewed, queried, accepted, rejected, expired, or intervention-required states
- conditional responses and clarification requests are handled through controlled internal workflows
- candidate remains a global entity with tenant association only

Acceptance policy defaults:
- candidate can only respond to the immutable released offer snapshot, not edit or renegotiate internal package terms directly from the acceptance layer
- negotiation does not happen directly inside acceptance; candidate can raise a query or clarification request which may route back to negotiation or rework flows
- conditional acceptance triggers internal review, not immediate final accepted state, unless policy explicitly allows auto-resolution
- recruiter can record offline acceptance or rejection only through assisted capture flow with audit and conflict validation
- expired offers can be revived only through governed reopen/extend workflow
- accepted offers can later be withdrawn only through authorized employer-side or candidate-side withdrawal processes with audit and downstream impact handling
- acceptance automatically locks the referenced released offer snapshot and compensation lineage for onboarding handoff
- rejection can reopen HDC decision or offer workflows if policy and internal users choose that route

Architecture layers:
- `Candidate Offer Access Layer`
- `Response & Validation Layer`
- `Query & Clarification Layer`
- `Expiry & Intervention Layer`
- `Handoff & Closure Layer`
- `Audit Layer`

## 2. Database Design

Primary entities:
- `offer_acceptance_case`
- `offer_acceptance_response`
- `offer_acceptance_state`
- `offer_acceptance_query`
- `offer_acceptance_rejection_reason`
- `offer_acceptance_expiry`
- `offer_acceptance_handoff`
- `offer_acceptance_intervention`
- `offer_acceptance_snapshot`
- `offer_acceptance_audit_log`

Required fields across entities:
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `final_offer_release_id`
- `offer_acceptance_case_id`
- `response_type`
- `response_status`
- `acceptance_status`
- `query_status`
- `rejection_status`
- `expiry_status`
- `handoff_status`
- `intervention_status`
- `offer_opened_at`
- `response_received_at`
- `accepted_at`
- `rejected_at`
- `expired_at`
- `created_by`
- `created_at`
- `updated_at`

Recommended entity details:

### `offer_acceptance_case`
- `id`
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `final_offer_release_id`
- `offer_acceptance_status`
- `offer_version_reference`
- `expiry_at`
- `created_by`
- `created_at`
- `updated_at`

### `offer_acceptance_response`
- `id`
- `tenant_id`
- `offer_acceptance_case_id`
- `response_type`
- `response_status`
- `response_payload`
- `response_received_at`
- `captured_via`
- `created_at`
- `updated_at`

### `offer_acceptance_state`
- `id`
- `tenant_id`
- `offer_acceptance_case_id`
- `acceptance_status`
- `query_status`
- `rejection_status`
- `expiry_status`
- `intervention_status`
- `created_at`
- `updated_at`

### `offer_acceptance_query`
- `id`
- `tenant_id`
- `offer_acceptance_case_id`
- `query_payload`
- `query_status`
- `responded_by_user_id`
- `responded_at`
- `created_at`
- `updated_at`

### `offer_acceptance_rejection_reason`
- `id`
- `tenant_id`
- `offer_acceptance_case_id`
- `reason_code`
- `reason_payload`
- `created_at`
- `updated_at`

### `offer_acceptance_expiry`
- `id`
- `tenant_id`
- `offer_acceptance_case_id`
- `expiry_status`
- `expiry_at`
- `extended_at`
- `extended_by`
- `created_at`
- `updated_at`

### `offer_acceptance_handoff`
- `id`
- `tenant_id`
- `offer_acceptance_case_id`
- `handoff_status`
- `handoff_target`
- `handoff_reference`
- `created_at`
- `updated_at`

### `offer_acceptance_intervention`
- `id`
- `tenant_id`
- `offer_acceptance_case_id`
- `intervention_type`
- `intervention_status`
- `intervention_payload`
- `created_at`
- `updated_at`

### `offer_acceptance_snapshot`
- `id`
- `tenant_id`
- `offer_acceptance_case_id`
- `snapshot_status`
- `snapshot_payload`
- `created_at`
- `updated_at`

### `offer_acceptance_audit_log`
- `id`
- `tenant_id`
- `offer_acceptance_case_id`
- `event_type`
- `actor_user_id`
- `audit_payload`
- `created_at`

## 3. API Structure

### Candidate-Facing APIs

#### Fetch Offer For Candidate Review
- Purpose: provide candidate-safe immutable released offer snapshot
- Method: `GET`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/candidate`
- Outputs:
  - `offer_snapshot`
  - `expiry_state`
- Permissions:
  - Candidate for linked case only

#### Acknowledge Offer Receipt
- Purpose: record candidate receipt/open event
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/candidate/acknowledge`
- Outputs:
  - `receipt_status`
  - `offer_opened_at`
- Permissions:
  - Candidate

#### Submit Acceptance
- Purpose: submit standard acceptance
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/candidate/accept`
- Inputs:
  - `acceptance_note`
- Outputs:
  - `acceptance_status`
  - `response_received_at`
- Permissions:
  - Candidate

#### Submit Conditional Acceptance
- Purpose: submit conditional acceptance for internal review
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/candidate/conditional-accept`
- Inputs:
  - `conditional_payload`
- Outputs:
  - `acceptance_status`
  - `review_required_status`
- Permissions:
  - Candidate

#### Submit Rejection
- Purpose: submit rejection state
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/candidate/reject`
- Inputs:
  - `rejection_note`
- Outputs:
  - `rejection_status`
  - `rejected_at`
- Permissions:
  - Candidate

#### Submit Rejection Reason
- Purpose: attach structured rejection reason
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/candidate/rejection-reason`
- Inputs:
  - `reason_code`
  - `reason_payload`
- Outputs:
  - `reason_status`
- Permissions:
  - Candidate

#### Submit Query / Clarification Request
- Purpose: raise clarification request
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/candidate/query`
- Inputs:
  - `query_payload`
- Outputs:
  - `query_status`
- Permissions:
  - Candidate

#### Fetch Offer Response Status
- Purpose: return candidate response status
- Method: `GET`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/candidate/status`
- Outputs:
  - `response_status`
  - `acceptance_status`
  - `query_status`
- Permissions:
  - Candidate

#### Fetch Offer Expiry State
- Purpose: return expiry countdown and state
- Method: `GET`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/candidate/expiry`
- Outputs:
  - `expiry_state`
- Permissions:
  - Candidate

#### Confirm Acceptance Acknowledgment If Needed
- Purpose: confirm final acknowledgment after acceptance
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/candidate/acknowledge-acceptance`
- Outputs:
  - `acknowledgment_status`
- Permissions:
  - Candidate

### Internal APIs

#### Fetch Acceptance Case
- Purpose: fetch internal acceptance case details
- Method: `GET`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}`
- Outputs:
  - `acceptance_case`
  - `state_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - HR / HRBP
  - Offer Owner
  - Governance Reviewer
  - Leadership Viewer

#### Fetch Acceptance Dashboard Data
- Purpose: retrieve operational dashboard view
- Method: `GET`
- Path: `/api/hdc/offers/acceptance/dashboard`
- Outputs:
  - `dashboard_data`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Offer Owner
  - Leadership Viewer

#### Fetch Candidate Response Timeline
- Purpose: view acceptance timeline
- Method: `GET`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/timeline`
- Outputs:
  - `timeline_events`
- Permissions:
  - Recruiter
  - Hiring Manager
  - HR / HRBP
  - Governance Reviewer

#### Fetch Open Queries
- Purpose: retrieve pending clarification requests
- Method: `GET`
- Path: `/api/hdc/offers/acceptance/queries/open`
- Outputs:
  - `open_queries`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Offer Owner

#### Respond To Clarification Query
- Purpose: answer candidate clarification request
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/queries/{query_id}/respond`
- Inputs:
  - `response_payload`
- Outputs:
  - `query_status`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Offer Owner

#### Extend Offer Expiry If Allowed
- Purpose: extend offer response window
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/extend-expiry`
- Inputs:
  - `new_expiry_at`
  - `extension_reason`
- Outputs:
  - `expiry_status`
- Permissions:
  - HR / HRBP
  - Offer Owner
  - Governance Reviewer where required

#### Mark Recruiter-Assisted Response Capture
- Purpose: capture offline acceptance or rejection through authorized user
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/assisted-response`
- Inputs:
  - `response_type`
  - `capture_payload`
- Outputs:
  - `response_status`
  - `conflict_check_status`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Offer Owner

#### Reopen Offer Response Window If Policy Allows
- Purpose: reopen expired or closed response window
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/reopen`
- Inputs:
  - `reopen_reason`
  - `new_expiry_at`
- Outputs:
  - `acceptance_status`
  - `expiry_status`
- Permissions:
  - HR / HRBP
  - Offer Owner
  - Governance Reviewer where required

#### Mark Acceptance Verified
- Purpose: verify accepted state for downstream onboarding
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/verify`
- Outputs:
  - `acceptance_status`
  - `verification_status`
- Permissions:
  - HR / HRBP
  - Offer Owner

#### Handoff Accepted Case To Onboarding
- Purpose: send verified accepted offer to onboarding/pre-boarding
- Method: `POST`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/handoff`
- Outputs:
  - `handoff_status`
  - `handoff_reference`
- Permissions:
  - HR / HRBP
  - Offer Owner

### Audit / Control APIs

#### Fetch Acceptance Audit Trail
- Purpose: retrieve immutable audit history
- Method: `GET`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/audit`
- Outputs:
  - `audit_events`
- Permissions:
  - Governance Reviewer
  - Leadership Viewer
  - Authorized admins

#### Fetch Response Snapshot
- Purpose: fetch immutable offer/response snapshot
- Method: `GET`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/snapshot`
- Outputs:
  - `response_snapshot`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Offer Owner
  - Governance Reviewer

#### Fetch Expiry / Timeout History
- Purpose: retrieve expiry changes and timeout events
- Method: `GET`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/expiry-history`
- Outputs:
  - `expiry_history`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Governance Reviewer

#### Fetch Intervention History
- Purpose: retrieve internal interventions and reopen/assist actions
- Method: `GET`
- Path: `/api/hdc/offers/acceptance/{offer_acceptance_case_id}/interventions`
- Outputs:
  - `intervention_history`
- Permissions:
  - HR / HRBP
  - Offer Owner
  - Governance Reviewer

## 4. UI Architecture

Frontend principles:
- clean candidate-friendly acceptance UX
- internal enterprise operational dashboard
- immutable released offer snapshot visibility
- clear state progression: sent, opened, queried, accepted, rejected, expired
- timeline and audit visibility
- responsive, trustworthy candidate experience

### Candidate UI

#### Offer Review Page
- candidate-safe entry point
- released offer state
- expiry countdown

#### Offer Summary And Details Screen
- offer summary
- role, location, and terms overview
- immutable release version reference

#### Compensation And Terms Snapshot
- frozen compensation summary
- benefits and terms display
- final issued package reference

#### Accept / Reject / Ask Question Actions
- standard actions
- explicit confirmation
- duplicate-submission protection

#### Query Submission Screen
- structured clarification form
- pending query status

#### Expiry Countdown / Deadline View
- response deadline
- extension notice if granted

#### Acceptance Confirmation Screen
- accepted state
- acknowledgment and next steps

#### Rejection Confirmation Screen
- rejection submitted
- optional reason confirmation

#### Response Submitted Timeline
- receipt
- query
- final response state

### Recruiter / HR UI

#### Offer Acceptance Dashboard
- active offer responses
- accepted/rejected/expired states
- cases requiring intervention

#### Pending Response Tracker
- not opened
- opened but not responded
- near-expiry

#### Query / Clarification Inbox
- open candidate questions
- SLA and owner tracking

#### Expiry Risk Tracker
- offers approaching expiry
- no-response escalations
- reopen/extend opportunities

#### Accepted / Rejected / Expired Views
- segmented operational views
- response reasons and status

#### Intervention Controls
- assisted capture
- reopen window
- extend expiry
- mark verified

#### Handoff-To-Onboarding Readiness Screen
- accepted and verified cases
- missing handoff blockers

### Hiring Manager / Leadership UI

#### Acceptance Status Overview
- live response summary
- accepted and rejected case counts

#### High-Value / High-Risk Offer Response Monitor
- executive offers
- high-compensation offers
- stalled responses

#### Rejection Reason Summary
- structured reason analytics
- role-specific decline patterns

#### Escalated Clarification Visibility
- critical pending queries
- business decision needed markers

## 5. Execution Flow

1. Final offer is released
2. Offer acceptance case is created
3. Candidate receives offer access
4. Candidate opens and reviews immutable offer snapshot
5. Candidate accepts, rejects, or asks for clarification
6. Internal team tracks response state
7. Clarification workflow completes if raised
8. Acceptance validation or verification runs if needed
9. Accepted case is handed off to onboarding or pre-boarding
10. Rejected or expired case updates hiring outcome and downstream workflows
11. Audit trail and response snapshots remain preserved

## 6. Edge Cases

- Candidate opens offer after expiry
  - view can be blocked or limited to expired state per policy; no valid response accepted without reopen
- Offer accepted after deadline but before system sync
  - timestamp arbitration and grace-window policy determine validity
- Candidate raises query near expiry
  - expiry can pause, extend, or continue based on policy and query type
- Recruiter records offline acceptance conflicting with portal state
  - conflict check blocks silent overwrite and routes case to intervention review
- Released offer recalled while candidate reviewing
  - acceptance case is invalidated or paused with candidate-safe messaging and full audit trail
- Candidate accepts but onboarding handoff fails
  - acceptance remains valid; handoff enters retry or manual intervention path
- Candidate rejects without reason
  - rejection allowed if policy permits optional reason; otherwise prompt for minimum coded reason
- Expired offer later reactivated
  - reopen creates a governed new response window while preserving prior expiry record
- Conditional acceptance conflicts with frozen offer terms
  - conditional acceptance routes to internal review, not final acceptance
- Duplicate response submission
  - idempotent response handling keeps first valid final state unless reopen policy applies
- Candidate response captured on stale offer version
  - stale response blocked or flagged; current active release lineage determines validity
- Audit continuity across extend, reopen, and expire cycles
  - append-only timeline preserved across all case state changes

## 7. Enterprise Features

- tenant-scoped acceptance cases
- immutable released offer reference
- candidate-facing response workflow
- conditional acceptance and clarification handling
- recruiter-assisted offline capture with conflict controls
- expiry and timeout handling
- reopen and extension governance
- accepted-state freeze and onboarding handoff
- rejection and expiry closure routing
- auditable acceptance lifecycle

## 8. Integration Mapping

### Final Offer Release Engine
- Consumes:
  - released offer packet
  - final frozen release snapshot
- Produces:
  - acceptance case initialization
- Events:
  - `hdc.offer.acceptance.case.created`
- Downstream:
  - candidate-facing review workflow

### Negotiation Engine
- Consumes:
  - negotiation closure lineage
  - negotiated package reference where applicable
- Produces:
  - rework or reopen trigger when query or conditional response requires it
- Events:
  - `hdc.offer.acceptance.rework.requested`
- Downstream:
  - negotiation or compensation re-entry if needed

### Compensation Engine
- Consumes:
  - frozen compensation snapshot
- Produces:
  - compensation reference for candidate review and onboarding handoff
- Events:
  - read-only snapshot usage
- Downstream:
  - acceptance display and onboarding packet

### Offer Management
- Consumes:
  - accepted, rejected, expired, or withdrawn outcomes
- Produces:
  - offer lifecycle state updates
- Events:
  - `hdc.offer.acceptance.outcome.updated`
- Downstream:
  - closure and reporting flows

### Pre-boarding / Onboarding
- Consumes:
  - verified accepted case
  - final release snapshot
- Produces:
  - onboarding workflow initiation
- Events:
  - `hdc.offer.acceptance.handed.to.onboarding`
- Downstream:
  - onboarding and employee setup flows

### Governance Layer
- Consumes:
  - reopen, extension, assisted capture, and recall-linked acceptance changes
- Produces:
  - policy block or approval requirement
- Events:
  - `hdc.offer.acceptance.override.requested`
- Downstream:
  - intervention controls

### Approval Engine
- Consumes:
  - conditional acceptance or governed reopen actions where needed
- Produces:
  - approval decision for exceptional response handling
- Events:
  - `hdc.offer.acceptance.conditional.review.required`
- Downstream:
  - acceptance resolution path

### Analytics Layer
- Consumes:
  - open rate
  - query rate
  - acceptance/rejection/expiry rates
  - response timing
- Produces:
  - offer acceptance metrics
  - decline reason analytics
- Events:
  - `hdc.offer.acceptance.metric.updated`
- Downstream:
  - HDC intelligence and operational dashboards

### Audit Layer
- Consumes:
  - receipt, query, response, intervention, reopen, expiry, and handoff events
- Produces:
  - immutable acceptance audit trail
- Events:
  - `hdc.offer.acceptance.audit.logged`
- Downstream:
  - governance and compliance review

### Notification / Communication Layer
- Consumes:
  - release to candidate
  - reminder needs
  - query responses
  - expiry warnings
- Produces:
  - candidate and internal notifications
- Events:
  - `hdc.offer.acceptance.notification.required`
- Downstream:
  - candidate portal and internal users

### Candidate Portal / Candidate-Facing Delivery Experience
- Consumes:
  - immutable released offer snapshot
  - response window state
- Produces:
  - receipt/open state
  - acceptance/rejection/query inputs
- Events:
  - `hdc.offer.acceptance.candidate.response.received`
- Downstream:
  - internal tracking and handoff workflows
