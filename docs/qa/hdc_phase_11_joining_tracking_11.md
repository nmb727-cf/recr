# HDC-JOINING-TRACKING-11

## 1. System Architecture

Shared engine name: `JoiningTrackingEngine`

Purpose:
- track candidate state after offer acceptance through join, drop, withdrawal, postponement, and final hiring outcome
- measure offer-to-join conversion, joining reliability, recruiter effectiveness, and agency effectiveness
- operate as the structured `Offer -> Join -> Close` tracking layer without requiring HRMS integration

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
  - Joining Tracking Engine
- Job Closure / Hiring Analytics / Performance Tracking

Core components:
1. `Joining Status Engine`
2. `Joining Date Tracker`
3. `Offer Drop Tracker`
4. `Joining Confirmation Engine`
5. `Candidate Reliability Tracker`
6. `Recruiter Performance Tracker`
7. `Agency Performance Tracker`
8. `Hiring Outcome Engine`
9. `Joining Analytics Engine`
10. `Joining Audit Engine`

Supported joining statuses:
- `offer_accepted`
- `joining_pending`
- `joining_confirmed`
- `joined`
- `not_joined`
- `offer_dropped`
- `joining_postponed`
- `candidate_withdrawn`
- `company_withdrawn`
- `offer_expired`
- `offer_cancelled`

Role architecture:
- Recruiter
- Hiring Manager
- HR / HRBP
- Agency Recruiter
- Company Recruiter
- Tenant Admin
- Leadership Viewer
- Candidate (joining confirmation only, optional)

Operating model:
- joining tracking begins from an accepted offer case
- joining status is tracked as a tenant-scoped case linked to decision, acceptance, and job pipeline context
- candidate can optionally confirm joining or request postponement through a limited candidate-facing flow
- internal teams can track offer drops, withdrawals, not-joined cases, and final closure outcomes
- candidate remains a global entity with tenant association only

Policy defaults:
- joining confirmation is optional by default, but can be required for some tenants or role classes
- recruiter can manually mark `joined` only if policy allows and audit reason is captured; HR ownership is preferred for final confirmation
- candidate can confirm joining only through controlled candidate-facing confirmation surfaces
- joining can be postponed subject to policy, role, and max-postpone rules
- `joined` can close the job pipeline if configured
- `not_joined`, `offer_dropped`, or `candidate_withdrawn` can reopen the hiring pipeline if policy allows

Architecture layers:
- `Joining Case Layer`
- `Status & Date Layer`
- `Confirmation & Intervention Layer`
- `Outcome & Closure Layer`
- `Analytics & Scoring Layer`
- `Audit Layer`

## 2. Database Design

Primary entities:
- `joining_tracking_case`
- `joining_status_history`
- `joining_confirmation`
- `joining_date_record`
- `joining_drop_record`
- `joining_postpone_record`
- `joining_outcome`
- `joining_reliability_score`
- `joining_performance_metric`
- `joining_audit_log`

Required fields across entities:
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `offer_acceptance_case_id`
- `joining_tracking_case_id`
- `joining_status`
- `joining_date`
- `actual_joining_date`
- `postponed_date`
- `drop_reason`
- `withdrawal_reason`
- `confirmation_status`
- `outcome_status`
- `candidate_reliability_score`
- `recruiter_performance_score`
- `agency_performance_score`
- `created_by`
- `created_at`
- `updated_at`

Recommended entity details:

### `joining_tracking_case`
- `id`
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `offer_acceptance_case_id`
- `joining_tracking_case_id_external`
- `joining_status`
- `owner_user_id`
- `created_by`
- `created_at`
- `updated_at`

### `joining_status_history`
- `id`
- `tenant_id`
- `joining_tracking_case_id`
- `joining_status`
- `status_reason`
- `changed_by_user_id`
- `changed_at`
- `created_at`
- `updated_at`

### `joining_confirmation`
- `id`
- `tenant_id`
- `joining_tracking_case_id`
- `confirmation_status`
- `confirmed_by_actor_type`
- `confirmed_by_user_id`
- `confirmed_at`
- `created_at`
- `updated_at`

### `joining_date_record`
- `id`
- `tenant_id`
- `joining_tracking_case_id`
- `joining_date`
- `actual_joining_date`
- `date_status`
- `created_at`
- `updated_at`

### `joining_drop_record`
- `id`
- `tenant_id`
- `joining_tracking_case_id`
- `drop_reason`
- `drop_payload`
- `created_at`
- `updated_at`

### `joining_postpone_record`
- `id`
- `tenant_id`
- `joining_tracking_case_id`
- `postponed_date`
- `postpone_reason`
- `postpone_count`
- `created_at`
- `updated_at`

### `joining_outcome`
- `id`
- `tenant_id`
- `joining_tracking_case_id`
- `outcome_status`
- `outcome_reason`
- `closed_at`
- `created_at`
- `updated_at`

### `joining_reliability_score`
- `id`
- `tenant_id`
- `joining_tracking_case_id`
- `candidate_reliability_score`
- `score_payload`
- `created_at`
- `updated_at`

### `joining_performance_metric`
- `id`
- `tenant_id`
- `joining_tracking_case_id`
- `recruiter_performance_score`
- `agency_performance_score`
- `metric_payload`
- `created_at`
- `updated_at`

### `joining_audit_log`
- `id`
- `tenant_id`
- `joining_tracking_case_id`
- `event_type`
- `actor_user_id`
- `audit_payload`
- `created_at`

## 3. API Structure

### Create Joining Tracking Case
- Purpose: initialize joining tracking after accepted offer
- Method: `POST`
- Path: `/api/hdc/joining`
- Inputs:
  - `job_id`
  - `candidate_id`
  - `decision_id`
  - `offer_acceptance_case_id`
- Outputs:
  - `joining_tracking_case_id`
  - `joining_status`
- Permissions:
  - Recruiter
  - HR / HRBP
  - System

### Fetch Joining Tracking Case
- Purpose: fetch joining case and current status
- Method: `GET`
- Path: `/api/hdc/joining/{joining_tracking_case_id}`
- Outputs:
  - `joining_tracking_case`
  - `status_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - HR / HRBP
  - Agency Recruiter where allowed
  - Leadership Viewer

### Update Joining Status
- Purpose: update case status
- Method: `PATCH`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/status`
- Inputs:
  - `joining_status`
  - `status_reason`
- Outputs:
  - `updated_status`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Tenant Admin

### Set Joining Date
- Purpose: set or update expected joining date
- Method: `POST`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/date`
- Inputs:
  - `joining_date`
- Outputs:
  - `joining_date_record`
- Permissions:
  - Recruiter
  - HR / HRBP

### Confirm Joining
- Purpose: confirm planned joining
- Method: `POST`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/confirm`
- Inputs:
  - `confirmation_note`
- Outputs:
  - `confirmation_status`
- Permissions:
  - Candidate for own case where enabled
  - Recruiter
  - HR / HRBP

### Mark Joined
- Purpose: mark actual join completion
- Method: `POST`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/joined`
- Inputs:
  - `actual_joining_date`
  - `join_note`
- Outputs:
  - `joining_status`
  - `outcome_status`
- Permissions:
  - HR / HRBP
  - Recruiter where allowed

### Mark Not Joined
- Purpose: mark no-join outcome
- Method: `POST`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/not-joined`
- Inputs:
  - `reason_payload`
- Outputs:
  - `joining_status`
  - `outcome_status`
- Permissions:
  - Recruiter
  - HR / HRBP

### Mark Offer Dropped
- Purpose: mark offer drop
- Method: `POST`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/offer-dropped`
- Inputs:
  - `drop_reason`
  - `drop_payload`
- Outputs:
  - `joining_status`
  - `drop_record`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Agency Recruiter where allowed

### Mark Candidate Withdrawn
- Purpose: mark candidate withdrawal after acceptance
- Method: `POST`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/candidate-withdrawn`
- Inputs:
  - `withdrawal_reason`
- Outputs:
  - `joining_status`
  - `outcome_status`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Agency Recruiter where allowed

### Mark Company Withdrawn
- Purpose: mark employer-side withdrawal
- Method: `POST`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/company-withdrawn`
- Inputs:
  - `withdrawal_reason`
- Outputs:
  - `joining_status`
  - `outcome_status`
- Permissions:
  - HR / HRBP
  - Tenant Admin
  - Leadership Viewer where authorized

### Postpone Joining
- Purpose: postpone joining date
- Method: `POST`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/postpone`
- Inputs:
  - `postponed_date`
  - `postpone_reason`
- Outputs:
  - `joining_status`
  - `postpone_record`
- Permissions:
  - Candidate where enabled
  - Recruiter
  - HR / HRBP

### Fetch Joining History
- Purpose: retrieve status and date history
- Method: `GET`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/history`
- Outputs:
  - `joining_history`
- Permissions:
  - Recruiter
  - Hiring Manager
  - HR / HRBP
  - Leadership Viewer

### Fetch Joining Analytics
- Purpose: retrieve joining analytics overview
- Method: `GET`
- Path: `/api/hdc/joining/analytics`
- Outputs:
  - `joining_analytics`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Leadership Viewer
  - Tenant Admin

### Fetch Offer Drop Rate
- Purpose: retrieve offer drop metrics
- Method: `GET`
- Path: `/api/hdc/joining/analytics/drop-rate`
- Outputs:
  - `drop_rate_metrics`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Leadership Viewer

### Fetch Recruiter Joining Performance
- Purpose: retrieve recruiter performance metrics
- Method: `GET`
- Path: `/api/hdc/joining/analytics/recruiter-performance`
- Outputs:
  - `recruiter_performance_metrics`
- Permissions:
  - HR / HRBP
  - Leadership Viewer
  - Tenant Admin

### Fetch Agency Joining Performance
- Purpose: retrieve agency performance metrics
- Method: `GET`
- Path: `/api/hdc/joining/analytics/agency-performance`
- Outputs:
  - `agency_performance_metrics`
- Permissions:
  - HR / HRBP
  - Leadership Viewer
  - Tenant Admin

### Fetch Candidate Reliability Score
- Purpose: retrieve candidate reliability score
- Method: `GET`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/candidate-reliability`
- Outputs:
  - `candidate_reliability_score`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Leadership Viewer where permitted

### Fetch Job Joining Ratio
- Purpose: retrieve join ratio for a job
- Method: `GET`
- Path: `/api/hdc/joining/analytics/job-ratio`
- Inputs:
  - `job_id`
- Outputs:
  - `job_joining_ratio`
- Permissions:
  - Recruiter
  - Hiring Manager
  - HR / HRBP
  - Leadership Viewer

### Fetch Joining Audit Trail
- Purpose: retrieve immutable joining audit history
- Method: `GET`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/audit`
- Outputs:
  - `audit_events`
- Permissions:
  - HR / HRBP
  - Tenant Admin
  - Leadership Viewer

### Fetch Status Change History
- Purpose: fetch status change history
- Method: `GET`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/status-history`
- Outputs:
  - `status_change_history`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Leadership Viewer

### Fetch Joining Outcome
- Purpose: fetch final outcome for joining case
- Method: `GET`
- Path: `/api/hdc/joining/{joining_tracking_case_id}/outcome`
- Outputs:
  - `joining_outcome`
- Permissions:
  - Recruiter
  - Hiring Manager
  - HR / HRBP
  - Leadership Viewer

## 4. UI Architecture

Frontend principles:
- operational enterprise dashboard for internal users
- optional minimal candidate confirmation flow
- explicit state visibility across accepted, pending, confirmed, joined, dropped, withdrawn, expired, and cancelled
- strong timeline and audit visibility

### Recruiter UI

#### Joining Tracking Dashboard
- active joining cases
- joining status distribution
- near-date and overdue joins

#### Joining Pending List
- accepted but not joined candidates
- upcoming joining dates
- at-risk joiners

#### Joining Confirmation Panel
- expected joining confirmations
- candidate-confirmed versus recruiter-confirmed view

#### Drop / Withdrawal Tracker
- dropped offers
- candidate/company withdrawals
- reasons and trends

#### Joining Calendar View
- joining dates
- postponements
- final outcomes

### Hiring Manager UI

#### Hiring Outcome Dashboard
- joined versus not joined summary
- role-level outcomes

#### Joined Vs Not Joined Summary
- ratio by job, team, and role
- latest closure view

#### Joining Delay Alerts
- postponed cases
- missing confirmations
- high-risk no-join indicators

### Agency UI

#### Candidate Joining Tracker
- agency candidate joining cases
- status by candidate

#### Offer Drop Tracking
- offer drop reasons
- agency-specific drop visibility

#### Agency Performance Dashboard
- join ratio
- drop ratio
- timeliness and reliability indicators

### Leadership UI

#### Hiring Outcome Dashboard
- organization-wide join outcomes
- no-join and withdrawal patterns

#### Offer Drop Analytics
- offer drop by team, recruiter, agency, role

#### Recruiter Performance Analytics
- recruiter-level join conversion
- delay and no-join indicators

#### Agency Performance Analytics
- agency-wise join success
- drop and withdrawal trends

### Candidate UI (Optional)

#### Joining Confirmation Screen
- confirm joining
- see current expected joining date

#### Joining Details View
- joining date
- final accepted offer reference

#### Postpone Request Option
- request postpone with reason
- see request state

## 5. Execution Flow

1. Offer is accepted
2. Joining tracking case is created
3. Joining date is recorded
4. Candidate confirmation is optionally captured
5. Recruiter and HR monitor joining status
6. Candidate joins, postpones, withdraws, drops, or does not join
7. Status is updated with audit trail
8. Hiring outcome is finalized
9. Analytics and performance scores are updated
10. Job pipeline is closed or reopened based on outcome and policy

## 6. Edge Cases

- Candidate joins earlier
  - actual joining date can precede planned date with audit reason
- Joining postponed multiple times
  - postpone count tracked and risk/performance indicators updated
- Candidate joins but later leaves before start
  - can be treated as not-joined or withdrawn-before-start based on policy
- Duplicate joining records
  - idempotency and unique case linkage required
- Recruiter marks wrong status
  - correction flow creates new audited status event, not overwrite
- Joining date changed after confirmation
  - confirmation state may reset to pending depending on policy
- Multiple offers accepted by candidate
  - tenant/job scoped case remains valid; global candidate rule preserved with conflict indicators only
- Candidate withdraws after acceptance
  - outcome routes to withdrawal or reopen path
- Company cancels role after acceptance
  - company-withdrawn path closes case and updates analytics

## 7. Enterprise Features

- tenant-scoped join tracking cases
- accepted-to-joined outcome tracking
- join, no-join, drop, withdrawal, postpone handling
- candidate reliability scoring
- recruiter and agency performance tracking
- optional candidate confirmation flow
- job closure and reopen linkage
- analytics-ready outcome measurement
- immutable audit trail
- candidate-global rule preserved

## 8. Integration Mapping

### Offer Acceptance Engine
- Consumes:
  - accepted offer case
  - acceptance status
- Produces:
  - joining tracking case initialization
- Events:
  - `hdc.joining.case.created`
- Downstream:
  - joining workflow

### Decision Engine
- Consumes:
  - decision and job linkage
- Produces:
  - hiring outcome closure context
- Events:
  - `hdc.joining.outcome.updated`
- Downstream:
  - pipeline closure or reopen

### Analytics Engine
- Consumes:
  - joining outcomes
  - delays
  - drops
  - withdrawals
- Produces:
  - joining analytics
  - conversion metrics
  - recruiter and agency performance metrics
- Events:
  - `hdc.joining.metric.updated`
- Downstream:
  - leadership dashboards

### Governance Layer
- Consumes:
  - manual overrides
  - reopen flows
  - high-risk corrections
- Produces:
  - policy block or review state
- Events:
  - `hdc.joining.override.requested`
- Downstream:
  - internal control review

### Candidate Profile
- Consumes:
  - candidate global identity and contact linkage
- Produces:
  - candidate-facing confirmation context
- Events:
  - read-only profile access
- Downstream:
  - confirmation and tracking surfaces

### Job Pipeline
- Consumes:
  - joined, not joined, withdrawn, cancelled outcomes
- Produces:
  - pipeline closure or reopen status
- Events:
  - `hdc.joining.pipeline.status.change.requested`
- Downstream:
  - requisition and hiring workflow states

### Agency Performance Engine
- Consumes:
  - agency-linked joining outcomes
- Produces:
  - agency performance metrics
- Events:
  - `hdc.joining.agency.metric.updated`
- Downstream:
  - agency dashboards and reviews

### Recruiter Performance Engine
- Consumes:
  - recruiter-linked join outcomes
- Produces:
  - recruiter performance metrics
- Events:
  - `hdc.joining.recruiter.metric.updated`
- Downstream:
  - internal performance dashboards
