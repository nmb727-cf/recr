# HDC-ANALYTICS-GOVERNANCE-12

## 1. System Architecture

Shared layer name: `HiringDecisionAnalyticsGovernanceLayer`

Purpose:
- provide the intelligence and control layer for the full Hiring Decision Command Center
- unify decision analytics, approval analytics, offer analytics, negotiation analytics, joining analytics, recruiter and agency performance analytics, governance policy enforcement, exception monitoring, and audit compliance
- support executive insights, operational optimization, and enterprise governance across the full post-interview hiring lifecycle

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
  - Hiring Decision Analytics & Governance Layer
- Executive Insights / Governance Controls / Hiring Optimization

Core components:
1. `Decision Analytics Engine`
2. `Approval Analytics Engine`
3. `Offer Analytics Engine`
4. `Negotiation Analytics Engine`
5. `Joining Analytics Engine`
6. `Recruiter Performance Engine`
7. `Agency Performance Engine`
8. `Governance Policy Engine`
9. `Exception Monitoring Engine`
10. `Audit & Compliance Engine`

Analytics scope:
- decision conversion
- decision turnaround time
- approval turnaround time
- approval bottlenecks
- candidate comparison effectiveness
- offer acceptance rate
- compensation deviation trends
- negotiation success rate
- joining rate
- offer drop rate
- recruiter decision quality
- agency joining quality
- final hiring outcome trends

Governance scope:
- decision approval compliance
- compensation policy compliance
- exception approval monitoring
- negotiation threshold governance
- offer release compliance
- joining closure compliance
- manual override logging
- audit trail visibility
- rule violation detection
- enterprise review controls

Role architecture:
- Recruiter
- Hiring Manager
- HR / HRBP
- Compensation Analyst
- Finance Reviewer
- Agency Recruiter
- Leadership Viewer
- Governance Reviewer
- Tenant Admin

Operating model:
- HDC engines emit operational events and metric-ready signals into this layer
- analytics pipelines compute real-time and aggregated metrics with tenant-safe isolation
- governance engine evaluates active workflows, exceptions, overrides, and threshold breaches against policy
- dashboards expose role-filtered visibility based on tenant, workspace type, recruiter, agency, role, job, and time window
- candidate does not access this internal layer
- candidate remains a global entity with tenant association only

Analytics model:
- real-time metrics for active operational views:
  - pending approvals
  - stalled negotiations
  - near-expiry offers
  - joining risk
- aggregated metrics for trend and executive views:
  - daily
  - weekly
  - monthly
- company and agency analytics remain isolated unless policy explicitly permits controlled comparison
- some metrics can be governance-locked and not user-adjustable

Governance model:
- policy can warn, block, escalate, or require exception approval
- governance can lock compensation and negotiation rules
- governance can reopen a decision chain only through explicit controlled workflow
- exception approval can require multi-level signoff for high-risk or high-value cases
- tenant-specific governance rules override platform defaults within allowed scope

Architecture layers:
- `Metric Intake Layer`
- `Aggregation & Snapshot Layer`
- `Performance Intelligence Layer`
- `Governance Policy Layer`
- `Violation & Exception Layer`
- `Audit & Review Layer`

## 2. Database Design

Primary entities:
- `hdc_analytics_metric`
- `hdc_analytics_snapshot`
- `hdc_decision_metric`
- `hdc_approval_metric`
- `hdc_offer_metric`
- `hdc_negotiation_metric`
- `hdc_joining_metric`
- `hdc_recruiter_performance`
- `hdc_agency_performance`
- `hdc_governance_policy`
- `hdc_governance_violation`
- `hdc_governance_exception`
- `hdc_governance_audit_log`
- `hdc_governance_review_record`

Required fields across entities:
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `metric_type`
- `metric_value`
- `metric_window`
- `approval_status`
- `offer_status`
- `negotiation_status`
- `joining_status`
- `policy_status`
- `violation_status`
- `exception_status`
- `review_status`
- `recruiter_user_id`
- `agency_tenant_id`
- `snapshot_date`
- `created_by`
- `created_at`
- `updated_at`

Recommended entity details:

### `hdc_analytics_metric`
- `id`
- `tenant_id`
- `metric_type`
- `metric_value`
- `metric_window`
- `metric_payload`
- `snapshot_date`
- `created_at`
- `updated_at`

### `hdc_analytics_snapshot`
- `id`
- `tenant_id`
- `snapshot_type`
- `snapshot_date`
- `snapshot_payload`
- `created_at`
- `updated_at`

### `hdc_decision_metric`
- `id`
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `decision_status`
- `metric_type`
- `metric_value`
- `created_at`
- `updated_at`

### `hdc_approval_metric`
- `id`
- `tenant_id`
- `decision_id`
- `approval_status`
- `metric_type`
- `metric_value`
- `created_at`
- `updated_at`

### `hdc_offer_metric`
- `id`
- `tenant_id`
- `decision_id`
- `offer_status`
- `metric_type`
- `metric_value`
- `created_at`
- `updated_at`

### `hdc_negotiation_metric`
- `id`
- `tenant_id`
- `decision_id`
- `negotiation_status`
- `metric_type`
- `metric_value`
- `created_at`
- `updated_at`

### `hdc_joining_metric`
- `id`
- `tenant_id`
- `decision_id`
- `joining_status`
- `metric_type`
- `metric_value`
- `created_at`
- `updated_at`

### `hdc_recruiter_performance`
- `id`
- `tenant_id`
- `recruiter_user_id`
- `metric_payload`
- `created_at`
- `updated_at`

### `hdc_agency_performance`
- `id`
- `tenant_id`
- `agency_tenant_id`
- `metric_payload`
- `created_at`
- `updated_at`

### `hdc_governance_policy`
- `id`
- `tenant_id`
- `policy_type`
- `policy_status`
- `policy_payload`
- `created_at`
- `updated_at`

### `hdc_governance_violation`
- `id`
- `tenant_id`
- `decision_id`
- `violation_status`
- `violation_type`
- `violation_payload`
- `created_at`
- `updated_at`

### `hdc_governance_exception`
- `id`
- `tenant_id`
- `decision_id`
- `exception_status`
- `exception_type`
- `exception_payload`
- `created_at`
- `updated_at`

### `hdc_governance_audit_log`
- `id`
- `tenant_id`
- `decision_id`
- `event_type`
- `actor_user_id`
- `audit_payload`
- `created_at`

### `hdc_governance_review_record`
- `id`
- `tenant_id`
- `decision_id`
- `review_status`
- `review_payload`
- `reviewed_by`
- `created_at`
- `updated_at`

## 3. API Structure

### Analytics APIs

#### Fetch Hiring Decision Analytics Dashboard
- Purpose: retrieve top-level HDC analytics dashboard
- Method: `GET`
- Path: `/api/hdc/analytics/dashboard`
- Outputs:
  - `dashboard_summary`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Leadership Viewer
  - Tenant Admin

#### Fetch Decision Conversion Metrics
- Purpose: retrieve decision conversion metrics
- Method: `GET`
- Path: `/api/hdc/analytics/decision-conversion`
- Outputs:
  - `decision_conversion_metrics`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Leadership Viewer

#### Fetch Approval Analytics
- Purpose: retrieve approval timing and bottleneck metrics
- Method: `GET`
- Path: `/api/hdc/analytics/approvals`
- Outputs:
  - `approval_analytics`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Leadership Viewer
  - Governance Reviewer

#### Fetch Offer Analytics
- Purpose: retrieve offer release and acceptance analytics
- Method: `GET`
- Path: `/api/hdc/analytics/offers`
- Outputs:
  - `offer_analytics`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Leadership Viewer

#### Fetch Negotiation Analytics
- Purpose: retrieve negotiation analytics
- Method: `GET`
- Path: `/api/hdc/analytics/negotiations`
- Outputs:
  - `negotiation_analytics`
- Permissions:
  - Recruiter
  - Compensation Analyst
  - HR / HRBP
  - Leadership Viewer

#### Fetch Joining Analytics
- Purpose: retrieve joining analytics
- Method: `GET`
- Path: `/api/hdc/analytics/joining`
- Outputs:
  - `joining_analytics`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Leadership Viewer

#### Fetch Recruiter Performance Analytics
- Purpose: retrieve recruiter performance analytics
- Method: `GET`
- Path: `/api/hdc/analytics/recruiters`
- Outputs:
  - `recruiter_performance_analytics`
- Permissions:
  - HR / HRBP
  - Leadership Viewer
  - Tenant Admin

#### Fetch Agency Performance Analytics
- Purpose: retrieve agency performance analytics
- Method: `GET`
- Path: `/api/hdc/analytics/agencies`
- Outputs:
  - `agency_performance_analytics`
- Permissions:
  - HR / HRBP
  - Leadership Viewer
  - Tenant Admin

#### Fetch Hiring Outcome Trends
- Purpose: retrieve hiring outcome trends
- Method: `GET`
- Path: `/api/hdc/analytics/outcomes`
- Outputs:
  - `hiring_outcome_trends`
- Permissions:
  - Leadership Viewer
  - HR / HRBP
  - Tenant Admin

#### Fetch Role / Job Wise Analytics
- Purpose: retrieve filtered analytics by job, role, or department
- Method: `GET`
- Path: `/api/hdc/analytics/by-role-job`
- Inputs:
  - `job_id`
  - `role_filters`
- Outputs:
  - `role_job_analytics`
- Permissions:
  - Recruiter
  - Hiring Manager
  - HR / HRBP
  - Leadership Viewer

#### Fetch Tenant-Level Hiring Intelligence
- Purpose: retrieve tenant-level intelligence view
- Method: `GET`
- Path: `/api/hdc/analytics/tenant-intelligence`
- Outputs:
  - `tenant_hiring_intelligence`
- Permissions:
  - Leadership Viewer
  - Tenant Admin

### Governance APIs

#### Fetch Governance Dashboard
- Purpose: retrieve governance control dashboard
- Method: `GET`
- Path: `/api/hdc/governance/dashboard`
- Outputs:
  - `governance_dashboard`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer

#### Fetch Active Governance Policies
- Purpose: list active governance policies
- Method: `GET`
- Path: `/api/hdc/governance/policies`
- Outputs:
  - `active_policies`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

#### Create Governance Policy
- Purpose: create policy
- Method: `POST`
- Path: `/api/hdc/governance/policies`
- Inputs:
  - `policy_type`
  - `policy_payload`
- Outputs:
  - `policy_record`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

#### Update Governance Policy
- Purpose: update policy
- Method: `PATCH`
- Path: `/api/hdc/governance/policies/{policy_id}`
- Inputs:
  - `policy_payload`
- Outputs:
  - `updated_policy`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

#### Fetch Governance Violations
- Purpose: retrieve violations
- Method: `GET`
- Path: `/api/hdc/governance/violations`
- Outputs:
  - `governance_violations`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer

#### Fetch Exception Requests
- Purpose: retrieve exception requests
- Method: `GET`
- Path: `/api/hdc/governance/exceptions`
- Outputs:
  - `exception_requests`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer

#### Approve / Reject Exception
- Purpose: resolve exception request
- Method: `POST`
- Path: `/api/hdc/governance/exceptions/{exception_id}/resolve`
- Inputs:
  - `exception_status`
  - `resolution_note`
- Outputs:
  - `resolved_exception`
- Permissions:
  - Governance Reviewer
  - Leadership Viewer
  - Tenant Admin where policy allows

#### Fetch Manual Overrides
- Purpose: retrieve manual override records
- Method: `GET`
- Path: `/api/hdc/governance/manual-overrides`
- Outputs:
  - `manual_overrides`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

#### Fetch Audit Trail
- Purpose: retrieve governance and decision audit
- Method: `GET`
- Path: `/api/hdc/governance/audit`
- Outputs:
  - `audit_trail`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer

#### Fetch Compliance Summary
- Purpose: retrieve compliance summary
- Method: `GET`
- Path: `/api/hdc/governance/compliance-summary`
- Outputs:
  - `compliance_summary`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer

### Drill-Down / Audit APIs

#### Fetch Decision Timeline
- Purpose: drill into a decision lifecycle
- Method: `GET`
- Path: `/api/hdc/analytics/decision-timeline/{decision_id}`
- Outputs:
  - `decision_timeline`
- Permissions:
  - Recruiter
  - Hiring Manager
  - HR / HRBP
  - Governance Reviewer

#### Fetch Approval Bottleneck Details
- Purpose: drill into approval delays
- Method: `GET`
- Path: `/api/hdc/analytics/approval-bottlenecks`
- Outputs:
  - `approval_bottleneck_details`
- Permissions:
  - HR / HRBP
  - Governance Reviewer
  - Leadership Viewer

#### Fetch Negotiation Exception Trail
- Purpose: inspect negotiation-related exceptions
- Method: `GET`
- Path: `/api/hdc/analytics/negotiation-exceptions`
- Outputs:
  - `negotiation_exception_trail`
- Permissions:
  - Compensation Analyst
  - Governance Reviewer
  - Leadership Viewer

#### Fetch Joining Outcome Audit
- Purpose: inspect joining closure and outcome details
- Method: `GET`
- Path: `/api/hdc/analytics/joining-audit`
- Outputs:
  - `joining_outcome_audit`
- Permissions:
  - HR / HRBP
  - Leadership Viewer
  - Governance Reviewer

#### Fetch Recruiter / Agency Deep Performance Record
- Purpose: inspect detailed performance record
- Method: `GET`
- Path: `/api/hdc/analytics/performance-record`
- Inputs:
  - `recruiter_user_id`
  - `agency_tenant_id`
- Outputs:
  - `deep_performance_record`
- Permissions:
  - HR / HRBP
  - Leadership Viewer
  - Tenant Admin

#### Fetch Violation History
- Purpose: inspect governance violation history
- Method: `GET`
- Path: `/api/hdc/governance/violations/history`
- Outputs:
  - `violation_history`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

## 4. UI Architecture

Frontend principles:
- executive summary cards
- trend charts
- bottleneck heatmaps
- recruiter and agency comparison tables
- governance status badges
- audit drill-down panels
- clean enterprise analytics layout
- filter by tenant, role, job, time, recruiter, agency
- no candidate access

### Executive / Leadership UI
- Hiring decision intelligence dashboard
- Offer acceptance and joining summary
- Recruiter performance overview
- Agency performance overview
- Risk / exception visibility
- Governance compliance summary

### Recruiter / HR UI
- Decision analytics dashboard
- Approval bottleneck tracker
- Offer and negotiation analytics
- Joining tracker summary
- Candidate outcome insights
- Recruiter performance screen

### Agency UI
- Submission-to-offer dashboard
- Offer acceptance summary
- Joining ratio dashboard
- Agency quality and drop-off analytics

### Governance / Admin UI
- Governance dashboard
- Policy management screen
- Exception approval queue
- Violation monitor
- Audit log viewer
- Override tracking screen

## 5. Execution Flow

1. HDC modules emit events and metrics
2. Analytics engine captures decision, approval, offer, negotiation, and joining signals
3. Governance engine evaluates actions against active policy
4. Metrics are aggregated into dashboards and trend reports
5. Violations and exceptions are recorded
6. Recruiters, leaders, and admins review analytics and governance state
7. Governance actions warn, block, escalate, or require exception approval
8. Outcomes feed recruiter performance, agency performance, and hiring intelligence
9. Audit trail remains preserved for every major decision and override

## 6. Edge Cases

- analytics mismatch due to delayed events
- approval completed but analytics snapshot not refreshed
- negotiation exception approved after offer already released
- joining recorded after job closure
- recruiter reassignment causing metric ownership confusion
- agency credited incorrectly after company-side correction
- duplicate override entries
- governance policy changed mid-process
- historical analytics on superseded decisions
- tenant-specific governance rules conflicting with default policy
- audit continuity across reopen / rework / reapproval cycles

## 7. Enterprise Features

- tenant-scoped HDC analytics and governance
- real-time and aggregated metrics
- daily, weekly, and monthly rollups
- recruiter and agency performance intelligence
- governance policy enforcement and locking
- exception monitoring and review workflows
- rule violation detection
- drill-down audit and timeline visibility
- company and agency analytics isolation
- auditable decision intelligence lifecycle

## 8. Integration Mapping

### Decision Engine
- Consumes:
  - decision events
  - decision statuses
- Produces:
  - decision metrics
  - decision timeline views
- Events:
  - `hdc.analytics.decision.updated`
- Downstream:
  - dashboards
  - recruiter performance

### Hiring Committee Engine
- Consumes:
  - committee recommendations
  - dissent and escalation signals
- Produces:
  - committee effectiveness analytics
  - governance review context
- Events:
  - `hdc.analytics.committee.updated`
- Downstream:
  - leadership dashboards

### Candidate Comparison Engine
- Consumes:
  - comparison rankings
  - tie and risk states
- Produces:
  - comparison effectiveness metrics
- Events:
  - `hdc.analytics.comparison.updated`
- Downstream:
  - decision quality analytics

### Decision Approval Engine
- Consumes:
  - approval states
  - escalation states
  - override states
- Produces:
  - approval analytics
  - bottleneck detection
  - violation candidates
- Events:
  - `hdc.analytics.approval.updated`
- Downstream:
  - governance and leadership views

### Offer Intelligence Engine
- Consumes:
  - recommendation scenarios
  - exception flags
- Produces:
  - offer intelligence metrics
- Events:
  - `hdc.analytics.offer.intelligence.updated`
- Downstream:
  - offer analytics

### Compensation Engine
- Consumes:
  - package validations
  - exceptions
  - approval dependencies
- Produces:
  - compensation deviation trends
  - policy compliance analytics
- Events:
  - `hdc.analytics.compensation.updated`
- Downstream:
  - governance dashboards

### Negotiation Engine
- Consumes:
  - negotiation rounds
  - concessions
  - outcomes
- Produces:
  - negotiation success and exception analytics
- Events:
  - `hdc.analytics.negotiation.updated`
- Downstream:
  - recruiter and leadership dashboards

### Final Offer Release Engine
- Consumes:
  - release readiness
  - dispatch and recall states
- Produces:
  - offer release analytics
  - release governance signals
- Events:
  - `hdc.analytics.release.updated`
- Downstream:
  - compliance summary

### Offer Acceptance Engine
- Consumes:
  - offer response states
  - queries
  - expiry and reopen states
- Produces:
  - acceptance rate analytics
  - response timing analytics
- Events:
  - `hdc.analytics.acceptance.updated`
- Downstream:
  - offer and recruiter performance analytics

### Joining Tracking Engine
- Consumes:
  - joined, not joined, postponed, withdrawn outcomes
- Produces:
  - joining metrics
  - recruiter and agency performance updates
- Events:
  - `hdc.analytics.joining.updated`
- Downstream:
  - leadership and performance dashboards

### Governance Layer
- Consumes:
  - policy definitions
  - review decisions
- Produces:
  - active governance control state
- Events:
  - `hdc.governance.policy.updated`
- Downstream:
  - all governed HDC modules

### Analytics Layer
- Consumes:
  - all HDC metric events
- Produces:
  - snapshots
  - trends
  - rollups
- Events:
  - `hdc.analytics.snapshot.updated`
- Downstream:
  - dashboards
  - intelligence

### Audit Layer
- Consumes:
  - overrides
  - policy changes
  - violation and exception events
- Produces:
  - immutable audit records
- Events:
  - `hdc.governance.audit.logged`
- Downstream:
  - governance review

### Notification / Communication Layer
- Consumes:
  - violation states
  - exception approvals
  - threshold alerts
- Produces:
  - internal notifications
  - governance escalation alerts
- Events:
  - `hdc.governance.notification.required`
- Downstream:
  - admins, recruiters, reviewers

### Recruiter Performance Systems
- Consumes:
  - recruiter-linked outcomes
- Produces:
  - recruiter performance records
- Events:
  - `hdc.analytics.recruiter.performance.updated`
- Downstream:
  - leadership and HR dashboards

### Agency Performance Systems
- Consumes:
  - agency-linked outcomes
- Produces:
  - agency quality and joining performance records
- Events:
  - `hdc.analytics.agency.performance.updated`
- Downstream:
  - agency review dashboards
